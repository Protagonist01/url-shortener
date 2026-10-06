# Build Book — URL Shortener with Analytics
A journal of the real reasoning behind this build: decisions, options rejected, and things that broke along the way.

## Index
- [Entry 1 — Stack, layout, and the redirect router that ate the world](#entry-1--stack-layout-and-the-redirect-router-that-ate-the-world)
- [Entry 2 — Don't trust unmaintained libraries: passlib vs modern bcrypt](#entry-2--dont-trust-unmaintained-libraries-passlib-vs-modern-bcrypt)
- [Entry 3 — The short code generator: base62 over an XOR'd autoincrement ID](#entry-3--the-short-code-generator-base62-over-an-xord-autoincrement-id)
- [Entry 4 — Caching the redirect, and why the worker uses a sync engine](#entry-4--caching-the-redirect-and-why-the-worker-uses-a-sync-engine)
- [Entry 5 — GeoIP enrichment: populating the country field in the worker](#entry-5--geoip-enrichment-populating-the-country-field-in-the-worker)
- [Entry 6 — Rate limiting: Redis sliding window as a FastAPI dependency](#entry-6--rate-limiting-redis-sliding-window-as-a-fastapi-dependency)
- [Entry 7 — Observability: Prometheus metrics and structured logging](#entry-7--observability-prometheus-metrics-and-structured-logging)
- [Entry 8 — Pre-aggregated analytics: Celery beat + daily_stats rollup](#entry-8--pre-aggregated-analytics-celery-beat--daily_stats-rollup)
- [Entry 9 — Expanding the test suite: isolation, cache, rate limits, and edge cases](#entry-9--expanding-the-test-suite-isolation-cache-rate-limits-and-edge-cases)
- [Entry 10 — README and architecture diagram](#entry-10--readme-and-architecture-diagram)
- [Entry 11 — Production deployment: Render, DATABASE_URL normalization, and the Dockerfile split](#entry-11--production-deployment-render-database_url-normalization-and-the-dockerfile-split)
- [Entry 12 — Free-tier fallback: BackgroundTasks when Celery is too expensive](#entry-12--free-tier-fallback-backgroundtasks-when-celery-is-too-expensive)
- [Entry 13 — UI redesign: the "paper & ink" theme and why every interaction got a state](#entry-13--ui-redesign-the-paper--ink-theme-and-why-every-interaction-got-a-state)
- [Entry 14 — Registering the task that beat already publishes](#entry-14--registering-the-task-that-beat-already-publishes)
- [Entry 15 — Keeping local configuration out of Git and Docker](#entry-15--keeping-local-configuration-out-of-git-and-docker)
- [Entry 16 — Turning local foundation checks into isolated CI](#entry-16--turning-local-foundation-checks-into-isolated-ci)
- [Entry 17 — Auditing dependencies before choosing upgrades](#entry-17--auditing-dependencies-before-choosing-upgrades)
- [Entry 18 — Removing unused JWT crypto without breaking existing tokens](#entry-18--removing-unused-jwt-crypto-without-breaking-existing-tokens)

---

## Entry 1 — Stack, layout, and the redirect router that ate the world
**Files touched:** `docker-compose.yml`, `Dockerfile`, `requirements.txt`, `app/main.py`, `app/api/*.py`, `app/core/config.py`

### Context
Starting a URL shortener that should impress recruiters: FastAPI + PostgreSQL + Redis + Celery, with caching, async DB, and background click tracking. The first decision that shapes everything else is *what the request path actually looks like* and *how the project is laid out* — because the redirect endpoint is a catch-all on `/{short_code}` and that has consequences for routing.

### Before you read on
You're building a shortener where the canonical URL is `http://host/ABC123`. That path has to be matched by *some* route, but FastAPI also has `/docs`, `/health`, `/api/urls`, `/api/auth/*`, `/api/analytics/*`. Given that FastAPI matches routes in registration order, where do you register the `/{short_code}` redirect handler relative to the others — and what regex constraint do you put on `short_code` to make sure `/docs` doesn't get treated as a short code? Sketch the registration order and the regex before reading further.

### Options considered
- **Flat single-file main.py** — rejected because recruiters can't see architecture; everything looks like a script.
- **Domain-modular (`app/urls/`, `app/analytics/`)** — rejected as overkill for this scope; would be right at ~10+ endpoints per domain.
- **Chosen: Layered (`app/api/`, `app/services/`, `app/models/`, `app/schemas/`, `app/core/`, `app/worker/`)** — clear separation between HTTP layer, business logic, persistence, and background jobs. Recruiters instantly recognise the shape.

### Why
The layered split pays off specifically because of Celery: the click-recording logic has to be callable from both the API process (to enqueue) and the worker process (to execute). Putting that in `app/worker/celery_app.py` and the URL logic in `app/services/url_service.py` keeps the worker from dragging in HTTP-layer code. If everything were in one file, the Celery task would end up importing FastAPI's app object just to reach the DB session, which is both wrong and slow.

### How to build it
The order that actually matters is the route registration order in `app/main.py`:

```python
app.include_router(auth.router)        # /api/auth/*
app.include_router(urls.router)        # /api/urls/*
app.include_router(analytics.router)   # /api/analytics/*

@app.get("/health")                    # registered BEFORE the catch-all
async def health(): ...

app.include_router(redirect.router)   # /{short_code} — LAST
```

The redirect router's handler is:

```python
CODE_RE = re.compile(r"^[0-9A-Za-z]{1,16}$")

@router.get("/{short_code}", response_class=RedirectResponse)
async def redirect(short_code: str, request: Request, db: SessionDep, user: CurrentUserOptional):
    if not CODE_RE.match(short_code):
        raise HTTPException(status_code=404, detail="not found")
    ...
```

The regex is the second safety net: even if a future route gets registered after the catch-all by mistake, anything that isn't base62 (like `/openapi.json` — has a dot) is rejected with 404 rather than being treated as a short code. Belt and braces.

`docker-compose.yml` defines 5 services: `db` (postgres:16-alpine), `redis` (redis:7-alpine), `api` (built from `Dockerfile`, runs `uvicorn app.main:app --reload`), `worker` (same image, overrides CMD to `celery -A app.worker.celery_app worker`), and `flower` (Celery monitoring UI on port 5555).

**Key gotcha on the Dockerfile:** `pool_pre_ping=True` on the SQLAlchemy engine is non-negotiable in Docker Compose — when you `docker compose restart db`, the API's existing connections go stale and the next request hangs for ~30s before timing out. `pool_pre_ping` issues a cheap `SELECT 1` before handing out a connection and recycles dead ones.

**Verification:** `docker compose up -d`, then `curl http://localhost:8000/health` returns `{"status":"ok","env":"development"}`. If you get `{"detail":"short url not found"}` on `/health`, the redirect router is registered before `/health` — fix the order in `main.py`.

### What went wrong
**The redirect router shadowed `/health`.** Initial `main.py` had `app.include_router(redirect.router)` *before* the `@app.get("/health")` decorator. The symptom: `GET /health` returned `{"detail":"short url not found"}` with a 404. Diagnosis was quick because FastAPI's 404 message came from the redirect handler's `raise HTTPException(404, "short url not found")` — the exact string pointed at the file. The fix is purely route-order: register `/health` before including the catch-all router. No regex change needed; `health` matches `^[0-9A-Za-z]{1,16}$`, so the regex wouldn't have caught it.

**Flower crashed on startup.** `command: celery --broker=redis://redis:6379/0 --port=5555 flower` failed with `Error: No such option: --port`. The `--port` flag belongs to the `flower` subcommand, not to `celery` itself, so it has to go *after* `flower` in the argument list: `celery --broker=redis://redis:6379/1 flower --port=5555`. (Also moved broker from DB 0 to DB 1 — see Entry 4 for why the Celery broker shouldn't share DB 0 with the cache.)

---

## Entry 2 — Don't trust unmaintained libraries: passlib vs modern bcrypt
**Files touched:** `requirements.txt`, `app/core/security.py`

### Context
The `/api/auth/register` endpoint returned 500 on the very first call. Stack trace pointed at `passlib/handlers/bcrypt.py:380` inside a function called `detect_wrap_bug`, raising `ValueError: password cannot be longer than 72 bytes`. The user hadn't even supplied a long password — the failure happened during passlib's *initialisation*, not during the actual hash call.

### Before you read on
You see `ValueError: password cannot be longer than 72 bytes` from passlib's internal `detect_wrap_bug` function at import time, with a normal-length password as input. Before reading further: what is passlib doing internally that triggers this, and what does that tell you about whether passlib is safe to use with the bcrypt version you just installed?

### Options considered
- **Pin `bcrypt==4.0.1`** — older bcrypt that doesn't raise on >72-byte inputs → rejected because bcrypt 4.0.1 is itself 2+ years old and we'd be pinning to an outdated crypto lib just to paper over passlib's bug.
- **Pin `bcrypt<4.1`** — same idea, same problem.
- **Chosen: Drop passlib entirely, call `bcrypt` directly** — passlib 1.7.4 is unmaintained (last release 2020), and the API we actually need is two functions: `bcrypt.hashpw` and `bcrypt.checkpw`.

### Why
passlib's `CryptContext(schemes=["bcrypt"])` runs a one-time probe at first use called `detect_wrap_bug(IDENT_2A)`. It hashes a deliberately-long secret to check whether the underlying bcrypt implementation has the historical 2a wraparound bug. Modern bcrypt (4.1+) validates input length and refuses secrets >72 bytes with `ValueError`. So passlib's own bug-detection code triggers bcrypt's input validation and crashes — at *import* time, on every request, before any user password is even hashed. This is not a passlib bug you can configure around; the probe is unconditional. The fix is to not use passlib. The two functions we need from bcrypt are 4 lines of code:

```python
import bcrypt

def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except ValueError:
        return False
```

### How to build it
1. In `requirements.txt`, replace `passlib[bcrypt]==1.7.4` with `bcrypt==4.2.1` (a single line, no passlib at all).
2. Rewrite `app/core/security.py` to import `bcrypt` directly and expose `hash_password` / `verify_password`. Keep the rest of the file (JWT helpers via `python-jose`) unchanged — passlib was only used for the password hashing.
3. The `User.hashed_password` column is `String(255)`, plenty for bcrypt's `$2b$...` 60-char output.
4. **Important:** bcrypt silently truncates inputs >72 bytes in older versions and raises `ValueError` in newer ones. Enforce a max password length at the *schema* layer (`UserCreate.password: str = Field(max_length=72)`) rather than relying on bcrypt's behaviour, so the error message is user-friendly instead of a 500.

**Verification:** `docker compose exec api pip install bcrypt==4.2.1`, then `docker compose exec api pytest -q`. The `test_register_and_login` test exercises register → login → authenticated request. Before the fix it failed with `assert 500 == 201`. After: `4 passed in 3.50s`. You can also manually verify: `POST /api/auth/register` with `{"email":"x@y.z","password":"hunter2hunter2"}` returns 201 and a user object.

### What went wrong
First attempted fix was pinning `bcrypt==4.0.1` — the version before bcrypt started raising on long inputs. That *should* have worked but didn't: the same `detect_wrap_bug` ValueError kept appearing. Diagnosis: the uvicorn `--reload` process had cached the old `passlib.CryptContext` instance in module state, so the downgrade wasn't being picked up without a full container restart. Rather than fight the reload dance, it was cleaner to remove passlib entirely. Lesson: when a dependency's *init code* crashes on a probe, downgrading the thing it probes is a fragile fix — the probe will find some other reason to crash on the next version bump. Cut the dependency.

---

## Entry 3 — The short code generator: base62 over an XOR'd autoincrement ID
**Files touched:** `app/utils/shortener.py`, `app/services/url_service.py`

### Context
Every short URL needs a short code. The obvious options are "random string, check for collision, retry" or "hash the URL". Both have problems. We need codes that are short, deterministic, collision-free without a uniqueness check, and not enumerable (an attacker shouldn't be able to iterate `base62(1), base62(2), ...` to scrape every URL in the system).

### Before you read on
You have a `short_urls` table with an autoincrement integer `id` PK. You need to turn that ID into a short, URL-safe, non-sequential code. Before reading further: write the `encode(id)` and `decode(code)` functions. Then think about how to stop an attacker from iterating IDs to enumerate every shortened URL in your system. How do you make the mapping ID → code non-guessable without storing extra state?

### Options considered
- **Random 6-char string + uniqueness check** — `secrets.token_urlsafe(6)`, then `SELECT WHERE short_code = ?` and retry on collision → rejected because it adds a read-before-write and a race (two concurrent inserts can both pass the check). Fixable with a unique constraint + retry, but messy.
- **MD5 of the original URL, take first 6 chars** — deterministic, no collision check needed for distinct URLs → rejected because same-URL-shortens-twice gives the same code (often undesirable), and MD5 prefixes *are* enumerable.
- **Chosen: `base62(id XOR salt)`** — deterministic, collision-free (IDs are unique), no extra queries, and the XOR makes the sequence non-guessable.

### Why
The autoincrement ID is already a unique, collision-free identifier — encoding it to base62 (10 digits + 26 upper + 26 lower = 62 chars) gives short codes (`62**6 ≈ 56.8B` codes at length 6). The only problem is that `base62(1), base62(2), ...` is trivially enumerable, so an attacker can scrape every URL by iterating. XOR-ing the ID with a fixed salt before encoding breaks the sequence: `base62(1 ^ SALT)` and `base62(2 ^ SALT)` produce codes that don't share a prefix pattern and aren't sorted. The salt is compiled into the code, not stored per-row, so there's no extra state.

This is *obscurity, not security* — if someone reverse-engineers one code they can derive the salt. The real protection against enumeration is rate-limiting and auth on the redirect endpoint's analytics. The XOR just stops the trivial `for i in range(1, 1000000): scrape(base62(i))` attack.

### How to build it
```python
ALPHABET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz"
BASE = len(ALPHABET)  # 62
SALT = 0x5A3C7E91  # arbitrary fixed 30-bit value, do NOT change post-launch

def _xor_id(id_: int) -> int:
    return id_ ^ SALT

def encode(id_: int) -> str:
    if id_ <= 0:
        raise ValueError("id must be positive")
    n = _xor_id(id_)
    chars = []
    while True:
        n, rem = divmod(n, BASE)
        chars.append(ALPHABET[rem])
        if n == 0:
            break
    return "".join(reversed(chars))
```

**Critical detail in `url_service.create_short_url`:** you can't compute the short code *before* the insert, because the ID doesn't exist yet. The sequence is:

1. `INSERT INTO short_urls (short_code='PENDING', original_url=..., ...)`
2. `COMMIT` — this gives the row its autoincrement ID
3. `url.short_code = encode(url.id)` — now we know the ID
4. `COMMIT` again
5. Warm the Redis cache

There's a brief window between step 2 and step 4 where the row has `short_code='PENDING'`. If a request hits `resolve_short_url` for a code that doesn't exist yet (because it's still `PENDING`), it returns 404 — which is correct behaviour, the URL isn't ready. A cleaner approach would be a separate sequence/lock to generate codes atomically, but for a demo project the two-step insert is fine and avoids a round-trip to a sequence generator.

**Verification:** In a Python shell, `encode(1)` should give `"1eSEBk"`, `encode(2)` should give `"1eSEBl"` (NOT `"1eSBk"` followed by `"1fSEBk"` — the XOR with the salt scrambles the bit pattern). Round-trip: `decode(encode(42)) == 42`. Live: after `POST /api/urls` returns `{"short_code":"1eSEBk", ...}`, `GET /1eSEBk` 302-redirects to the original URL.

### What went wrong
Nothing on this one — the math worked on the first try. The only thing worth flagging is the temptation to "improve" it by using a longer salt or per-user salts. Don't, unless you also build a migration story: changing `SALT` after launch breaks every existing short URL, because `decode(old_code)` would XOR with the new salt and return a different (wrong) ID. Pick the salt once, never change it.

---

## Entry 4 — Caching the redirect, and why the worker uses a sync engine
**Files touched:** `app/services/url_service.py`, `app/worker/celery_app.py`, `app/api/redirect.py`, `app/core/redis.py`

### Context
The redirect endpoint is the hot path — every short-URL click hits it. Two things have to happen on each click: (1) resolve the short code to a target URL, (2) record the click for analytics. Doing both in the request handler makes redirect latency = `cache_lookup + db_insert`, when it should be just `cache_lookup`. The click write should happen off the request path.

### Before you read on
You have a Redis cache for the short-code → URL mapping and a PostgreSQL `click_events` table. The redirect handler needs to: (a) look up the target as fast as possible, (b) persist the click somewhere. Sketch the data flow: what runs in the API process, what runs in the Celery worker, and what gets passed between them? Specifically — should the worker use the same SQLAlchemy `AsyncSession` as the API, or a different engine? Why?

### Options considered
- **FastAPI `BackgroundTasks` for click writes** — runs in the API process after the response is sent → rejected because (a) a crash or restart loses in-flight clicks, (b) doesn't scale horizontally (each API pod has its own background task queue with no persistence), (c) doesn't show off Celery, which is the whole point.
- **Celery task with the async engine** — try to share `app.core.database.engine` with the worker → rejected because Celery workers are synchronous. You'd have to wrap every DB call in `asyncio.run(...)`, which is fragile inside Celery's prefork model and can deadlock.
- **Chosen: Celery task with a sync engine created inside the task** — the worker converts the async DB URL (`postgresql+asyncpg://`) to a sync one (`postgresql+psycopg2://`) and creates a throwaway `create_engine` per task invocation.

### Why
The async engine from the API process is bound to the API's event loop. Celery workers don't have that loop — they're synchronous processes that fork. Sharing the async engine would either require `asyncio.run` per task (slow, can deadlock when nested) or running Celery in a thread+event-loop hybrid (fragile). The clean answer is: the worker is a different process with different constraints, give it a sync engine.

Creating the engine *per task* is wasteful in principle (engine setup has overhead), but for a demo with low click volume it's fine. In production you'd create one module-level sync engine in `celery_app.py` and reuse it — but you have to be careful: Celery's prefork model forks workers, and SQLAlchemy engines don't survive `fork()` cleanly (they hold connection pool state). The safe pattern is to create the engine lazily inside the task, or use Celery's `worker_init` signal to build it post-fork.

### How to build it
The redirect handler is intentionally tiny — cache lookup, enqueue, return:

```python
@router.get("/{short_code}", response_class=RedirectResponse)
async def redirect(short_code, request, db, user):
    target = await url_service.resolve_short_url(db, short_code)  # cache-first
    if target is None:
        raise HTTPException(404, "short url not found")

    record_click.delay(                                   # fire-and-forget
        url_id=target["id"],
        short_code=target["short_code"],
        ip_address=_client_ip(request),
        user_agent=request.headers.get("user-agent"),
        referer=request.headers.get("referer"),
    )
    return RedirectResponse(url=target["original_url"], status_code=302)
```

`url_service.resolve_short_url` is cache-first with read-through:
1. `redis.get(f"url:{short_code}")` — if hit, return parsed JSON (no DB hit).
2. On miss: `SELECT * FROM short_urls WHERE short_code = ?`, then `redis.set(key, json, ex=3600)`.
3. Cache key format: `url:{short_code}`. TTL 1 hour. No explicit invalidation on update (for a shortener, the original URL basically never changes); on delete we `redis.delete(key)`.

**The Celery task** (`app/worker/celery_app.py`):
```python
@celery_app.task(name="record_click", bind=True, max_retries=3)
def record_click(self, url_id, short_code, ip_address, user_agent, referer):
    sync_url = settings.DATABASE_URL.replace(
        "postgresql+asyncpg://", "postgresql+psycopg2://"
    )
    engine = create_engine(sync_url, pool_pre_ping=True)
    try:
        with Session(engine) as session:
            session.add(ClickEvent(url_id=url_id, ip_address=ip_address, ...))
            session.commit()
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries * 5)
    finally:
        engine.dispose()
```

`psycopg2-binary` has to be in `requirements.txt` even though the API uses `asyncpg` — they're different drivers for the same database, and the worker needs the sync one.

**Redis DB separation:** `docker-compose.yml` and `.env` use Redis DB 0 for the cache, DB 1 for the Celery broker, DB 2 for the Celery result backend. If they share DB 0, Celery's broker keys (`celery-*`, `_kombu.*`) interleave with your cache keys (`url:*`) — not a correctness bug, but makes `redis-cli KEYS *` unreadable when debugging, and a `FLUSHDB` to clear the cache would also nuke the broker.

**Verification:**
1. `POST /api/urls` with `{"original_url":"https://example.com/long"}` → get `short_code` back.
2. `docker compose exec redis redis-cli KEYS "url:*"` → see `url:<short_code>` (cache warmed on creation).
3. `GET /<short_code>` with `follow_redirects=False` → 302 to the original URL.
4. `docker compose logs worker` → within ~1s, see `Task record_click[...] received` then `succeeded in 1.0s: None`.
5. `GET /api/analytics/<short_code>` → `{"total_clicks": 1, "last_24h": 1, ...}`. The click was persisted by the worker, not the API.

### What went wrong
Nothing broke here. The non-obvious part is the engine-per-task pattern looking wasteful — it is, and a code reviewer would flag it. The build book says so explicitly rather than pretending it's optimal. The honest framing: this is fine for a demo's traffic; for production, build the engine once in `worker_init` and reuse it, but watch out for `fork()` + SQLAlchemy connection pool issues.

---

## Entry 5 — GeoIP enrichment: populating the country field in the worker
**Files touched:** `app/services/geoip_service.py` (new), `app/worker/celery_app.py`, `requirements.txt`

### Context
The `click_events` table has a `country` column, but it was hardcoded to `None` in the worker task. The analytics endpoint already returns `top_countries`, but it's always empty because no country is ever populated. We need to look up the visitor's country from their IP address — but where should that lookup happen, and which GeoIP source should we use?

### Before you read on
You have an IP address (from `X-Forwarded-For` or `request.client.host`) arriving in the Celery `record_click` task. You need to turn it into a 2-letter country code. Before reading further: where in the architecture should the lookup happen — in the API process (before enqueuing) or in the worker (after dequeue)? And for the GeoIP data source itself, what are the two main approaches, and what are the tradeoffs of each?

### Options considered
- **Local MaxMind GeoLite2 .mmdb file + `geoip2` library** — the industry standard; memory-mapped binary search, sub-millisecond lookups, no external API dependency → rejected for this demo because it requires creating a free MaxMind account, getting a license key, downloading the `.mmdb` file (which can't be bundled in the repo — it's ~60MB and MaxMind's license forbids redistribution), and refreshing it monthly. That's real friction for someone trying to reproduce the build.
- **External API call to ip-api.com inside the Celery task** — free, no API key, no binary file, no account → chosen because the lookup happens in the worker (off the request path), so the API's rate limit (45 req/min) and network latency don't affect redirect performance.
- **External API call from the API process (before enqueuing the click)** — rejected because it would add 100-500ms to every redirect, defeating the purpose of the cache-first design.

### Why
The key insight is **where** the lookup happens. The redirect endpoint's entire value proposition is speed — it should be cache-lookup + 302, nothing else. Adding a GeoIP API call (even 100ms) to the request path would double the redirect latency. By doing the lookup inside the Celery task, we trade a small delay in *when* the country appears in analytics (1-2 seconds after the click) for zero impact on redirect performance. The user clicking the link never waits for GeoIP.

For the data source, ip-api.com is the right tradeoff for a demo: zero setup, works immediately, and the 45 req/min limit is irrelevant at demo traffic volumes. The function signature (`lookup_country(ip: str | None) -> str | None`) is identical to what a `geoip2`-based implementation would look like, so swapping to a local `.mmdb` later means changing only the function body — no callers change.

### How to build it

**Step 1: Create the GeoIP service** (`app/services/geoip_service.py`):

```python
import logging
import requests

logger = logging.getLogger(__name__)

IP_API_URL = "http://ip-api.com/json/{ip}?fields=countryCode"

# Private/loopback ranges can't be geo-located. In local dev your IP is
# 127.0.0.1 or a Docker bridge address, so we short-circuit those.
PRIVATE_PREFIXES = ("127.", "192.168.", "10.", "172.16.", "::1", "localhost")

def lookup_country(ip_address: str | None) -> str | None:
    if ip_address is None:
        return None
    if ip_address.startswith(PRIVATE_PREFIXES):
        return None
    try:
        response = requests.get(
            IP_API_URL.format(ip=ip_address),
            timeout=3,
        )
        response.raise_for_status()
        data = response.json()
        country = data.get("countryCode")
        return country if country and len(country) == 2 else None
    except Exception:
        # Don't let a GeoIP failure crash the click-recording task.
        # The click still gets recorded with country=None.
        logger.warning("GeoIP lookup failed for %s", ip_address, exc_info=True)
        return None
```

Key details:
- **`?fields=countryCode`** — ip-api.com supports field selection. Without it, the response includes timezone, lat/lon, ISP, etc. We only need the country code, so restricting fields makes the response smaller and the parse faster.
- **`timeout=3`** — the GeoIP API is a best-effort enrichment. If it's slow or down, we don't want the Celery task to hang for 30 seconds. 3 seconds is generous; most lookups complete in <500ms.
- **The `except Exception` catch is critical** — if the GeoIP API fails (rate limit, network error, malformed JSON), the click must still be recorded with `country=None`. The GeoIP call is an enrichment, not a gate. Without this catch, a transient API outage would cause the Celery task to retry (via the `self.retry` in the outer `except`), which would re-queue the click and potentially duplicate it.
- **`PRIVATE_PREFIXES` short-circuit** — in local development, `request.client.host` is `127.0.0.1` or a Docker bridge IP like `172.18.0.1`. Calling the GeoIP API on these would waste rate-limit quota and return nothing useful.

**Step 2: Call it from the worker task** (`app/worker/celery_app.py`):

Inside `record_click`, replace `country=None` with `country=lookup_country(ip_address)`. The import is done *inside the task function* (lazy import), same as the SQLAlchemy models, to avoid import-time side effects in the Celery worker process.

**Step 3: Add `requests==2.32.3` to `requirements.txt`.** We already have `httpx` for async HTTP (used by tests), but the Celery worker is synchronous and `requests` is simpler in a sync context.

**Verification:**
1. Create a short URL: `POST /api/urls` with any URL.
2. Click it with a simulated public IP: `GET /<short_code>` with header `X-Forwarded-For: 8.8.8.8` (Google's DNS — resolves to US).
3. Wait 2 seconds for the Celery task.
4. `GET /api/analytics/<short_code>` → `"top_countries": [["US", 1]]`. The country was populated by the worker.
5. Without the `X-Forwarded-For` header, your local Docker IP will be private → `top_countries` stays empty. This is expected.

### What went wrong
Nothing broke. The only subtlety was testing: in local development, `request.client.host` is always a private IP (Docker's bridge network), so `top_countries` would always be empty unless you simulate a public IP via the `X-Forwarded-For` header. The `_client_ip()` helper in `app/api/redirect.py` already checks `X-Forwarded-For` first, so sending that header in the test request is enough to verify the full pipeline. In production behind a load balancer or CDN, `X-Forwarded-For` is set by the proxy — you'd want to validate it comes from a trusted proxy, not the client, to prevent IP spoofing.

---

## Entry 6 — Rate limiting: Redis sliding window as a FastAPI dependency
**Files touched:** `app/core/rate_limit.py` (new), `app/api/redirect.py`, `app/api/urls.py`, `app/api/auth.py`

### Context
The shortener has two endpoints that need protection: the redirect (public, high-traffic — an attacker could iterate short codes to scrape every URL, as noted in Entry 3) and the shorten endpoint (someone could fill the DB with junk). Auth endpoints need protection too (brute-force password guessing). We need rate limiting that works across multiple API instances — so in-memory rate limiting is out; it has to be Redis-backed.

### Before you read on
You have Redis. You need to limit each client IP to N requests per 60-second window. Before reading further: what data structure in Redis would you use to implement a *sliding* window (not a fixed window that resets at the top of every minute)? Think about what operations you need — add an event, remove expired events, count current events. How many Redis round-trips per request?

### Options considered
- **In-memory `dict[ip] = deque[timestamps]`** — simplest, zero Redis round-trips → rejected because it doesn't work across multiple API instances. Each pod has its own dict, so the effective limit becomes `limit * num_pods`.
- **Fixed window with `INCR` + `EXPIRE`** — one Redis round-trip, but has the boundary burst problem: if the window is 60s and limit is 10, you can do 10 requests at 0:59 and 10 more at 1:01 — 20 requests in 2 seconds. → Rejected for the auth endpoint (brute-force protection), acceptable for redirect.
- **Chosen: Sliding window with Redis sorted set (ZSET)** — 3 Redis operations (pipelined into 1 round-trip), accurate to the second, no boundary burst.

### Why
A sorted set scored by timestamp gives you a sliding window naturally:
- `ZREMRANGEBYSCORE key 0 (now - window)` — drop entries older than the window. This is the "slide."
- `ZCARD key` — count entries still in the window. This is the "how many have happened recently?"
- `ZADD key {member: timestamp}` — add this request.
- `EXPIRE key window` — auto-cleanup so the key doesn't linger forever after the client stops.

The "member" needs to be unique (if two requests have the same score, only one is kept). We use `f"{timestamp}:{id(request)}"` — the Python object id guarantees uniqueness within a process. In production across multiple processes you'd use a UUID or a monotonic counter, but `id(request)` is fine for a single-process demo.

The pipeline sends all 4 commands in one round-trip, so the cost is one Redis call per rate-limited request — same as the INCR approach, but with sliding-window accuracy.

### How to build it

**Step 1: The rate limiter** (`app/core/rate_limit.py`):

The function `rate_limit(limit, window, scope)` returns a FastAPI *dependency* — a callable that FastAPI will inject into any endpoint via `Depends()`. The `scope` parameter lets you have separate buckets: `scope="redirect"`, `scope="shorten"`, `scope="auth"` each get their own Redis key namespace, so hitting the redirect limit doesn't consume your shorten budget.

```python
def rate_limit(limit: int = 10, window: int = 60, scope: str = "global"):
    async def _check(request: Request) -> None:
        ip = _client_ip(request)
        key = f"rate_limit:{scope}:{ip}"
        now = time.time()
        window_start = now - window

        pipe = redis_client.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)    # 1. drop expired
        pipe.zcard(key)                                  # 2. count remaining
        pipe.zadd(key, {f"{now}:{id(request)}": now})    # 3. add this request
        pipe.expire(key, window)                         # 4. auto-cleanup
        results = await pipe.execute()

        count = results[1]  # ZCARD result (before adding this request)
        if count >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"rate limit exceeded: {limit} requests per {window}s",
                headers={"Retry-After": str(window)},
            )
    return _check
```

**Key detail: the pipeline.** Without `redis_client.pipeline()`, each of the 4 commands would be a separate network round-trip to Redis — that's 4× the latency per request, which on the hot redirect path would be unacceptable. The pipeline batches them into one round-trip: all 4 commands are sent together, and Redis returns all 4 responses together.

**Key detail: `results[1]` is the ZCARD result.** The pipeline returns a list where index 0 is the result of the first command (ZREMRANGEBYSCORE — returns the count of removed elements, which we don't care about), index 1 is ZCARD (the count we need), index 2 is ZADD (returns the number of new elements added), index 3 is EXPIRE (returns 1 or 0). You have to know the order of your commands to index the results correctly — there's no named-result interface.

**Step 2: Pre-built dependency aliases** at the bottom of the file:

```python
RateLimitRedirect = Annotated[None, Depends(rate_limit(limit=100, window=60, scope="redirect"))]
RateLimitShorten  = Annotated[None, Depends(rate_limit(limit=20,  window=60, scope="shorten"))]
RateLimitAuth     = Annotated[None, Depends(rate_limit(limit=5,   window=60, scope="auth"))]
```

These give you a named type you can drop into any endpoint signature: `_: RateLimitAuth`. The `_` name signals "I need this dependency for its side effect (the rate check), not for its return value." This is a common FastAPI idiom for dependencies that raise on failure but return `None` on success.

**Step 3: Apply to endpoints.** Add the dependency parameter to each handler:

```python
# redirect.py — 100 redirects/minute per IP (generous; the real protection
# is against enumeration scraping, not legitimate use)
async def redirect(..., _: RateLimitRedirect) -> RedirectResponse:

# urls.py — 20 shorten requests/minute per IP
async def create_url(..., _: RateLimitShorten) -> URLResponse:

# auth.py — 5 auth attempts/minute per IP (tight, to stop brute-force)
async def register(..., _: RateLimitAuth) -> User:
async def login(..., _: RateLimitAuth) -> TokenResponse:
```

**Verification:**
1. Hit `/api/auth/login` 6 times with wrong credentials. First 5 return 401 (invalid credentials). 6th returns 429 with header `Retry-After: 60`.
2. `docker compose exec redis redis-cli KEYS "rate_limit:*"` — see keys like `rate_limit:auth:172.18.0.1`.
3. After 60 seconds (or `redis-cli DEL rate_limit:auth:*`), the limit resets.
4. Different endpoints have independent budgets: after exhausting the auth limit, redirects still work (different `scope` → different key).

### What went wrong
**`NameError: name 'Depends' is not defined` at import time.** The module-level aliases `RateLimitRedirect = Annotated[None, Depends(...)]` call `Depends()` at module import time, but the import was `from fastapi import HTTPException, Request, status` — `Depends` wasn't in the import list. The symptom: uvicorn's reloader caught the `NameError`, the API process crashed, and every request timed out (the container was up but the app inside wasn't serving). Diagnosis was straightforward — the traceback in `docker compose logs api` pointed at the exact line. Fix: add `Depends` to the `from fastapi import ...` line. Lesson: when you use a FastAPI primitive at *module level* (not inside a function), the import has to be present at import time — there's no lazy evaluation to save you.

---

## Entry 7 — Observability: Prometheus metrics and structured logging
**Files touched:** `app/core/metrics.py` (new), `app/core/logging.py` (new), `app/main.py`, `app/services/url_service.py`, `app/api/redirect.py`, `app/core/rate_limit.py`, `requirements.txt`

### Context
The app runs, but from the outside you can't tell *what it's doing* — is the cache working? How many clicks have been enqueued vs. processed? Are redirects getting slower under load? Without metrics, you're debugging blind. Two things are needed: (1) a `/metrics` endpoint that Prometheus can scrape for time-series data, and (2) structured log output so logs are machine-parseable, not just human-readable text.

### Before you read on
You need to expose metrics in Prometheus format at `/metrics`. Before reading further: what's the difference between an "infra" metric (CPU, memory, GC) and a "business" metric (cache hits, URLs created)? Which library gives you both for free, and which do you have to instrument manually? For logging: why is `print()` or `logging.info("user %s clicked %s")` not good enough for production, and what does "structured logging" actually mean in practice?

### Options considered
- **`prometheus_client` directly (manual metrics)** — full control, but you have to write a middleware to track every HTTP request's method, path, status, and duration → rejected because that's a solved problem; writing your own middleware is reinventing the wheel.
- **`starlette-exporter`** — another middleware option → rejected because `prometheus-fastapi-instrumentator` is more widely used and better maintained.
- **Chosen: `prometheus-fastapi-instrumentator` for HTTP metrics + `prometheus_client` for custom business metrics** — the instrumentator auto-tracks `http_requests_total`, `http_request_duration_seconds`, and response sizes by route/method/status, with zero code. For business-specific metrics (cache hits, click enqueues), we define custom `Counter` objects with `prometheus_client` and increment them in the service layer.
- **For logging: `structlog`** — popular structured logging library → rejected as overkill; Python's stdlib `logging` with a custom JSON formatter achieves the same output (one JSON object per line) without a new dependency. The formatter is ~20 lines of code.

### Why
The split between "infra metrics for free" and "business metrics you instrument yourself" is the key architectural decision. The instrumentator gives you everything an SRE needs to debug latency and error rates — `http_request_duration_seconds` by route, `http_requests_total` by status code — without you writing a single line of tracking code. But it can't know about your *domain*: it doesn't know what a "cache hit" is, or that a "click enqueue" is a meaningful business event. Those require explicit `Counter.inc()` calls in the right places.

For logging, the JSON formatter is deliberately simple: each log line becomes `{"timestamp": "...", "level": "INFO", "message": "...", "module": "...", "function": "...", "line": 42}`. This is what log aggregators (Loki, Elasticsearch, Datadog) expect. In development, we switch to human-readable text (`14:32:05 [INFO] app.services.url_service: cache hit for code 1eSEBk`) because JSON is hard to read in a terminal.

### How to build it

**Step 1: HTTP metrics with the instrumentator** (`app/main.py`):

```python
from prometheus_fastapi_instrumentator import Instrumentator

Instrumentator(
    should_group_status_codes=True,      # 200, 201, 204 → all "2xx"
    should_ignore_untemplated=True,       # don't track /{short_code} as separate per-code metrics
    should_respect_env_var=False,
    excluded_handlers=["/metrics"],       # don't track metrics about the metrics endpoint
).instrument(app).expose(app, endpoint="/metrics")
```

The `should_ignore_untemplated=True` is important for the redirect endpoint: without it, every distinct `short_code` would become a separate label value (`handler="/1eSEBk"`, `handler="/1eSEBr"`, ...), creating unbounded cardinality that would explode Prometheus's memory. With this flag, all redirects are grouped under the templated route `handler="/{short_code}"`.

**Step 2: Custom business metrics** (`app/core/metrics.py`):

```python
from prometheus_client import Counter

cache_hits_total = Counter(
    "url_shortener_cache_hits_total",
    "Total Redis cache hits on the redirect path.",
)
cache_misses_total = Counter(...)
clicks_enqueued_total = Counter(...)
urls_created_total = Counter(...)
rate_limit_rejections_total = Counter(
    "url_shortener_rate_limit_rejections_total",
    "Total requests rejected by the rate limiter (429).",
    labelnames=("scope",),  # labels: scope="redirect" | "shorten" | "auth"
)
```

The naming convention `url_shortener_*` prefixes all metrics so they don't collide with other services when scraped into a shared Prometheus instance. The `labelnames=("scope",)` on `rate_limit_rejections_total` lets you break down 429s by endpoint type — you'd query `rate_limit_rejections_total{scope="auth"}` to see brute-force attempts specifically.

**Step 3: Increment counters at the right points.** This is where the "how" matters:

- `cache_hits_total.inc()` — in `url_service.resolve_short_url`, inside the `if cached is not None:` branch (cache hit path).
- `cache_misses_total.inc()` — same function, right before the DB fallback query (cache miss path).
- `clicks_enqueued_total.inc()` — in `redirect.py`, right after `record_click.delay(...)`.
- `urls_created_total.inc()` — in `url_service.create_short_url`, after `_cache_url(url)`.
- `rate_limit_rejections_total.labels(scope=scope).inc()` — in `rate_limit.py`, right before raising the 429.

The placement matters: the counter must be incremented *after the thing being counted has happened*, so the metric accurately reflects reality. If you increment before the operation and the operation fails, you've over-counted.

**Step 4: Structured JSON logging** (`app/core/logging.py`):

```python
class JSONFormatter(logging.Formatter):
    def format(self, record):
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_entry, default=str)
```

Called once at app startup inside the `lifespan` context manager: `setup_logging()`. The `default=str` in `json.dumps` handles any non-serializable objects (like datetime) by stringifying them, so a log call never crashes the app due to a serialization error.

**Verification:**
1. `GET /metrics` → returns Prometheus text format with `http_requests_total`, `http_request_duration_seconds_bucket`, and all custom `url_shortener_*` counters.
2. Create a URL, then click it twice: `cache_hits_total` increments by 2, `clicks_enqueued_total` by 2, `urls_created_total` by 1.
3. Hit the auth endpoint 6 times to trigger rate limiting: `rate_limit_rejections_total{scope="auth"}` increments.
4. In dev mode, logs look like `14:32:05 [INFO] app.services.url_service: ...`. Set `APP_ENV=production` and they switch to JSON objects.

### What went wrong
**`TypeError: FastAPI.get() got an unexpected keyword argument 'include_render'`.** The `Instrumentator.expose()` method in version 7.0 doesn't accept `include_render=False` — that parameter was removed in a newer version of the library. The API docs I referenced were for a different version. The fix was simply removing the kwarg; the default behavior (no HTML rendering of metrics, just raw text) is what we want anyway. Diagnosis: the traceback pointed at the exact line in `main.py`. Lesson: when a library's API doesn't match the docs, check the installed version with `pip show` — docs are often for the latest or a different major version.

---

## Entry 8 — Pre-aggregated analytics: Celery beat + daily_stats rollup
**Files touched:** `app/models/models.py`, `app/worker/beat_tasks.py` (new), `app/worker/celery_app.py`, `app/services/analytics_service.py`, `alembic/versions/0002_daily_stats.py` (new), `docker-compose.yml`

### Context
The analytics endpoint (`GET /api/analytics/{short_code}`) was computing the timeseries chart by running `SELECT date_trunc('day', clicked_at), COUNT(*) FROM click_events WHERE url_id = ? GROUP BY 1` on every request. That's fine with 10 clicks. At 1 million clicks per URL, every analytics page load scans a million rows. We need a pre-aggregated table that the analytics endpoint can read from instead — and a scheduled job to populate it.

### Before you read on
You need to populate a `daily_stats` table from `click_events` on a schedule. Before reading further: where should the scheduling happen — in the FastAPI process, or in a separate Celery process? What's the difference between Celery `worker` and Celery `beat`? And: if the aggregation job runs every hour but aggregates per-day data, what happens if it runs twice for the same day — do you get duplicate rows, or does the second run replace the first?

### Options considered
- **Materialized view in Postgres** — `CREATE MATERIALIZED VIEW daily_stats AS SELECT ...` + `REFRESH MATERIALIZED VIEW` on a schedule → rejected because materialized views can't be refreshed incrementally (Postgres rebuilds the entire view), and you can't index a subset — the full view is locked during refresh. Fine for small datasets, painful at scale.
- **Write-through: increment daily_stats on every click** — `INSERT ... ON CONFLICT (url_id, date) DO UPDATE SET click_count = click_count + 1` inside the `record_click` task → rejected because it couples the click-recording path to the aggregation, and under concurrent clicks on the same URL+day, the `ON CONFLICT` causes row-level lock contention (multiple workers waiting on the same row lock).
- **Chosen: Separate Celery beat job that reads raw events and upserts aggregates** — decouples the write path (click recording) from the read path (aggregation). The beat job is idempotent: re-running for the same day replaces the existing aggregate row via `ON CONFLICT DO UPDATE`.

### Why
The key insight is that `beat` is a *scheduler*, not a *worker*. Celery `worker` executes tasks as they arrive in the queue. Celery `beat` is a separate process that enqueues tasks on a schedule — it doesn't execute them, it just puts them in the queue at the right time. So `beat` sends `aggregate_daily_stats` into the Redis broker every hour, and the `worker` process picks it up and runs it. This separation means:
- If the worker is down, beat still enqueues (tasks pile up in Redis).
- If beat is down, the worker still processes any tasks already in the queue.
- You can scale workers independently of the scheduler.

The job runs hourly, not daily at midnight, because the dashboard should show today's data within an hour, not wait until tomorrow. This is safe because the task is idempotent: `ON CONFLICT DO UPDATE` means running it 24 times in a day for the same `(url_id, date)` produces the same result as running it once. The aggregate is always recomputed from raw events, so it's always consistent with the source of truth.

### How to build it

**Step 1: The `daily_stats` model** (`app/models/models.py`):

```python
class DailyStats(Base):
    __tablename__ = "daily_stats"
    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(ForeignKey("short_urls.id", ondelete="CASCADE"), index=True)
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    click_count: Mapped[int] = mapped_column(default=0)
    unique_ips: Mapped[int] = mapped_column(default=0)
    top_country: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (
        UniqueConstraint("url_id", "date", name="uq_daily_stats_url_date"),
    )
```

The `UniqueConstraint("url_id", "date")` is what makes the upsert work — `ON CONFLICT` needs a unique constraint to detect the conflict against. Without it, the upsert has nothing to conflict on.

**Step 2: The migration** (`alembic/versions/0002_daily_stats.py`): standard `op.create_table` mirroring the model. Run with `alembic upgrade head`.

**Step 3: The aggregation task** (`app/worker/beat_tasks.py`):

```python
@celery_app.task(name="aggregate_daily_stats")
def aggregate_daily_stats() -> dict:
    engine = create_engine(sync_url, pool_pre_ping=True)
    now = datetime.now(timezone.utc)
    window_start = now.replace(hour=0, minute=0, second=0, microsecond=0) - timedelta(days=7)

    with Session(engine) as session:
        # 1. Group raw clicks by (url_id, day)
        raw = session.execute(
            select(
                ClickEvent.url_id,
                func.date_trunc("day", ClickEvent.clicked_at).label("day"),
                func.count(ClickEvent.id).label("click_count"),
                func.count(ClickEvent.ip_address.distinct()).label("unique_ips"),
            )
            .where(ClickEvent.clicked_at >= window_start)
            .group_by(ClickEvent.url_id, func.date_trunc("day", ClickEvent.clicked_at))
        ).all()

        # 2. For each (url_id, day), find the top country, then upsert
        for row in raw:
            top_country = session.execute(
                select(ClickEvent.country, func.count(ClickEvent.id))
                .where(ClickEvent.url_id == row.url_id, ...)
                .group_by(ClickEvent.country)
                .order_by(func.count(ClickEvent.id).desc())
                .limit(1)
            ).first()

            stmt = pg_insert(DailyStats).values(
                url_id=row.url_id, date=row.day,
                click_count=row.click_count, unique_ips=row.unique_ips,
                top_country=top_country[0] if top_country else None,
            )
            stmt = stmt.on_conflict_do_update(
                constraint="uq_daily_stats_url_date",
                set_={
                    "click_count": stmt.excluded.click_count,
                    "unique_ips": stmt.excluded.unique_ips,
                    "top_country": stmt.excluded.top_country,
                },
            )
            session.execute(stmt)
        session.commit()
```

**Key detail: `pg_insert` (not generic `insert`).** SQLAlchemy's generic `insert().on_conflict_do_update()` doesn't exist — `on_conflict_do_update` is PostgreSQL-specific and lives in `sqlalchemy.dialects.postgresql.insert`. If you use `sqlalchemy.insert`, the `on_conflict_do_update` method doesn't exist and you get an `AttributeError`.

**Key detail: `stmt.excluded`.** In a PostgreSQL upsert, `excluded` refers to the row that *would have been inserted* but conflicted. `set_={"click_count": stmt.excluded.click_count}` means "set click_count to the new value from the INSERT, ignoring the old value." Without this, the upsert would silently keep the old row unchanged — the task would appear to "run" but the numbers would never update.

**Step 4: The beat schedule** (`app/worker/celery_app.py`):

```python
celery_app.conf.update(
    beat_schedule={
        "aggregate-daily-stats": {
            "task": "aggregate_daily_stats",
            "schedule": 3600,  # every hour
        },
    },
)
```

**Step 5: The `beat` service in docker-compose.yml:**

```yaml
beat:
  build: .
  command: celery -A app.worker.celery_app beat --loglevel=info
  depends_on:
    redis: { condition: service_healthy }
```

Note: `beat` depends only on `redis` (the broker), not on `db`. It doesn't connect to the database itself — it just enqueues tasks. The `worker` process is what connects to the DB when it executes the task.

**Step 6: Read from `daily_stats` in the analytics service.** The analytics endpoint now reads the timeseries from `daily_stats` instead of re-aggregating from `click_events`. Real-time stats (total, last 24h, top countries) still read from raw `click_events` because they're small queries (COUNT with a WHERE on an indexed column). The timeseries is the expensive query, so that's what reads from the pre-aggregated table. There's a fallback: if `daily_stats` has no rows for this URL (beat hasn't run yet), it falls back to raw aggregation so the endpoint works from the moment a URL is created.

**Verification:**
1. `alembic upgrade head` → creates the `daily_stats` table.
2. Manually trigger the task: `docker compose exec worker python -c "from app.worker.beat_tasks import aggregate_daily_stats; print(aggregate_daily_stats.apply().result)"` → returns `{"rows_upserted": N, "window": "..."}`.
3. `docker compose exec db psql -U shortener -d shortener -c "SELECT * FROM daily_stats LIMIT 5;"` → see aggregated rows with `click_count`, `unique_ips`, `top_country`.
4. `GET /api/analytics/{short_code}` → timeseries still works, now reading from `daily_stats`.
5. `docker compose logs beat` → see `beat: Starting...` and `Scheduler: Sending due task aggregate-daily-stats`.

### What went wrong
Nothing broke. The main subtlety was the `pg_insert` vs `insert` distinction — it's easy to reach for `sqlalchemy.insert` by reflex and then be confused when `on_conflict_do_update` isn't there. The other subtlety is remembering that `beat` is a separate process from `worker` — if you only start `worker` and not `beat`, the schedule never fires and `daily_stats` stays empty. The analytics endpoint still works because of the raw-events fallback, which masks the problem. That's a double-edged sword: the fallback is good for robustness, but it also hides misconfiguration. In a production system you'd add an alert: "daily_stats is empty but click_events has data" → means beat is broken.

---

## Entry 9 — Expanding the test suite: isolation, cache, rate limits, and edge cases
**Files touched:** `tests/test_api.py`

### Context
The original test suite had 4 tests — health, shorten+redirect, 404, and register+login. Two problems: (1) tests weren't isolated — `test_register_and_login` created a user that persisted across runs, causing 409 Conflict on the second run; (2) no coverage of the new features: cache behavior, rate limiting, analytics, custom codes, auth edge cases. A recruiter looking at 4 tests would assume the project was a toy. We need tests that prove the architecture actually works.

### Before you read on
You're writing integration tests that hit a real running docker-compose stack (not mocks). Before reading further: how do you isolate tests from each other when they all share the same database and Redis? Specifically — if test A creates a user and test B tries to create the same user, what happens? And if test A warms the Redis cache, does test B see stale data? Sketch a fixture that makes each test independent.

### Options considered
- **Unit tests with mocked DB/Redis** — fast, no Docker needed → rejected because mocking SQLAlchemy and Redis gives you false confidence. The bugs we actually hit (timezone mismatch, passlib crash, route ordering) were integration bugs that mocks would never catch.
- **In-memory SQLite per test** — fast, isolated → rejected because we use PostgreSQL-specific features (`date_trunc`, `ON CONFLICT DO UPDATE`, asyncpg). SQLite would either silently change behavior or fail on syntax.
- **Transaction rollback per test** — start a transaction, run the test, roll back → rejected because our tests need to verify Celery tasks (which run in a separate process with a separate DB connection). The worker's writes wouldn't be visible inside the test's uncommitted transaction.
- **Chosen: Integration tests against the real stack, with a `clean_state` fixture that clears Redis keys before/after each test** — slower (8.8s for 17 tests) but tests the real system end-to-end. Database rows are allowed to accumulate (they don't affect test assertions because each test uses unique emails/codes), and Redis state is explicitly cleared.

### Why
The test suite's job is to catch regressions in the *architecture*, not to achieve 100% line coverage. The most valuable tests are the ones that verify the integration points: "does the cache actually get warmed on creation?", "does the rate limiter actually return 429?", "does the Celery worker actually persist the click?". These are questions about whether the pieces are wired together correctly — mocks can't answer them.

The `clean_state` fixture clears Redis `url:*` and `rate_limit:*` keys before and after each test. This is sufficient because:
- Cache keys are the only Redis state that affects test assertions (if a stale cache hit exists, the redirect test might pass without hitting the DB).
- Rate-limit keys must be cleared so a previous test's 429s don't block the next test.
- Database rows don't need clearing because tests use unique emails (`_unique_email()` generates `test_{timestamp}@example.com`) and assert on specific short codes, not on global counts.

### How to build it

**Step 1: The `clean_state` fixture:**

```python
@pytest.fixture(autouse=True)
def clean_state():
    import os, redis
    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=2)
    for pattern in ("url:*", "rate_limit:*"):
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
    yield
    for pattern in ("url:*", "rate_limit:*"):
        keys = r.keys(pattern)
        if keys:
            r.delete(*keys)
```

`autouse=True` means it runs for every test without being explicitly requested. The `os.environ.get("REDIS_URL")` is critical: when tests run inside the API container (`docker compose exec api pytest`), `REDIS_URL` is `redis://redis:6379/0` (the Docker service name). When running locally, it defaults to `redis://localhost:6379/0`. Without this, the fixture crashes with `ConnectionError: Error 111 connecting to localhost:6379` inside the container because `localhost` refers to the API container itself, not the Redis container.

**Step 2: Test categories.** The 17 tests are organized into 6 groups:

1. **Health** (2 tests): `/health` returns 200; `/metrics` returns Prometheus format with custom metric names.
2. **Shortening + redirect** (5 tests): basic shorten→redirect, invalid URL validation, 404 on unknown code, custom short code, custom code collision (409).
3. **Cache behavior** (2 tests): cache is warmed immediately after URL creation (verified by reading the Redis key directly); redirect works from cache after the first hit.
4. **Analytics** (2 tests): analytics endpoint shows clicks after a redirect with `X-Forwarded-For: 8.8.8.8` (so GeoIP resolves US); 404 on unknown code.
5. **Auth** (4 tests): register→login→authenticated request; wrong password (401); duplicate email (409); invalid bearer token treated as anonymous (200, empty list — not 401).
6. **Rate limiting** (2 tests): 6th auth request returns 429 with `Retry-After` header; exhausting auth limit doesn't affect shorten limit (different scope).

**Step 3: The analytics test's `time.sleep(3)`.** The click is processed asynchronously by the Celery worker. The test enqueues a click (via the redirect), then waits 3 seconds for the worker to pick it up and persist it, then checks analytics. This is a race condition in theory — if the worker is slow, the test could fail. In practice, the worker processes the click in ~1 second (we verified this in Entry 4), so 3 seconds is a safe margin. A more robust approach would be to poll the analytics endpoint until `total_clicks > 0`, with a timeout.

**Verification:** `docker compose exec api pytest -q` → `17 passed in 8.80s`. If any test fails, the first thing to check is whether `clean_state` ran (Redis might have stale rate-limit keys from a previous failed run). Clear manually: `docker compose exec redis redis-cli FLUSHDB`.

### What went wrong
**`redis.exceptions.ConnectionError: Error 111 connecting to localhost:6379`** — all 17 tests errored on the first run. The `clean_state` fixture used `redis://localhost:6379/0`, but tests run inside the API container where `localhost` is the container's loopback, not the Redis service. The Redis container is reachable at the Docker DNS name `redis` (from `REDIS_URL=redis://redis:6379/0` in `.env`). Fix: read `REDIS_URL` from the environment instead of hardcoding `localhost`. The `.env` file already sets it correctly for the container; the fixture just needs to use it. Lesson: when writing tests that run inside Docker, never hardcode `localhost` for any service — always read from the environment, because `localhost` means something different inside a container than outside.

---

## Entry 10 — README and architecture diagram
**Files touched:** `README.md`

### Context
The project has no README. A recruiter who clones the repo will see a wall of Python files and no entry point. The README is the single highest-leverage documentation artifact — it's the first thing anyone reads, and if it doesn't explain what the project is and how to run it in 30 seconds, most people won't go further.

### Before you read on
You need to write a README for a project with 6 Docker services, 8 API endpoints, Prometheus metrics, Celery beat scheduling, and a build book. Before reading further: what goes in the README, and just as importantly, what does *not*? How do you structure it so a recruiter can `docker compose up` and see something working in under a minute, without having to read 500 lines of explanation first?

### Options considered
- **Long-form README with full explanation of every design decision** → rejected because the BUILD_BOOK.md already does that. Duplicating it in the README makes the README intimidating and the build book redundant.
- **Minimal README (just `docker compose up`) with no architecture** → rejected because recruiters want to understand *what* the project demonstrates, not just that it runs.
- **Chosen: README with architecture diagram + quick start + API reference + "key design decisions" pointer to BUILD_BOOK** — the README answers "what is this, how do I run it, what are the endpoints" in under 2 minutes of reading. The BUILD_BOOK is linked for anyone who wants the "why" behind each decision.

### Why
The README's job is to get someone from `git clone` to "I can see this working" as fast as possible, then give them enough context to understand what they're looking at. The architecture diagram (ASCII, not an image — so it renders in any markdown viewer and survives git diffs) shows the request flow at a glance: client → API → Redis (cache) / PostgreSQL (persistence) / Celery (async click tracking). The "Quick start" section is 4 commands. The API reference shows example requests/responses without requiring the reader to open Swagger.

The "Key design decisions" section at the bottom is deliberately a *pointer*, not a reproduction — one-line summaries with "see BUILD_BOOK.md for the full reasoning." This avoids the trap of having two places that explain the same thing, which inevitably drift out of sync.

### How to build it

The README has 6 sections:

1. **Architecture diagram** — an ASCII art diagram showing all 6 services and the data flow. ASCII, not an image, because:
   - It renders in any markdown viewer (GitHub, VS Code, terminal).
   - It's diffable in git — changes show up as text changes, not binary blobs.
   - No image hosting or asset pipeline needed.

2. **Request flow diagram** — a step-by-step trace of what happens on a redirect (the hot path): cache check → DB fallback → 302 → Celery enqueue → worker persists. This is the single most important thing to understand about the architecture, so it gets its own section.

3. **Services table** — a 6-row table listing each Docker service, its port, and its purpose. Answers "what's running?" at a glance.

4. **Quick start** — 4 commands: `docker compose up -d`, `alembic upgrade head`, `curl /health`, open `/docs`. The goal is: copy-paste these 4 commands and see a working API in under 60 seconds.

5. **API reference** — example request/response for each endpoint group (shorten, redirect, analytics, auth, metrics). Enough to understand the API without opening Swagger, but Swagger is linked for interactive exploration.

6. **Key design decisions** — 6 one-line bullet points summarizing the most interesting architectural choices (short code generation, cache-first redirects, async click tracking, rate limiting, pre-aggregated analytics, sync worker engine), each pointing to BUILD_BOOK.md for the full reasoning.

### What went wrong
Nothing broke. The only decision point was ASCII diagram vs. image. An image diagram (drawn in Excalidraw or Mermaid) looks prettier, but ASCII wins for maintainability: you can update it in a text editor, it shows up in `git diff`, and it renders everywhere. The tradeoff is that ASCII diagrams are harder to draw and less flexible — but for a 6-service architecture, the flow is simple enough that ASCII conveys it clearly.

---

## Entry 11 — Production deployment: Render, DATABASE_URL normalization, and the Dockerfile split
**Files touched:** `Dockerfile`, `start.sh` (new), `render.yaml` (new), `app/core/config.py`, `app/core/database.py`, `app/worker/celery_app.py`, `app/worker/beat_tasks.py`, `alembic/env.py`, `docker-compose.yml`, `.env.example` (new), `.gitattributes` (new)

### Context
The app works locally via `docker compose up`, but a portfolio needs a live URL. We're deploying to Render (free tier, Docker support, managed Postgres + Redis). Three things have to change: (1) the Dockerfile is hardcoded to `--reload` (dev mode), (2) Render provides `DATABASE_URL` as `postgresql://...` but our code expects `postgresql+asyncpg://...` (async) and `postgresql+psycopg2://...` (sync for Celery), and (3) migrations need to run automatically on deploy, not manually.

### Before you read on
You're deploying a Docker app to Render. Render gives you a `DATABASE_URL` env var in the format `postgresql://user:pass@host:port/db` — no SQLAlchemy driver suffix. Your app needs *three* variants of this URL: async (for FastAPI), sync (for Celery + Alembic), and the raw one (for Render's dashboard). Before reading further: where do you put the logic that converts `postgresql://` to `postgresql+asyncpg://`? Should it live in the env var, in a config class, or in each consumer? And: should the Dockerfile have one CMD for both dev and prod, or separate Dockerfiles?

### Options considered
- **Separate Dockerfiles (`Dockerfile` + `Dockerfile.dev`)** → rejected because two Dockerfiles drift apart. The dev image might have dependencies the prod image doesn't, or vice versa. One image + runtime overrides is the Docker-native pattern.
- **Set `DATABASE_URL` with the driver suffix in Render's dashboard** → rejected because Render's managed Postgres auto-generates the `DATABASE_URL` env var without a driver suffix, and you can't override an auto-injected env var. You'd have to create a *second* env var like `ASYNC_DATABASE_URL` and keep them in sync manually.
- **Chosen: One Dockerfile, one `DATABASE_URL`, normalize in the `Settings` class** — the config class exposes `async_database_url` and `sync_database_url` as computed properties that call `_ensure_driver()`. Every consumer (`database.py`, `celery_app.py`, `beat_tasks.py`, `alembic/env.py`) asks for the variant it needs. One source of truth, no manual sync.

### Why
The `_ensure_driver()` function is the crux. It strips any existing driver suffix (`+asyncpg`, `+psycopg2`) from the URL, then injects the one the caller wants:

```python
def _ensure_driver(url: str, driver: str) -> str:
    if "postgresql+asyncpg://" in url:
        base = url.replace("postgresql+asyncpg://", "postgresql://")
    elif "postgresql+psycopg2://" in url:
        base = url.replace("postgresql+psycopg2://", "postgresql://")
    else:
        base = url
    return base.replace("postgresql://", f"postgresql+{driver}://")
```

This handles three cases: Render's bare `postgresql://` (injects the driver), local dev's `postgresql+asyncpg://` (strips and re-injects the right one), and any future URL format. The `Settings` class then exposes:

```python
@property
def async_database_url(self) -> str:
    return _ensure_driver(self.DATABASE_URL, "asyncpg")

@property
def sync_database_url(self) -> str:
    return _ensure_driver(self.DATABASE_URL, "psycopg2")
```

Every consumer calls `settings.async_database_url` (the FastAPI engine) or `settings.sync_database_url` (Celery tasks, Alembic). Nobody calls `settings.DATABASE_URL` directly for engine creation — it's the raw platform-provided value, not usable for SQLAlchemy without normalization.

### How to build it

**Step 1: The production Dockerfile.** Key changes from the dev version:

```dockerfile
# Non-root user (Render runs containers as root by default — security risk)
RUN useradd -m -u 1000 appuser
USER appuser

# No --reload. Uses PORT env var (Render sets this, usually 10000).
# start.sh runs migrations before starting uvicorn.
CMD ["./start.sh"]
```

The dev override lives in `docker-compose.yml`, not in a second Dockerfile:
```yaml
api:
  command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

This means `docker compose build` produces the production image, and docker-compose overrides the CMD for dev. One image, two run modes.

**Step 2: `start.sh` — migrations before server start:**

```bash
#!/bin/sh
set -e
echo "Running database migrations..."
alembic upgrade head
echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 2
```

`exec` replaces the shell process with uvicorn — without it, uvicorn would be a child of the shell, and `docker stop` would send SIGTERM to the shell (which doesn't forward it to uvicorn, causing a 10-second timeout before Docker SIGKILLs).

**Key detail: migrations on every deploy.** `alembic upgrade head` is idempotent — if no new migrations exist, it prints "Running upgrade" with no SQL and exits 0. Running it on every deploy means you never have to manually migrate after pushing a schema change. The risk: if a migration is destructive (e.g., drops a column), it runs automatically on deploy. For a portfolio project this is fine; in a real production system you'd run migrations as a separate deploy step with a manual gate.

**Step 3: `render.yaml` — infrastructure as code.** Defines 4 resources:

```yaml
databases:
  - name: shortener-db        # Managed PostgreSQL (free for 90 days)
  - name: shortener-redis     # Managed Redis (free tier, 15MB)

services:
  - type: web                 # FastAPI (free tier, spins down after 15 min)
    name: url-shortener-api
    runtime: docker
    healthCheckPath: /health
    envVars:
      - key: DATABASE_URL
        fromDatabase: { name: shortener-db, property: connectionString }
      - key: REDIS_URL
        fromService: { type: pserv, name: shortener-redis, property: connectionString }
      - key: SECRET_KEY
        generateValue: true    # Render generates a random secret
      - key: SHORT_URL_BASE
        value: https://url-shortener-api.onrender.com

  - type: worker              # Celery worker + beat (Starter plan, ~$7/month)
    name: url-shortener-worker
    dockerCommand: celery -A app.worker.celery_app worker --beat --loglevel=info --concurrency=2
```

**Key detail: `worker --beat` combines worker + beat in one process.** In local dev they're separate containers (`worker` + `beat` in docker-compose). On Render, each background worker costs ~$7/month, so we combine them with `--beat` to save one service. This is a deliberate tradeoff: if the worker restarts mid-schedule, a beat tick might be missed. For a demo this is fine; in production you'd separate them.

**Key detail: `generateValue: true` for SECRET_KEY.** Render generates a random 32-byte hex string and injects it as the env var. You never see it — it's stored in Render's secret store. This is better than committing a secret to the repo, even for a demo.

**Key detail: Redis on Render doesn't support multiple databases.** Locally we use Redis DB 0 for cache, DB 1 for broker, DB 2 for results. On Render's managed Redis, you get one database. The `REDIS_URL` from Render doesn't include a `/0` suffix — it's just `redis://host:port`. This works because Celery's broker keys (`celery-*`, `_kombu.*`) and our cache keys (`url:*`) and rate-limit keys (`rate_limit:*`) all use distinct prefixes, so they coexist in one keyspace without collision. The `CELERY_BROKER_URL` and `CELERY_RESULT_BACKEND` env vars are set to the same Redis URL as `REDIS_URL` — they all point to the same instance.

**Step 4: Update all consumers to use normalized URLs.**

| File | Before | After |
|------|--------|-------|
| `app/core/database.py` | `settings.DATABASE_URL` | `settings.async_database_url` |
| `app/worker/celery_app.py` | `.replace("postgresql+asyncpg://", ...)` | `settings.sync_database_url` |
| `app/worker/beat_tasks.py` | same .replace hack | `settings.sync_database_url` |
| `alembic/env.py` | same .replace hack | `settings.sync_database_url` |

**Verification:**
1. Local: `docker compose up -d`, `docker compose exec api pytest -q` → `17 passed`. The normalization works for both local (`postgresql+asyncpg://...`) and Render (`postgresql://...`) URLs.
2. `docker compose exec api python -c "from app.core.config import settings; print(settings.async_database_url)"` → prints the URL with `+asyncpg` driver, regardless of what format `DATABASE_URL` is in.
3. `docker compose exec api python -c "from app.core.config import settings; print(settings.sync_database_url)"` → prints with `+psycopg2`.
4. Production: push to GitHub, connect Render to the repo, Render auto-builds the Docker image, runs `start.sh` (migrations + uvicorn), health check at `/health` passes, service goes live.

### What went wrong
**`celerybeat-schedule` file committed to git.** Celery beat creates a local file (`celerybeat-schedule` or `celerybeat-schedule.db`) to persist its schedule state across restarts. It's a binary runtime artifact that should never be in version control. Caught it during the initial `git add -A` — added `celerybeat-schedule*` to `.gitignore` and removed it from tracking with `git rm --cached`. Lesson: always review `git status` before committing, especially the first commit of a project — runtime artifacts, `.pyc` files, and local configs sneak in.

**Docker Desktop stopped mid-deployment.** The Docker daemon on the development machine crashed during the rebuild step (Windows `com.docker.service` stopped). This wasn't a code issue — restarting Docker Desktop and re-running `docker compose up -d` resolved it. The code changes were already validated by the test suite running inside the container before the crash, so no rework was needed. Lesson: keep your work committed before doing infrastructure operations, so a Docker crash doesn't lose uncommitted code.

---

## Entry 12 — Free-tier fallback: BackgroundTasks when Celery is too expensive
**Files touched:** `app/services/click_service.py` (new), `app/services/geoip_service.py`, `app/api/redirect.py`, `app/core/config.py`, `render.yaml`, `.env`, `.env.example`, `requirements.txt`, `tests/test_api.py`

### Context
Render's free tier covers the web service, Postgres, and Redis — but not background workers. The Celery worker requires a Starter plan at ~$7/month. Without it, click tracking silently fails: the redirect endpoint calls `record_click.delay()`, the task is enqueued to Redis, but no worker ever picks it up. Analytics shows zero clicks forever. For a portfolio project that should demonstrate *working* analytics, paying $7/month just to have a worker process running is a hard sell. We need click tracking to work without a dedicated worker process.

### Before you read on
You have a Celery-based click tracker. The redirect endpoint calls `record_click.delay(url_id, ip, ua, referer)` and returns 302 immediately. You can't afford a Celery worker on Render's free tier. Before reading further: what's the cheapest way to still record clicks? The redirect still needs to return 302 fast — the click write can't block the response. What FastAPI primitive runs code *after* the response is sent, inside the API process itself? And what's the tradeoff vs. a real Celery worker?

### Options considered
- **Synchronous inline write** — `INSERT INTO click_events` inside the redirect handler, before returning 302 → rejected because it adds 5-20ms of DB write latency to every redirect. The whole point of the architecture is cache-lookup + 302, nothing else.
- **Spin up a Celery worker inside the API container** — run `celery worker` as a subprocess alongside uvicorn → rejected because it requires a process manager (supervisord), doubles the memory footprint, and the worker would die when the free-tier web service spins down after 15 min of inactivity.
- **Drop click tracking entirely on free tier** → rejected because analytics is a core feature the portfolio needs to demonstrate.
- **Chosen: FastAPI `BackgroundTasks`** — the redirect handler receives a `BackgroundTasks` instance, adds the click-writing coroutine to it, and returns 302. FastAPI runs the task after the response is sent, in the same event loop as the API. No extra process, no extra cost.

### Why
FastAPI's `BackgroundTasks` is purpose-built for this exact use case: "do something after the response is sent, but don't make the client wait for it." It runs in the API process's event loop — the 302 goes out immediately, then the click is written to Postgres. The tradeoff vs. Celery is:

| | Celery worker | BackgroundTasks |
|---|---|---|
| Cost | $7/month on Render | Free |
| Survives API crash? | Yes (task re-queued) | No (lost) |
| Retries on failure? | Yes (`max_retries=3`) | No |
| Runs when API spun down? | Yes (separate process) | No (no process running) |
| Latency on redirect | Same (both are fire-and-forget) | Same |

For a portfolio project where the goal is "recruiter clicks a shortened URL and sees the click in analytics," BackgroundTasks is more than sufficient. The click is written within milliseconds of the 302, well before anyone navigates to the analytics endpoint. The only scenario where it fails is if the API process crashes in the ~10ms window between sending the 302 and completing the background task — vanishingly unlikely at demo traffic volumes.

The architectural win is that the *same code path* works in both modes. The redirect endpoint calls `track_click(background_tasks, ...)`, which checks `settings.CLICK_TRACKING_BACKEND` and dispatches to either `record_click.delay()` (Celery) or `background_tasks.add_task(_record_click_async, ...)` (BackgroundTasks). Switching between modes is a single env var change — no code changes, no redeploy of the redirect handler.

### How to build it

**Step 1: The config flag** (`app/core/config.py`):

```python
CLICK_TRACKING_BACKEND: str = "celery"  # or "background_tasks"
```

**Step 2: The async click recorder** (`app/services/click_service.py`):

```python
async def _record_click_async(url_id, ip_address, user_agent, referer):
    country = await lookup_country_async(ip_address)
    async with SessionLocal() as session:
        click = ClickEvent(url_id=url_id, ip_address=ip_address,
                           user_agent=user_agent, referer=referer,
                           country=country)
        session.add(click)
        await session.commit()
```

**Key detail: `SessionLocal()`, not the request's session.** The request's DB session (`db: SessionDep`) is closed by the time the background task runs — FastAPI's dependency cleanup happens after the response but before background tasks. So the background task creates its own session via `SessionLocal()`. This is why the function is `async` — it uses the async session factory directly.

**Step 3: The dispatcher** (`track_click` in the same file):

```python
def track_click(background_tasks, url_id, short_code, ip_address, user_agent, referer):
    if settings.CLICK_TRACKING_BACKEND == "background_tasks":
        background_tasks.add_task(_record_click_async, url_id=url_id, ...)
    else:
        from app.worker.celery_app import record_click
        record_click.delay(url_id=url_id, short_code=short_code, ...)
```

The Celery import is *lazy* (inside the `else` branch) — when running in `background_tasks` mode, the Celery module is never loaded, and the Celery broker connection is never attempted. This matters on Render's free tier: there's no Celery worker, so attempting to connect to the broker would just add a timeout. By not importing it at all, the app starts faster and doesn't log spurious connection errors.

**Step 4: The redirect endpoint** (`app/api/redirect.py`):

```python
async def redirect(
    short_code: str,
    request: Request,
    db: SessionDep,
    user: CurrentUserOptional,
    background_tasks: BackgroundTasks,  # ← injected by FastAPI
    _: RateLimitRedirect,
) -> RedirectResponse:
    ...
    track_click(background_tasks=background_tasks, ...)
    return RedirectResponse(url=target["original_url"], status_code=302)
```

`BackgroundTasks` is a FastAPI dependency — just adding it to the signature is enough. FastAPI populates it automatically and runs any tasks added to it after the response.

**Step 5: GeoIP for both modes.** The sync `lookup_country()` (Celery path) and async `lookup_country_async()` (BackgroundTasks path) both use `httpx` — `httpx.get()` for sync, `httpx.AsyncClient` for async. This replaced the `requests` dependency entirely (httpx was already in requirements for tests). One library, both modes, no extra dependency.

**Step 6: render.yaml** — removed the `worker` service, set `CLICK_TRACKING_BACKEND=background_tasks` on the web service. The render.yaml now defines 3 resources (web, postgres, redis) instead of 5. All on the free tier.

**Verification:**
1. Set `CLICK_TRACKING_BACKEND=background_tasks` in `.env`.
2. Create a URL, click it with `X-Forwarded-For: 8.8.8.8`.
3. Within 1 second (no 3s Celery wait needed), `GET /api/analytics/{code}` shows `total_clicks: 1` and `top_countries: [["US", 1]]`.
4. Switch back to `CLICK_TRACKING_BACKEND=celery` — same behavior, but clicks are processed by the Celery worker instead.
5. `pytest -q` → 18 passed (includes `test_background_tasks_click_tracking` which toggles the flag at runtime).

### What went wrong
Nothing broke. The implementation was clean because the GeoIP service already had a well-defined interface — adding an async variant was a 15-line addition. The only subtlety was the session lifecycle: the first attempt used the request's `db` session, which was already closed by the time the background task ran. The error was `StatementError: Object is not bound to a Session`. Diagnosis: the background task runs *after* FastAPI's dependency cleanup, which closes the request's session. Fix: create a new `SessionLocal()` inside the background task function. This is a general pattern for BackgroundTasks that touch the DB — never share the request's session, always create your own.

---

## Entry 13 — UI redesign: the "paper & ink" theme and why every interaction got a state
**Files touched:** `app/static/index.html`

### Context
The original UI was a competent but generic light theme: Tailwind-default blue (`#3b82f6`), DM Sans, flat `#fafafa` background. It looked like every other tool built from the same defaults - nothing about it said "SnipURL". The goal for the redesign: keep 100% of the existing API contract and JS logic shape, but give the page an actual point of view, and close the UX gaps (no loading states, browser `confirm()` dialogs, no keyboard support, toasts without icons).

### Before you read on
You have a single-file HTML app where all styling flows through ~15 CSS variables. Before reading further: what aesthetic actually fits a tool named *Snip*URL whose core gesture is "paste, cut, share"? Sketch two directions - one dark/technical, one warm/tactile - and decide which one survives contact with QR codes (which need a white box) and analytics charts (which need readable grids).

### Options considered
- **Dark developer-tool theme** (near-black, neon accent) - rejected: QR codes force a white box that glares against a dark page, and analytics modals become low-contrast squinting exercises.
- **Generic SaaS light theme v2** (new blue, more whitespace) - rejected as sideways motion; still indistinguishable from a thousand dashboards.
- **Chosen: warm "paper & ink" atelier theme** - cream paper background with subtle SVG grain, deep pine-green primary, amber accents, Fraunces serif display type. The name *Snip* evokes scissors/craft/stationery; the palette leans into it instead of fighting it.

### Why
Three reasons this direction wins:

1. **Contrast hierarchy is physical, not just color.** Ink-on-paper is the most legible metaphor there is. Pine green (`#216B47`) on cream passes contrast comfortably while being instantly distinct from default-blue tools.
2. **The serif display font earns the brand.** Fraunces (with its optical-size axis) gives the hero and section headings an editorial voice; Instrument Sans handles UI text; IBM Plex Mono marks anything machine-generated (short codes, aliases, table headers). Three fonts, three jobs, no overlap.
3. **Every state now has a designed answer.** The old UI had exactly two interaction states (idle, error-toast). The redesign adds: button loading spinners ("Snipping…"), copy-button confirmation swaps, spinning refresh icon, pulsing health pill with ok/warn/offline variants, skeleton-free but explicit "Loading…" row, count chips, and empty states with an icon.

### How to build it

**Step 1: Tokenize the palette first.** Everything hangs off `:root` variables - `--paper`, `--surface`, `--pine`, `--amber`, plus shadow/radius/easing tokens including a shared `--ease: cubic-bezier(.22,1,.36,1)` so all motion feels like one hand wrote it.

**Step 2: Atmosphere before components.** Two fixed pseudo-layers sit under everything: an inline-SVG `feTurbulence` noise texture at 5% opacity (multiply blend), and two blurred radial glows (green top-left, amber top-right). This costs zero requests and turns a flat background into a lit surface.

**Step 3: Motion with restraint.** One orchestrated load sequence (hero → form → table, staggered via `animation-delay`), one signature moment (the amber underline draws itself under the italic *Share.* via stroke-dashoffset), and micro-transitions everywhere else. Modals animate opacity+visibility on the overlay and transform on the panel so both can transition (you can't transition `display:none`). A `prefers-reduced-motion` block flattens all of it.

**Step 4: Replace browser chrome with in-page chrome.** `confirm()` became a custom overlay reusing the modal system (`askDelete()` stores the pending id, `reallyDelete()` executes). Toasts became dark ink cards with check/x icon chips and a shrinking progress bar timed to the auto-dismiss.

**Step 5: Keyboard support.** `/` focuses the URL input (guarded so it doesn't fire while typing in inputs, hinted by a kbd chip shown only when the field is empty via `:placeholder-shown`-style focus rules); Escape closes any open overlay.

**Step 6: Harden the render path.** Row templates now escape interpolated values (`esc()` helper) before dropping them into `title="..."` attributes - a long URL containing a quote previously broke the attribute silently.

**Verification:** extracted the inline `<script>` and ran `node --check` (syntax OK); parsed the HTML with Python's `html.parser` tag-balance checker (no mismatches, nothing unclosed); API contract unchanged - same endpoints, same payloads, same localStorage keys.

### What went wrong
Two self-inflicted bugs during the rewrite. First, the `esc()` helper was written with `.replace(/"/g:'&quot;'` - colon instead of comma - which `node --check` caught immediately; lesson: always syntax-check template-heavy inline JS rather than eyeballing it. Second, the result panel's entrance animation only plays when `display` toggles, so re-snipping another link within the same page life wouldn't replay it; fixed by forcing a reflow between hide and show (`el.style.display='none'; void el.offsetWidth; el.style.display='block'`) - the standard trick for restarting a CSS animation.

## Entry 14 — Registering the task that beat already publishes
**Files touched:** `app/worker/celery_app.py`, `tests/test_worker_registration.py`, `scripts/verify_worker_registration.py`, execution/input documents.

### Context
Main now contains the owner-merged foundation audit (PR50), but not the original checkout's uncommitted QR prototype or later journal entries. This entry is appended to the tracked journal in an isolated worktree; that original journal remains intact. AUD04 identified that beat publishes aggregate_daily_stats while a new worker never imports its definition.

### Before you read on
The scheduler sends a task name, not its implementation. How do you prove the worker can find that function without a test accidentally importing it first?

### Options considered and why
Import beat_tasks eagerly at the bottom of celery_app, or declare it in Celery's include list. The module already imports celery_app to decorate its function; choose the loader include to avoid a circular eager dependency. It changes startup discovery, not task timing, queries, retention or pool budgets. Those still belong to the broader parent issue and owner decisions.

### How to build it
1. In a regression test start a fresh Python interpreter with synthetic configuration pointing to unused ports. Call celery_app.loader.init_worker(), collect beat_schedule task names, and report names absent from celery_app.tasks. Do not import beat_tasks in the test itself. Before the fix the assertion fails with aggregate_daily_stats missing.
2. Add include=["app.worker.beat_tasks"] to the Celery constructor. The loader imports it during worker initialization, after the app exists. Repeat the same test; an empty missing list demonstrates that discovery works without a broker or DB.
3. Add a separate isolated real-service check that starts one real worker, has one Celery scheduler publish a due rollup, and checks PostgreSQL for the expected fixture counts. Verify the child task's behavior before marking it done; registration alone cannot prove delivery.
4. Keep raw test logs under ignored output/. Record versions, fixture setup, commands and failures in the execution ledger. Preserve existing hourly production scheduling. No latency/load result follows from this startup fix.

### What went wrong so far
The regression reproduced the missing task (one failing test). Docker Desktop was stopped; its start command returned a starting message but the Linux engine endpoint was still absent on the first check. Continue to inspect the live startup state rather than treating the message as proof of readiness. Real delivery remains unverified until the service experiment finishes.

### Verified outcome
The engine became available (29.7.2). The first fixture setup correctly stopped on an inspect error; Docker's absent-container message uses lowercase, so match the specific no-such-object text case-insensitively while still refusing other errors. Repeated setup created only labeled loopback fixtures. One solo worker consumed record_click and the scheduler's aggregate_daily_stats through Redis; PostgreSQL contained two daily rows with counts4 and2. The production hourly interval stayed3600. Unit regression passed; cleanup removed only those fixtures and the spawned worker. This proves local task delivery, not pooling, idempotency, Linux prefork support or capacity.

The first sub-issue attachment used issue_id; GitHub required sub_issue_id and rejected it. Re-read the existing marker before retrying so no duplicate child was created. A transient DNS failure also interrupted metadata synchronization; refreshed state before retrying. GitHub's current PR response did not include merge_commit_sha, so verify the merged flag/head commit and actual ancestry in fetched origin/main rather than assuming that field exists.

## Entry 15 — Keeping local configuration out of Git and Docker
**Files touched:** `.gitignore`, `.dockerignore`, `.env.example`, `README.md`, `scripts/verify_configuration.py`, verification notes. `.env` is removed from the branch index, not from the local filesystem.

### Context
AUD02 confirmed a tracked .env. Its values and active exposure are unknown; credential rotation remains an owner decision. The Dockerfile uses COPY . ., so Git ignore rules alone would not prevent environment files entering build context/layers. Supersedes the implicit configuration distribution in earlier quick-start instructions; do not rewrite Git history or rotate production credentials in this fix.

### Why and how to build it
Keep local credentials where they are, remove only their index entry with git rm --cached -- .env, ignore .env variants, and explicitly allow .env.example in Git. Docker has independent ignore rules: exclude root/nested dotenv files plus Git, virtualenv and output directories. Publish only fake placeholders that match current required settings; retain existing service defaults rather than choosing new launch budgets.

Verify before changing anything: git ls-files reports .env and the configuration boundary checker fails. After staging the scoped change, use git metadata/check-ignore to prove private names are excluded and the public example remains tracked. The helper reads only the public template and forces its synthetic values before app config import, so it does not load real local credentials for validation. It opens no DB/broker connections.

To prove actual Docker semantics, copy only .dockerignore into a temporary owned directory containing synthetic .env variants, nested private markers, Git/venv/output markers and an allowed application fixture. Build FROM scratch with COPY . /context and the local exporter. The allowed fixture must exist, and every private marker must be absent. Do not build this test from the actual repository context. Remove only that temporary directory after verifying its resolved path stays inside output/.

### Verification in progress
The pre-change checker failed because .env remained tracked. The after-change Git/template/Docker checks will be recorded once run. No real credential was displayed, no history was rewritten and no production value was changed. Existing local files and the original dirty checkout remain intact.

The first Docker assertion incorrectly searched absolute path components for output; every exported fixture lives under the test's own output directory, so even the allowed application file was flagged. The actual copied names contained no dotenv/Git/venv files. Fix the verifier to inspect paths relative to the exported context, then rerun the actual Docker check rather than treating the false assertion as a pass.

Review caught a second detail: Pydantic reads dotenv even when environment values override its settings. To avoid reading the local file at all, run the subprocess from an empty temporary working directory and put the repository on PYTHONPATH. The final Git/template/actual Docker checks passed with this revised helper on Docker29.7.2. No application connections were opened. Full reproduction and limits are in docs/verification/2026-10-06-configuration-boundaries.md.

The owner authorized merging PRs on2026-10-06. Reviewed worker PR52 merged as0f316c69f88374a177ce5d4abb58c153d8e249d3; GitHub closed child51. Parent45 remains open. Numerical, deployment and privacy decisions remain pending; merge authority does not supply them.

## Entry 16 — Turning local foundation checks into isolated CI
**Files touched:** `.github/workflows/foundation-checks.yml`, `requirements-ci.txt`, worker test/harness, CI documentation and execution ledger.

### Context and options
Child F03a/#55 covers deterministic foundation correctness; parent F03 still needs approved architecture/budgets, complete API/QR/frontend checks and actual security scanning. Reuse the already verified service harness or create a separate workflow-only integration runner. Reuse keeps local and Linux evidence comparable and retains the existing container label/port guard. The existing API suite clears broad Redis namespaces and defaults to a local API; do not run it against an unspecified service in this child.

### How to build it
1. Pin official checkout/setup-python/upload-artifact actions to full commit SHAs obtained from their upstream tag refs. Use contents:read, no persisted checkout credentials, pull_request rather than privileged pull_request_target, and a bounded GitHub-hosted Linux job. No deployment credentials or production endpoints are used.
2. Install existing pinned direct requirements plus psutil7.2.2, which the harness already needs to clean only its spawned process tree. No extra production dependency is added. Transitive hashes/advisory checks remain parent work.
3. Run configuration boundaries and the fresh-interpreter worker test, then create the harness's owned disposable services. Run its migration/real-delivery check and clean only those fixtures in an always step. Upload only synthetic logs/evidence from its output directory, with a short artifact lifetime.
4. Apply the empty-directory isolation found in Entry15 to worker imports too. Put the repository on PYTHONPATH; resolve Alembic script paths through a temporary ini file. Start descendants in the empty cwd so no relative dotenv lookup reads the real local file. Production settings remain unchanged.
5. Verify locally, push a scoped PR, then inspect the actual GitHub job for this head before merging/closing the child. Writing valid YAML is not proof the Linux job works. Record a failed job and repair it if the run exposes a missing dependency or platform difference.

### Verification in progress
Configuration child53 closed after reviewed PR54 merged as e3a97a84a2040a89976d87c0787a7d2c3e010e0e. Worker51 is also closed. Neither parent nor milestone is complete. CI is unverified until the local and actual GitHub runs finish.

The first local unit run used the system Python3.13/pytest9.1.1 and passed once, but that is not the declared baseline. Use the existing Python3.12.13 environment with pytest8.3.4/Celery5.4.0 for the next local run; CI installs its own declared requirements. A prematurely started verify command correctly refused services not yet created. Startup then created its owned containers, but failed leaving an empty cwd on Windows: TemporaryDirectory cannot delete the process's current directory. Add a finally that restores the previous cwd before cleanup, remove only the owned fixtures, and repeat startup/verification sequentially. Record the failure rather than treating container creation as a successful run.

The sequential rerun passed: Python3.12.13/pytest8.3.4 one registration test (10.46s), Git/template/actual synthetic Docker boundaries, migrations and one real Celery5.4.0 scheduler/solo worker delivery. Counts4/2 and period3600 match the earlier fixture. Descendant temporary directories are kept inside the parent's owned directory so termination does not leak separate worker temp folders. The actual Linux CI result is still pending at this point.

PR56 head840d643 then passed actual GitHub run37521244163, job112466887529. Queried the run/job/artifact APIs: every check, owned cleanup and upload step succeeded, with a foundation-verification artifact. Reviewed/merged exact head as bad860b57261b5225eaf9a033b40a5a4ae1ac08e; child55 closed, parent3 remains open. This is now Linux solo correctness evidence, not prefork or capacity proof. Original76 source hashes still match. Older audit draft49 was closed as superseded after proving its exact head is already in main through owner PR50; roadmap PR41 was already marked merged.

## Entry 17 — Auditing dependencies before choosing upgrades
**Files touched:** advisory evidence/tooling and execution docs on an isolated branch from main ddddc5175e3dbd9c3bac8ac73b13a8eaa1f53c50. Application dependency upgrades are not part of the evidence step.

### Context and choice
F03 requires actual advisory checks before upgrades; existing correctness CI cannot certify dependency security. Scan the public requirements with PyPA's pip-audit, rather than treating a green test run as an advisory result or blindly applying all suggested upgrades. A separate tool environment keeps the scanner's dependencies out of the application environment. Scanning public package names/versions does not require production credentials or F01 provider/budget decisions.

### How to build the evidence
Create an ignored tool virtualenv with the existing Python3.12 interpreter and install a pinned pip-audit2.10.1 from public PyPI. Disable user/system pip configuration with PIP_CONFIG_FILE=os.devnull and remove inherited PIP_* settings so private package indexes cannot enter the experiment. Use explicit public index/service, bounded requests and JSON without long descriptions. Resolve the requirements including transitives; record OS/Python/tool/commit and exact versions. Do not use --fix, ignored findings or a zero return code as the only evidence; validate the resulting dependency list and distinguish findings from resolver/service failures.

Map findings to primary advisory/maintainer sources and linked remediation. Record application reachability as static evidence or unverified, not an exploitability guarantee. A Windows scan omits Linux-only distributions, so record that coverage gap until an actual Linux counterpart runs. Hosted frontend/unpublished prototype dependencies remain separate scope. Parent security/release gates stay open when advisories exist.

### In progress
The first child-issue synchronization timed out during a read-only API request; refresh/dedupe before retrying. Virtualenv creation has a live command handle and remains pending, so do not restart it merely because output is quiet. No scan result or clean-security claim exists yet.

Child58 was created and attached to3 after the read-only retry; the same marker prevented duplicates. The tool virtualenv completed, but scanner installation failed: pip reported a CacheControl/filelock resolution error after PyPI read timeouts. This is a tooling/resolution failure, not an application advisory finding. Do not loosen app requirements in response to it. Investigate the specific public dependency/index and run an actual Linux counterpart; record failures distinctly. No application scan has completed at this point.

PR59 head5db24d0 ran actual Linux advisory collection37525390386/job112480968985 and correctness37525390328/job112480983369. Retrieved the expected three-file advisory artifact with account authentication kept only in memory; confirmed run/head and allowed filenames before extraction. The Linux report resolves61 packages and records35 advisory records in5 packages. Grouping by package/id gives18 unique advisory IDs; duplicate IDs/aliases mean neither35 nor18 is a verified count of distinct exploitable vulnerabilities. Preserve raw records and report unique IDs separately.

The second unchanged scanner installation succeeded, including filelock4.0.12. A too-early local audit had returned PackageNotFoundError before installation completed; repeat only after its handle is terminal. The actual Windows scan is now running. The Linux result is known_vulnerabilities with scanner exit1, not clean security, even though the evidence-collection job succeeds. Linked remediation will cover JOSE/ECDSA, compatible framework/parsers and test tooling; every package remains a release follow-up. No app pins were loosened to fix installation.

All18 canonical PyPA source links returned200 and contained the expected identifier. Created/verified M0 children60/61/62 of3 mapping all packages. The Windows run eventually ended with PermissionError during temporary cleanup and no completed baseline, so do not infer Windows results from Linux. Pipes/descendants can outlive a directly killed scanner: replace capture_output with a file log, Popen.wait with a finite timeout and psutil cleanup scoped to that Popen tree. Pin psutil7.2.2 in tool requirements, keep child temporary files inside the owned run directory, verify its resolved boundary, and record operational failure class separately. No global process kill or application environment change is used.

Local real process cleanup test passed once in2.105s; Linux head50f6bc0 passed advisory37527373512 and correctness37527373523, including the added process test. The revised Windows scan ended with a logged PyPI ReadTimeout and separate RuntimeError failure JSON, so its coverage is incomplete and recorded as such. Stop retrying unchanged network failures in this step; actual Linux evidence remains authoritative for the Linux baseline. All findings map to verified open children60/61/62, with parent3/security43 and release gates still open.

PR59 final head91123c8 passed actual Linux advisory37532103550 and foundation37532103585, then merged as e0ad487ecc0e0501d104e6a03fc01ede66220f4c. This completes discovery58; all remediation/release gates remain open. A transient GitHub DNS failure delayed the documentation push; retry succeeded without recreating the PR or discarding the saved commit.

## Entry 18 — Removing unused JWT crypto without breaking existing tokens
**Files touched:** security helper, runtime pin, isolated historical fixture/tests, ADR0003 and verification tooling.

### Context and options
Issue60 targets the actual JOSE/ECDSA advisory chain. Our observed app only signs/verifies HS256. Upgrade JOSE or use a focused JWT implementation: the former retains its unused ECDSA chain with an unfixed finding, so choose PyJWT2.15.1 without crypto extras. A library swap must preserve existing valid app-issued tokens; changing keys/TTL/session policy in the same repair would hide whether interoperability works.

### How to build it
Replace the runtime pin/import, keep encode claims sub/exp and the fixed HS256 decode allow-list. Treat non-string subjects and malformed numeric expiry safely, keeping the existing optional-exp contract rather than silently selecting a new session policy. Create a separate historical interpreter from requirements-legacy-jwt.txt; never install it into the app environment. Pass synthetic key/claims through captured stdin/stdout, generate an old token accepted by the new helper, then verify a new app token with the old verifier. Store assertions/results, not token bytes. Load application settings in an empty cwd before importing app modules so tests cannot read local dotenv values. Then run isolated real API/PostgreSQL/Redis, worker and fresh resolution/advisory checks.

### In progress and failures
Runtime library choice is documented; results are pending. GitHub reads/push briefly failed with DNS errors, recovered, and the reviewed evidence PR merged. The existing Python3.12 app interpreter lacks pip, so a first isolated-target PyJWT installation command failed without changing it; use the already isolated audit tool's pip to populate ignored output/jwt-dependency/vendor for local tests. This does not remove the old library from the original owner's environment or prove a clean application install.

Eight cross-library/negative contract tests passed with that isolated PyJWT target. Fresh app virtualenv installation is running separately. The first owned PostgreSQL/Redis startup timed out during a5s readiness subprocess and removed both fixtures; the sequential retry succeeded. Do not increase production connection budgets to fix a local Docker startup fluctuation. Extend the existing read-only CI with a separately isolated legacy interpreter, new contract tests and guarded real HTTP checks. Add a targeted fresh-audit gate requiring no python-jose/ecdsa in app resolution and no known PyJWT findings, while leaving framework/test-tool findings visible. A historical fixture being intentionally vulnerable does not make it a runtime dependency or release exception.

That local fresh install hit its300s process limit, and the existing worker check did not become ready within30s. Both are failed/incomplete checks; stop the owned worker and remove labeled fixture containers, then seek the independent clean Linux run. Do not modify a global environment or claim absent installed packages from the local target. Commit the scoped repair for review with these limitations explicit; issue60 remains open until real-service and fresh resolution evidence is obtained.

The repeated Windows install also timed out; stop repeating unchanged setup failures. The reviewed branch headeae7f8f passed actual Linux foundation37536532072 and advisory37536532081. Every step succeeded, including owned cleanup. Downloaded artifacts with expected head, safe filename lists and hashes verified:18 legacy HTTP tests passed, real bearer old/new/negative claims and cold/warm printed anchors passed, worker delivery passed. Fresh55-package resolution removes JOSE/ECDSA; PyJWT2.15.1 has no recorded findings. Remaining3 affected packages/28 records/14 unique IDs stay mapped to61/62. Preserve the sanitized exact reports separately from the initial historical baseline.

The serial2,000-token decode experiment after200 warmups recorded p50/p95/p99 of45.505/57.257/71.323us with zero errors. This measures ordinary helper cost on one Linux runner, not HTTP throughput, large tokens, saturation or an approved capacity budget. Reports carry the merge-checkout source1b75eaea and exact requirement/security hashes; link the PR branch headeae7f8f separately so readers can reproduce the identity distinction. The dependency change has no data/schema/index/cache work to explain-plan; full load and policy gaps remain parent work.

Final documentation headcf33361991ffcf23400634060813d51e5668ae81 passed foundation37538150154/job112524279883 and advisory37538150166/job112524279751. Reviewed/merged PR63 with that head guard as43efdc66d1d2aefbf98fd1e259cc53548b6eac77; GitHub closed60. Fetched main contains the implementation. Local cleanup initially timed out removing its labeled Redis container; guarded retry completed, and final inspection confirms both owned containers absent. All76 original source/config/readme/ignore hashes still match; the original index is untouched. Keep parent3/43/45, remaining dependencies61/62 and all milestone gates open.
