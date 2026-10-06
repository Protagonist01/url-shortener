"""Celery worker for async click tracking.

The redirect endpoint does NOT block on click persistence — it enqueues a
`record_click` task and returns the 302 immediately. This keeps redirect
latency dominated by the cache lookup, not by a DB write.
"""
from __future__ import annotations

import logging

from celery import Celery

from app.core.config import settings

logger = logging.getLogger(__name__)

celery_app = Celery(
    "url_shortener",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    # Workers must load the module defining the task named by beat_schedule.
    # Keeping this in Celery's loader avoids a circular eager import.
    include=["app.worker.beat_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    task_default_queue="clicks",
    beat_schedule={
        "aggregate-daily-stats": {
            "task": "aggregate_daily_stats",
            "schedule": 3600,  # every hour (3600 seconds)
        },
    },
)


@celery_app.task(name="record_click", bind=True, max_retries=3)
def record_click(
    self,
    url_id: int,
    short_code: str,
    ip_address: str | None,
    user_agent: str | None,
    referer: str | None,
) -> None:
    """Persist a single click event. Uses a SYNC SQLAlchemy engine because
    Celery workers are synchronous; we cannot share the async engine from the
    API process. The DB URL is converted from asyncpg -> psycopg2 driver.
    """
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from app.models.models import ClickEvent
    from app.services.geoip_service import lookup_country

    sync_url = settings.sync_database_url
    engine = create_engine(sync_url, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            click = ClickEvent(
                url_id=url_id,
                ip_address=ip_address,
                user_agent=user_agent,
                referer=referer,
                country=lookup_country(ip_address),
            )
            session.add(click)
            session.commit()
    except Exception as exc:
        logger.exception("failed to record click for url_id=%s", url_id)
        raise self.retry(exc=exc, countdown=2**self.request.retries * 5)
    finally:
        engine.dispose()
