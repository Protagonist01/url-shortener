# URL Shortener with Analytics

A URL shortener being hardened for production, built with FastAPI, PostgreSQL, Redis, and Celery. Shorten URLs, cache redirects in Redis, track clicks via background work, and view analytics with geographic breakdown. The foundation audit records unresolved release gates in docs/audits/2026-10-03-foundation.md.

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
# 1. Prepare local configuration, preserving an existing local file
# PowerShell: if (-not (Test-Path .env)) { Copy-Item .env.example .env }
cp -n .env.example .env
# Replace SECRET_KEY and POSTGRES_PASSWORD with unique generated local values.
# Update the password in DATABASE_URL to match POSTGRES_PASSWORD.
# Do not overwrite an existing .env; keep it local and untracked.

# 2. Start the development stack
docker compose up -d

# 3. Run database migrations
docker compose exec api alembic upgrade head

# 4. Verify
curl http://localhost:8000/health
# → {"status":"ok","env":"development"}

# 5. Open Swagger UI
# http://localhost:8000/docs
```

`.env.example` is a public development template; its placeholders must be replaced before running services. Generate URL-safe random local values with `python -c "import secrets; print(secrets.token_urlsafe(48))"`, then edit the local file. Production secrets belong in the selected deployment provider's secret store. `.env` and variants are excluded from Git and Docker build contexts. Untracking them does not remove old Git history or rotate previously exposed credentials; exposure/rotation remains tracked in INPUT_REQUIRED.md (IN10).

Verify configuration boundaries without reading real local environment values:

```bash
python -m scripts.verify_configuration
python -m scripts.verify_configuration --docker
```

The Docker check builds only a temporary synthetic context with the repository's ignore rules; it never submits this checkout's environment files to Docker. See docs/verification/2026-10-06-configuration-boundaries.md for evidence and limitations.

## Foundation checks

The `Foundation correctness` workflow runs isolated configuration, worker-registration, migration and actual task-delivery checks. Reproduce with `requirements-ci.txt` and the commands in [foundation-ci.md](docs/verification/foundation-ci.md). This scoped job does not establish full application/security/browser/performance readiness; F03 and the milestone gates track remaining coverage.

Dependency advisories are collected separately with pinned `requirements-audit.txt` tooling. See [reproduction and scope](docs/verification/dependency-advisories.md) and [known finding mappings](docs/security/dependency-triage.md). The evidence workflow does not approve vulnerable packages for release; F03 tracks repairs and enforcement.

HS256 token dependency repair and historical-token/real-service checks are documented in [JWT verification](docs/verification/jwt-dependency-remediation.md). `requirements-legacy-jwt.txt` is an intentionally historical compatibility fixture for a separate test environment; never include it in an application deployment.

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

Use a separate Python3.12 virtual environment. The API image intentionally
installs only requirements.txt; tests and optional monitoring have separate manifests.

```bash
python -m pip install -r requirements-ci.txt
python -m pip check
python -m pytest tests/test_worker_registration.py -c pytest.ini -q
```

Run the HTTP suite only through the labeled disposable-service harness in
[foundation-ci.md](docs/verification/foundation-ci.md) and
[JWT verification](docs/verification/jwt-dependency-remediation.md).
Its cache cleanup must never target shared Redis. The suite covers health,
metrics, shortening, redirects, analytics, authentication and rate limits.
See [test dependency repair](docs/verification/test-dependency-remediation.md)
for install scopes, the before/after UNIX check and rollback.

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
