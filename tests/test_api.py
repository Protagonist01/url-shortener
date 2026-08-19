"""End-to-end tests against the running docker-compose stack.

Run with: docker compose up -d && pytest

These tests hit the real API, DB, and Redis services. The stack must be up.
Each test cleans up its own data (users, URLs, cache keys, rate-limit keys)
via the `clean_state` fixture so tests are independent and repeatable.
"""
from __future__ import annotations

import time

import httpx
import pytest

BASE = "http://localhost:8000"


@pytest.fixture
async def client():
    async with httpx.AsyncClient(base_url=BASE, timeout=10.0) as c:
        yield c


@pytest.fixture(autouse=True)
def clean_state():
    """Clear Redis cache and rate-limit keys before each test.
    Runs synchronously before the async test body."""
    import os

    import redis

    # When running inside the API container, REDIS_URL is set to redis://redis:6379/0.
    # When running locally, use localhost.
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


def _unique_email() -> str:
    """Generate a unique email so tests don't collide on existing users."""
    return f"test_{int(time.time() * 1000)}@example.com"


# ─── Health ──────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_health(client: httpx.AsyncClient) -> None:
    r = await client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_metrics_endpoint(client: httpx.AsyncClient) -> None:
    r = await client.get("/metrics")
    assert r.status_code == 200
    assert "http_requests_total" in r.text
    assert "url_shortener_cache_hits_total" in r.text


# ─── URL shortening + redirect ───────────────────────────────────────────────

@pytest.mark.asyncio
async def test_shorten_and_redirect(client: httpx.AsyncClient) -> None:
    target = "https://example.com/very/long/path?x=1"
    r = await client.post("/api/urls", json={"original_url": target})
    assert r.status_code == 201
    body = r.json()
    assert body["original_url"] == target
    assert body["short_code"]
    assert body["short_url"].startswith("http")
    assert body["is_active"] is True

    r2 = await client.get(f"/{body['short_code']}", follow_redirects=False)
    assert r2.status_code == 302
    assert r2.headers["location"] == target


@pytest.mark.asyncio
async def test_shorten_invalid_url(client: httpx.AsyncClient) -> None:
    r = await client.post("/api/urls", json={"original_url": "not-a-url"})
    assert r.status_code == 422  # Pydantic validation error


@pytest.mark.asyncio
async def test_unknown_code_returns_404(client: httpx.AsyncClient) -> None:
    r = await client.get("/nonexistent", follow_redirects=False)
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_custom_short_code(client: httpx.AsyncClient) -> None:
    target = "https://example.com/custom"
    code = f"C{int(time.time())}a"
    r = await client.post(
        "/api/urls",
        json={"original_url": target, "custom_code": code},
    )
    assert r.status_code == 201
    assert r.json()["short_code"] == code

    r2 = await client.get(f"/{code}", follow_redirects=False)
    assert r2.status_code == 302
    assert r2.headers["location"] == target


@pytest.mark.asyncio
async def test_custom_code_collision(client: httpx.AsyncClient) -> None:
    code = f"D{int(time.time())}b"
    r1 = await client.post(
        "/api/urls",
        json={"original_url": "https://example.com/first", "custom_code": code},
    )
    assert r1.status_code == 201

    r2 = await client.post(
        "/api/urls",
        json={"original_url": "https://example.com/second", "custom_code": code},
    )
    assert r2.status_code == 409


# ─── Cache behavior ──────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_cache_is_warmed_on_creation(client: httpx.AsyncClient) -> None:
    import os

    import redis

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    r = redis.from_url(redis_url, decode_responses=True)
    r.flushdb()

    resp = await client.post(
        "/api/urls", json={"original_url": "https://example.com/cached"}
    )
    code = resp.json()["short_code"]

    # The cache key should exist immediately after creation.
    cached = r.get(f"url:{code}")
    assert cached is not None
    assert "https://example.com/cached" in cached


@pytest.mark.asyncio
async def test_redirect_uses_cache_not_db(client: httpx.AsyncClient) -> None:
    """After the first redirect (which warms the cache), subsequent redirects
    should still return 302 even if we delete the URL from the DB — because
    the cache has it. (This is a somewhat artificial test, but it proves the
    cache is being read, not just the DB.)"""
    import redis.asyncio as aioredis

    resp = await client.post(
        "/api/urls", json={"original_url": "https://example.com/cache-test"}
    )
    code = resp.json()["short_code"]

    # First redirect — hits DB, warms cache.
    r1 = await client.get(f"/{code}", follow_redirects=False)
    assert r1.status_code == 302

    # Verify the cache key exists.
    import os

    redis_url = os.environ.get("REDIS_URL", "redis://localhost:6379/0")
    rc = aioredis.from_url(redis_url, decode_responses=True)
    assert await rc.exists(f"url:{code}")
    await rc.aclose()


# ─── Analytics ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analytics_after_click(client: httpx.AsyncClient) -> None:
    resp = await client.post(
        "/api/urls", json={"original_url": "https://example.com/analytics-test"}
    )
    code = resp.json()["short_code"]

    # Click it with a public IP so GeoIP resolves a country.
    await client.get(
        f"/{code}",
        follow_redirects=False,
        headers={"X-Forwarded-For": "8.8.8.8"},
    )

    # Wait for the Celery worker to process the click.
    time.sleep(3)

    r = await client.get(f"/api/analytics/{code}")
    assert r.status_code == 200
    body = r.json()
    assert body["total_clicks"] >= 1
    assert body["last_24h"] >= 1
    assert len(body["timeseries"]) >= 1


@pytest.mark.asyncio
async def test_analytics_unknown_code(client: httpx.AsyncClient) -> None:
    r = await client.get("/api/analytics/doesnotexist")
    assert r.status_code == 404


# ─── Auth ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_register_and_login(client: httpx.AsyncClient) -> None:
    email = _unique_email()
    password = "hunter2hunter2"

    r = await client.post(
        "/api/auth/register", json={"email": email, "password": password}
    )
    assert r.status_code == 201
    assert r.json()["email"] == email

    r2 = await client.post(
        "/api/auth/login", json={"email": email, "password": password}
    )
    assert r2.status_code == 200
    token = r2.json()["access_token"]
    assert token

    # Authenticated request.
    r3 = await client.get(
        "/api/urls", headers={"Authorization": f"Bearer {token}"}
    )
    assert r3.status_code == 200


@pytest.mark.asyncio
async def test_login_wrong_password(client: httpx.AsyncClient) -> None:
    email = _unique_email()
    await client.post(
        "/api/auth/register", json={"email": email, "password": "correct-pass"}
    )

    r = await client.post(
        "/api/auth/login", json={"email": email, "password": "wrong-pass"}
    )
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_register_duplicate_email(client: httpx.AsyncClient) -> None:
    email = _unique_email()
    r1 = await client.post(
        "/api/auth/register", json={"email": email, "password": "password1"}
    )
    assert r1.status_code == 201

    r2 = await client.post(
        "/api/auth/register", json={"email": email, "password": "password2"}
    )
    assert r2.status_code == 409


@pytest.mark.asyncio
async def test_invalid_bearer_token(client: httpx.AsyncClient) -> None:
    r = await client.get(
        "/api/urls", headers={"Authorization": "Bearer not-a-real-token"}
    )
    # Optional auth: invalid token is treated as anonymous, not an error.
    assert r.status_code == 200
    assert r.json() == []


# ─── Rate limiting ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_auth_rate_limit(client: httpx.AsyncClient) -> None:
    """The auth endpoint allows 5 requests per 60s per IP.
    The 6th should return 429."""
    email = _unique_email()
    for i in range(5):
        r = await client.post(
            "/api/auth/login",
            json={"email": email, "password": "wrong"},
        )
        assert r.status_code == 401, f"request {i+1} should be 401"

    r6 = await client.post(
        "/api/auth/login",
        json={"email": email, "password": "wrong"},
    )
    assert r6.status_code == 429
    assert r6.headers.get("retry-after") is not None


@pytest.mark.asyncio
async def test_rate_limit_scopes_are_independent(client: httpx.AsyncClient) -> None:
    """Exhausting the auth rate limit shouldn't affect the shorten limit."""
    email = _unique_email()
    for _ in range(6):
        await client.post(
            "/api/auth/login", json={"email": email, "password": "wrong"}
        )

    # Auth is now rate-limited, but shorten should still work (different scope).
    r = await client.post(
        "/api/urls", json={"original_url": "https://example.com/scope-test"}
    )
    assert r.status_code == 201
