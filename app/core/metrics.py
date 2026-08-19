"""Custom Prometheus metrics for the URL shortener.

The `prometheus-fastapi-instrumentator` (set up in main.py) automatically
tracks HTTP request count, latency, and status by route. Here we define
additional *business* metrics that the instrumentator can't infer:
  - cache_hits_total / cache_misses_total: for the Redis redirect cache
  - clicks_enqueued_total: clicks handed off to Celery
  - urls_created_total: new short URLs
  - rate_limit_rejections_total: 429s served

These are scraped by Prometheus from the /metrics endpoint.
"""
from __future__ import annotations

from prometheus_client import Counter

cache_hits_total = Counter(
    "url_shortener_cache_hits_total",
    "Total Redis cache hits on the redirect path.",
)

cache_misses_total = Counter(
    "url_shortener_cache_misses_total",
    "Total Redis cache misses on the redirect path (fell back to DB).",
)

clicks_enqueued_total = Counter(
    "url_shortener_clicks_enqueued_total",
    "Total click events handed off to the Celery worker.",
)

urls_created_total = Counter(
    "url_shortener_urls_created_total",
    "Total short URLs created.",
)

rate_limit_rejections_total = Counter(
    "url_shortener_rate_limit_rejections_total",
    "Total requests rejected by the rate limiter (429).",
    labelnames=("scope",),
)
