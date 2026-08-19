"""Scheduled Celery beat tasks.

Celery beat is a scheduler that runs tasks on a recurring schedule (like cron).
It uses a separate process (`celery -A app.worker.celery_app beat`) that
enqueues tasks at the configured intervals.

We define one scheduled task:
  - aggregate_daily_stats: runs every hour, rolls up today's raw click_events
    into the daily_stats table. Running hourly (not daily at midnight) means
    the dashboard shows fresh data within an hour instead of waiting until
    the next day. The task is idempotent: re-running for the same day
    replaces the existing aggregate row.
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import create_engine, func, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.models import ClickEvent, DailyStats, ShortURL
from app.worker.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="aggregate_daily_stats")
def aggregate_daily_stats() -> dict:
    """Roll up raw click_events into daily_stats for today (UTC).

    For each (url_id, day) combination:
      - Count total clicks
      - Count unique IP addresses
      - Find the top country by click count

    Uses PostgreSQL's INSERT ... ON CONFLICT (upsert) so the task is
    idempotent — if it runs twice for the same day, the second run replaces
    the first's row. This is why running hourly is safe, not just daily.
    """
    sync_url = settings.sync_database_url
    engine = create_engine(sync_url, pool_pre_ping=True)

    now = datetime.now(timezone.utc)
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    window_end = now
    window_start = today_start - timedelta(days=7)  # roll up last 7 days

    try:
        with Session(engine) as session:
            # Aggregate clicks per (url_id, day) from raw events.
            # date_trunc('day', ...) groups clicks into UTC day buckets.
            raw_aggregates = session.execute(
                select(
                    ClickEvent.url_id,
                    func.date_trunc("day", ClickEvent.clicked_at).label("day"),
                    func.count(ClickEvent.id).label("click_count"),
                    func.count(ClickEvent.ip_address.distinct()).label("unique_ips"),
                )
                .where(ClickEvent.clicked_at >= window_start)
                .group_by(
                    ClickEvent.url_id,
                    func.date_trunc("day", ClickEvent.clicked_at),
                )
            ).all()

            rows_upserted = 0
            for row in raw_aggregates:
                # Find the top country for this url on this day.
                top_country_row = session.execute(
                    select(ClickEvent.country, func.count(ClickEvent.id))
                    .where(
                        ClickEvent.url_id == row.url_id,
                        func.date_trunc("day", ClickEvent.clicked_at) == row.day,
                        ClickEvent.country.is_not(None),
                    )
                    .group_by(ClickEvent.country)
                    .order_by(func.count(ClickEvent.id).desc())
                    .limit(1)
                ).first()
                top_country = top_country_row[0] if top_country_row else None

                stmt = pg_insert(DailyStats).values(
                    url_id=row.url_id,
                    date=row.day,
                    click_count=row.click_count,
                    unique_ips=row.unique_ips,
                    top_country=top_country,
                )
                stmt = stmt.on_conflict_do_update(
                    constraint="uq_daily_stats_url_date",
                    set_=dict(
                        click_count=stmt.excluded.click_count,
                        unique_ips=stmt.excluded.unique_ips,
                        top_country=stmt.excluded.top_country,
                    ),
                )
                session.execute(stmt)
                rows_upserted += 1

            session.commit()
            logger.info(
                "daily_stats aggregated: %d (url, day) rows upserted", rows_upserted
            )
            return {"rows_upserted": rows_upserted, "window": f"{window_start} to {window_end}"}
    except Exception:
        logger.exception("daily_stats aggregation failed")
        raise
    finally:
        engine.dispose()
