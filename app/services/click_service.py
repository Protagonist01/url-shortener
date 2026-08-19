"""Click tracking service.

Two backends, selected by the CLICK_TRACKING_BACKEND setting:

  "celery" (default) — enqueues a Celery task. Robust: survives API
    crashes, retries on failure. Requires a Celery worker process
    (paid service on Render, free in local Docker).

  "background_tasks" — uses FastAPI's BackgroundTasks to run the
    click write in the API process after the response is sent. Free:
    no extra process needed. Less robust: lost on crash/restart,
    doesn't persist across API restarts. Good enough for a portfolio.

The redirect endpoint calls `track_click()` which dispatches to the
right backend based on the config.
"""
from __future__ import annotations

import logging

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import SessionLocal
from app.models.models import ClickEvent
from app.services.geoip_service import lookup_country_async

logger = logging.getLogger(__name__)


async def _record_click_async(
    url_id: int,
    ip_address: str | None,
    user_agent: str | None,
    referer: str | None,
) -> None:
    """Write a click event using the async DB session.

    This runs as a FastAPI BackgroundTask — after the 302 response is
    already sent to the client. Creates its own session (the request's
    session is closed by now). Does the GeoIP lookup via httpx async.
    """
    country = await lookup_country_async(ip_address)
    try:
        async with SessionLocal() as session:
            click = ClickEvent(
                url_id=url_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                country=country,
            )
            session.add(click)
            await session.commit()
    except Exception:
        logger.exception("failed to record click for url_id=%s", url_id)


def track_click(
    background_tasks: BackgroundTasks,
    url_id: int,
    short_code: str,
    ip_address: str | None,
    user_agent: str | None,
    referer: str | None,
) -> None:
    """Dispatch click tracking to the configured backend."""
    if settings.CLICK_TRACKING_BACKEND == "background_tasks":
        background_tasks.add_task(
            _record_click_async,
            url_id=url_id,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
        )
    else:
        # Celery path — import here to avoid loading Celery when
        # running in background_tasks mode (the Celery broker might
        # not even be configured).
        from app.worker.celery_app import record_click

        record_click.delay(
            url_id=url_id,
            short_code=short_code,
            ip_address=ip_address,
            user_agent=user_agent,
            referer=referer,
        )
