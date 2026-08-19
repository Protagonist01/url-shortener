import json
import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.metrics import cache_hits_total, cache_misses_total, urls_created_total
from app.core.redis import redis_client
from app.models.models import ShortURL
from app.schemas.url import URLCreate
from app.utils.shortener import encode

logger = logging.getLogger(__name__)

CACHE_PREFIX = "url:"


def _cache_key(short_code: str) -> str:
    return f"{CACHE_PREFIX}{short_code}"


async def _cache_url(url: ShortURL) -> None:
    payload = {
        "id": url.id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "is_active": url.is_active,
    }
    await redis_client.set(
        _cache_key(url.short_code),
        json.dumps(payload),
        ex=settings.CACHE_TTL_SECONDS,
    )


async def _cache_get(short_code: str) -> dict | None:
    raw = await redis_client.get(_cache_key(short_code))
    if raw is None:
        return None
    return json.loads(raw)


async def _cache_invalidate(short_code: str) -> None:
    await redis_client.delete(_cache_key(short_code))


async def create_short_url(
    db: AsyncSession, payload: URLCreate, owner_id: int | None
) -> ShortURL:
    """Create a new short URL. The short code is derived from the DB row ID via
    base62-encoding, so we have to INSERT first (getting the autoincrement ID),
    then UPDATE the row to set the short_code derived from it.

    For custom codes we skip the auto-generation and store the requested code
    directly, rejecting collisions up front.
    """
    if payload.custom_code:
        existing = await db.execute(
            select(ShortURL).where(ShortURL.short_code == payload.custom_code)
        )
        if existing.scalar_one_or_none():
            raise ValueError("custom_code already in use")
        url = ShortURL(
            short_code=payload.custom_code,
            original_url=str(payload.original_url),
            owner_id=owner_id,
            is_active=True,
        )
        db.add(url)
        await db.commit()
        await db.refresh(url)
        return url

    # Insert with a placeholder code; we will patch the real code in once we
    # know the row's autoincrement ID. This avoids a separate sequence/lock.
    url = ShortURL(
        short_code="PENDING",
        original_url=str(payload.original_url),
        owner_id=owner_id,
        is_active=True,
    )
    db.add(url)
    await db.commit()
    await db.refresh(url)

    url.short_code = encode(url.id)
    await db.commit()
    await db.refresh(url)

    await _cache_url(url)
    urls_created_total.inc()
    return url


async def resolve_short_url(db: AsyncSession, short_code: str) -> dict | None:
    """Resolve a short code to its target. Cache-first; falls back to DB and
    warms the cache on miss."""
    cached = await _cache_get(short_code)
    if cached is not None:
        if not cached.get("is_active", True):
            return None
        cache_hits_total.inc()
        return cached

    cache_misses_total.inc()
    result = await db.execute(
        select(ShortURL).where(ShortURL.short_code == short_code)
    )
    url = result.scalar_one_or_none()
    if url is None or not url.is_active:
        return None

    payload = {
        "id": url.id,
        "short_code": url.short_code,
        "original_url": url.original_url,
        "is_active": url.is_active,
    }
    await _cache_url(url)
    return payload


async def get_url_by_id(db: AsyncSession, url_id: int) -> ShortURL | None:
    result = await db.execute(select(ShortURL).where(ShortURL.id == url_id))
    return result.scalar_one_or_none()


async def delete_short_url(db: AsyncSession, url_id: int) -> bool:
    result = await db.execute(select(ShortURL).where(ShortURL.id == url_id))
    url = result.scalar_one_or_none()
    if url is None:
        return False
    await _cache_invalidate(url.short_code)
    await db.delete(url)
    await db.commit()
    return True


async def list_urls_for_user(
    db: AsyncSession, owner_id: int, limit: int = 50, offset: int = 0
) -> list[ShortURL]:
    result = await db.execute(
        select(ShortURL)
        .where(ShortURL.owner_id == owner_id)
        .order_by(ShortURL.created_at.desc())
        .limit(limit)
        .offset(offset)
    )
    return list(result.scalars().all())
