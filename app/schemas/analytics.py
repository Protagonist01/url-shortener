from datetime import datetime

from pydantic import BaseModel


class ClickStats(BaseModel):
    short_code: str
    total_clicks: int


class TimeSeriesPoint(BaseModel):
    bucket: datetime
    clicks: int


class URLAnalytics(BaseModel):
    short_code: str
    total_clicks: int
    last_24h: int
    last_7d: int
    top_countries: list[tuple[str, int]]
    timeseries: list[TimeSeriesPoint]
