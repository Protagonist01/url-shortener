# URL Shortener with Analytics

A production-grade URL shortener built with FastAPI, PostgreSQL, Redis, and Celery. Shorten URLs, cache redirects in Redis, track clicks asynchronously via a Celery worker, and view analytics with geographic breakdown.

## Architecture

```
                    ┌─────────────────────────────────────────────┐
                    │                   Client                     │
                    └──────────────────┬──────────────────────────┘
                                       │
                            ┌──────────▼──────────┐
                            │   FastAPI (uvicorn) │  :8000
                            │   - /api/urls       │
                            │   - /api/auth       │
                            │   - /api/analytics  │
                            │   - /{short_code}   │
                            │   - /metrics        │
                            └───┬──────┬──────┬──┘
                                │      │      │
                    ┌───────────▼┐  ┌───▼──┐ ┌▼────────────┐
                    │ PostgreSQL │  │ Redis │ │   Celery    │
                    │  (asyncpg) │  │ cache │ │  .delay()   │
                    └──────┬─────┘  └───┬──┘ └──────┬──────┘
                           │            │           │
                           │      ┌─────▼──────┐    │ enqueue
                           │      │ rate_limit  │    │
                           │      │ ZSET keys   │    │
                           │      └────────────┘    │
                           │                        │
                    ┌──────▼──────────────────────▼─┐
                    │       Celery Worker (:5555)    │
                    │  - record_click (sync engine)  │
                    │  - aggregate_daily_stats       │
                    │  - GeoIP lookup (ip-api.com)   │
                    └──────────────┬─────────────────┘
                                   │
                    ┌──────────────▼──────────┐
                    │   Celery Beat (scheduler) │
                    │   - hourly rollup         │
                    └─────────────────────────┘
```

### Request flow: redirect (the hot path)

```
Client → GET /{short_code}
  → Redis cache hit? → 302 redirect (no DB call)
  → Cache miss? → SELECT from PostgreSQL → warm cache → 302
  → Celery .delay(record_click) → 302 returns immediately
  → Worker: INSERT click_event + GeoIP lookup (async, off-request)
```

### Services

| Service    | Port | Purpose                                      |
|------------|------|----------------------------------------------|
| `api`      | 8000 | FastAPI app (Swagger at `/docs`)             |
| `db`       | 5432 | PostgreSQL 16 (persistence)                 |
| `redis`    | 6379 | Redis 7 (cache, rate limiter, Celery broker) |
| `worker`   | —    | Celery worker (click tracking, aggregation)  |
| `beat`     | —    | Celery beat (hourly stats aggregation)        |
| `flower`   | 5555 | Celery monitoring UI                          |

## Quick start

```bash
# 1. Start the full stack
docker compose up -d

# 2. Run database migrations
docker compose exec api alembic upgrade head

# 3. Verify
curl http://localhost:8000/health
# → {"status":"ok","env":"development"}

# 4. Open Swagger UI
# http://localhost:8000/docs
```

## API reference

### Shorten a URL
```bash
POST /api/urls
Content-Type: application/json

{"original_url": "https://example.com/very/long/path"}
# Optional: {"custom_code": "mycode"}
```
Response: `201 Created`
```json
{
  "id": 1,
  "short_code": "1eSEBk",
  "original_url": "https://example.com/very/long/path",
  "short_url": "http://localhost:8000/1eSEBk",
  "is_active": true,
  "created_at": "2026-08-16T..."
}
```

### Redirect
```bash
GET /{short_code}
# → 302 redirect to original URL
# Click is tracked asynchronously via Celery
```

### Analytics
```bash
GET /api/analytics/{short_code}
```
Response:
```json
{
  "short_code": "1eSEBk",
  "total_clicks": 42,
  "last_24h": 5,
  "last_7d": 30,
  "top_countries": [["US", 15], ["GB", 8], ["DE", 5]],
  "timeseries": [
    {"bucket": "2026-08-10T00:00:00Z", "clicks": 3},
    {"bucket": "2026-08-11T00:00:00Z", "clicks": 7}
  ]
}
```

### Auth (optional)
```bash
POST /api/auth/register  {"email": "...", "password": "..."}
POST /api/auth/login     {"email": "...", "password": "..."}  → {"access_token": "..."}
```
Authenticated users can list and delete their own URLs. Anonymous shortening is also supported.

### Metrics
```bash
GET /metrics  # Prometheus format
```

## Running tests

```bash
docker compose exec api pytest -q
# → 17 passed
```

Tests cover: health, metrics, URL shortening, redirect, cache warming, custom codes,
code collisions, analytics, auth (register/login/duplicate/wrong-password/invalid-token),
and rate limiting (429 enforcement + scope independence).

## Tech stack

| Layer            | Technology                                    |
|------------------|-----------------------------------------------|
| Web framework    | FastAPI + uvicorn                             |
| Database         | PostgreSQL 16 + SQLAlchemy 2.0 (async)       |
| Cache            | Redis 7 (read-through cache + rate limiter)  |
| Background jobs  | Celery 5 + Redis broker                       |
| Scheduler        | Celery beat (hourly analytics rollup)          |
| Migrations       | Alembic                                       |
| Auth             | JWT (python-jose) + bcrypt                    |
| Metrics          | prometheus-fastapi-instrumentator             |
| GeoIP            | ip-api.com (free, no API key)                 |
| Monitoring       | Flower (Celery task UI)                       |

## Key design decisions

See `BUILD_BOOK.md` for the full engineering journal. Highlights:

- **Short codes** are `base62(id XOR salt)` — collision-free without uniqueness checks, non-enumerable without knowing the salt.
- **Cache-first redirects** — Redis lookup → DB fallback → warm cache. Redirects that hit the cache never touch PostgreSQL.
- **Async click tracking** — the redirect enqueues a Celery task and returns 302 immediately. Click persistence (including GeoIP lookup) happens in the worker, off the request path.
- **Rate limiting** — Redis sorted-set sliding window, scoped per endpoint type (redirect/shorten/auth have independent budgets).
- **Pre-aggregated analytics** — a Celery beat job rolls up raw clicks into `daily_stats` hourly, so the analytics endpoint reads pre-aggregated data instead of scanning millions of rows.
- **Worker uses a sync engine** — the Celery worker can't share the async SQLAlchemy engine (Celery is synchronous), so it creates a sync `psycopg2` engine per task.
