"""Analytics service.

Two data sources:
  - click_events: raw, append-only, one row per click. Used for real-time
    counts (total, last 24h, last 7d, top countries).
  - daily_stats: pre-aggregated by the Celery beat job (aggregate_daily_stats).
    Used for the timeseries chart. This avoids re-scanning the full
    click_events table on every analytics request.

The split is deliberate: real-time numbers are small queries (COUNT with a
WHERE clause on an indexed timestamp column), so they can hit raw events.
The timeseries is a GROUP BY over potentially millions of rows — that's
what the pre-aggregated table is for.
"""
from datetime import datetime, timedelta, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import ClickEvent, DailyStats, ShortURL
from app.schemas.analytics import TimeSeriesPoint, URLAnalytics


async def get_url_analytics(
    db: AsyncSession, short_code: str, days: int = 7
) -> URLAnalytics | None:
    url_result = await db.execute(
        select(ShortURL).where(ShortURL.short_code == short_code)
    )
    url = url_result.scalar_one_or_none()
    if url is None:
        return None

    now = datetime.now(timezone.utc)
    last_24h_cutoff = now - timedelta(hours=24)
    last_7d_cutoff = now - timedelta(days=7)
    series_cutoff = now - timedelta(days=days)

    # --- Real-time stats from raw click_events ---
    total_q = await db.execute(
        select(func.count(ClickEvent.id)).where(ClickEvent.url_id == url.id)
    )
    total_clicks = total_q.scalar_one()

    last_24h_q = await db.execute(
        select(func.count(ClickEvent.id)).where(
            ClickEvent.url_id == url.id,
            ClickEvent.clicked_at >= last_24h_cutoff,
        )
    )
    last_24h = last_24h_q.scalar_one()

    last_7d_q = await db.execute(
        select(func.count(ClickEvent.id)).where(
            ClickEvent.url_id == url.id,
            ClickEvent.clicked_at >= last_7d_cutoff,
        )
    )
    last_7d = last_7d_q.scalar_one()

    countries_q = await db.execute(
        select(ClickEvent.country, func.count(ClickEvent.id))
        .where(ClickEvent.url_id == url.id, ClickEvent.country.is_not(None))
        .group_by(ClickEvent.country)
        .order_by(func.count(ClickEvent.id).desc())
        .limit(5)
    )
    top_countries = [(c, n) for c, n in countries_q.all()]

    # --- Timeseries from pre-aggregated daily_stats ---
    # Falls back to raw click_events if no daily_stats rows exist yet
    # (e.g. the beat job hasn't run for this URL).
    series_q = await db.execute(
        select(DailyStats.date.label("bucket"), DailyStats.click_count.label("clicks"))
        .where(DailyStats.url_id == url.id, DailyStats.date >= series_cutoff)
        .order_by(DailyStats.date)
    )
    timeseries = [
        TimeSeriesPoint(bucket=row.bucket, clicks=row.clicks)
        for row in series_q.all()
    ]

    if not timeseries:
        # Fallback: compute from raw events if beat hasn't run yet.
        raw_series_q = await db.execute(
            select(
                func.date_trunc("day", ClickEvent.clicked_at).label("bucket"),
                func.count(ClickEvent.id).label("clicks"),
            )
            .where(ClickEvent.url_id == url.id, ClickEvent.clicked_at >= series_cutoff)
            .group_by("bucket")
            .order_by("bucket")
        )
        timeseries = [
            TimeSeriesPoint(bucket=row.bucket, clicks=row.clicks)
            for row in raw_series_q.all()
        ]

    return URLAnalytics(
        short_code=short_code,
        total_clicks=total_clicks,
        last_24h=last_24h,
        last_7d=last_7d,
        top_countries=top_countries,
        timeseries=timeseries,
    )
