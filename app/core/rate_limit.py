"""Redis-based sliding-window rate limiter.

Implements a sliding window using a Redis sorted set (ZSET):
  - Each request adds a member scored by its timestamp (microsecond precision).
  - We first remove all entries older than the window, then count remaining.
  - If count >= limit, reject. Otherwise add the new entry and set TTL.

This is the "sorted set" approach from Redis's official rate limiting patterns.
It's more accurate than fixed-window (no burst-at-boundary problem) and simpler
than token-bucket (no refill math). The cost is one ZREMRANGEBYSCORE + one
ZCARD + one ZADD per request — 3 Redis round-trips. For a demo that's fine; in
production you'd pipeline them or use the INCR-based fixed-window approach
(1 round-trip, but less precise).

Used as a FastAPI dependency: `Depends(rate_limit(limit=10, window=60))`.
On limit exceeded, raises 429 Too Many Requests with a Retry-After header.
"""
from __future__ import annotations

import time
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from app.core.metrics import rate_limit_rejections_total
from app.core.redis import redis_client


def _client_ip(request: Request) -> str:
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


def rate_limit(limit: int = 10, window: int = 60, scope: str = "global"):
    """Return a FastAPI dependency that enforces `limit` requests per `window`
    seconds per client IP, keyed under `rate_limit:{scope}:{ip}`.

    `scope` lets you have separate buckets for different endpoints — e.g.
    `scope="redirect"` and `scope="shorten"` can have different limits without
    one consuming the other's budget.
    """

    async def _check(request: Request) -> None:
        ip = _client_ip(request)
        key = f"rate_limit:{scope}:{ip}"
        now = time.time()
        window_start = now - window

        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)  # drop expired entries
        pipe.zcard(key)                               # count current window
        pipe.zadd(key, {f"{now}:{id(request)}": now})  # add this request
        pipe.expire(key, window)                      # auto-cleanup key
        results = await pipe.execute()

        count = results[1]  # ZCARD result (before adding this request)
        if count >= limit:
            rate_limit_rejections_total.labels(scope=scope).inc()
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"rate limit exceeded: {limit} requests per {window}s",
                headers={"Retry-After": str(window)},
            )

    return _check


RateLimitRedirect = Annotated[None, Depends(rate_limit(limit=100, window=60, scope="redirect"))]
RateLimitShorten = Annotated[None, Depends(rate_limit(limit=20, window=60, scope="shorten"))]
RateLimitAuth = Annotated[None, Depends(rate_limit(limit=5, window=60, scope="auth"))]
