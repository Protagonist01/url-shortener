from fastapi import APIRouter, HTTPException, status
from fastapi.responses import RedirectResponse

from app.api.deps import CurrentUserOptional, SessionDep
from app.core.config import settings
from app.core.rate_limit import RateLimitShorten
from app.schemas.url import URLCreate, URLResponse
from app.services import url_service

router = APIRouter(prefix="/api/urls", tags=["urls"])


def _to_response(url) -> URLResponse:
    return URLResponse(
        id=url.id,
        short_code=url.short_code,
        original_url=url.original_url,
        short_url=f"{settings.SHORT_URL_BASE}/{url.short_code}",
        is_active=url.is_active,
        created_at=url.created_at,
    )


@router.post("", response_model=URLResponse, status_code=201)
async def create_url(
    payload: URLCreate,
    db: SessionDep,
    user: CurrentUserOptional,
    _: RateLimitShorten,
) -> URLResponse:
    try:
        url = await url_service.create_short_url(
            db, payload, owner_id=user.id if user else None
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail=str(exc)
        ) from exc
    return _to_response(url)


@router.get("", response_model=list[URLResponse])
async def list_my_urls(
    db: SessionDep, user: CurrentUserOptional, limit: int = 50, offset: int = 0
) -> list[URLResponse]:
    if user is None:
        return []
    urls = await url_service.list_urls_for_user(db, user.id, limit, offset)
    return [_to_response(u) for u in urls]


@router.delete("/{url_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_url(url_id: int, db: SessionDep, user: CurrentUserOptional) -> None:
    url = await url_service.get_url_by_id(db, url_id)
    if url is None:
        raise HTTPException(status_code=404, detail="url not found")
    if url.owner_id is not None and (user is None or url.owner_id != user.id):
        raise HTTPException(status_code=403, detail="not allowed to delete this url")
    deleted = await url_service.delete_short_url(db, url_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="url not found")
