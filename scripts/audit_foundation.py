"""Reproducible foundation evidence; always uses synthetic local audit settings.

python -m scripts.audit_foundation snapshot
python -m scripts.audit_foundation offline
python -m scripts.audit_foundation serve
python -m scripts.audit_foundation api-tests
python -m scripts.audit_foundation live

Service commands require disposable PostgreSQL/Redis on 15432/16379.
GeoIP is stubbed to ZZ in the audit server; no provider reliability is claimed.
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import json
import os
import platform
import subprocess
import sys
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock, patch

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "foundation-audit"

def require_disposable_services():
    """Refuse to use an arbitrary process listening on an audit service port."""
    for suffix, service_port, host_port in (("db", "5432/tcp", "15432"),
                                           ("redis", "6379/tcp", "16379")):
        raw = subprocess.check_output(
            ["docker", "inspect", "qr-foundation-audit-20261003-" + suffix],
            text=True,
        )
        container = json.loads(raw)[0]
        bindings = container["NetworkSettings"]["Ports"].get(service_port) or []
        if (container["Config"].get("Labels", {}).get("qr.foundation.audit") != "20261003"
                or not container["State"]["Running"]
                or bindings != [{"HostIp": "127.0.0.1", "HostPort": host_port}]):
            raise RuntimeError("Audit requires the labeled disposable local service: " + suffix)

def audit_environment():
    # Override every credential-bearing setting before importing the application.
    os.environ.update({
        "APP_ENV": "test",
        "SECRET_KEY": "audit-only-not-a-production-key-20261003",
        "DATABASE_URL": "postgresql+asyncpg://audit:audit@127.0.0.1:15432/qr_audit",
        "REDIS_URL": "redis://127.0.0.1:16379/0",
        "CELERY_BROKER_URL": "redis://127.0.0.1:16379/1",
        "CELERY_RESULT_BACKEND": "redis://127.0.0.1:16379/2",
        "SHORT_URL_BASE": "http://127.0.0.1:18000",
        "CLICK_TRACKING_BACKEND": "background_tasks",
    })

def save(name, data):
    OUTPUT.mkdir(parents=True, exist_ok=True)
    (OUTPUT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(data, indent=2))

def source_snapshot():
    paths = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard"],
        cwd=ROOT, text=True,
    ).splitlines()
    # Never read secret configuration or include its values in an artifact.
    selected = [
        p for p in paths if p.startswith(("app/", "tests/", "alembic/"))
        or p in ("requirements.txt", "Dockerfile", "docker-compose.yml",
                 "render.yaml", "start.sh", "README.md", ".gitignore")
    ]
    return {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest()
            for p in selected if (ROOT / p).is_file()}

def snapshot():
    versions = {}
    for name in ("fastapi", "SQLAlchemy", "redis", "celery", "bcrypt",
                 "Pillow", "numpy", "zxing-cpp", "opencv-python-headless", "pytest"):
        try:
            versions[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            versions[name] = "not installed"
    data = {
        "python": platform.python_version(), "platform": platform.platform(),
        "head": subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip(),
        "working_tree": subprocess.check_output(["git", "status", "--short"], text=True),
        "dependencies": versions, "source_sha256": source_snapshot(),
        "dotenv_tracked": bool(subprocess.check_output(
            ["git", "ls-files", ".env"], text=True).strip()),
    }
    save("snapshot.json", data)

async def offline():
    from fastapi import BackgroundTasks
    from redis.exceptions import ConnectionError as RedisConnectionError
    from starlette.requests import Request
    from app.api import redirect, urls
    from app.core import security
    from app.services import url_service
    from app.worker.celery_app import celery_app, record_click

    findings = []
    db = AsyncMock()
    with patch.object(url_service, "_cache_get", AsyncMock(
            side_effect=RedisConnectionError("synthetic audit outage"))):
        try:
            await url_service.resolve_short_url(db, "auditcode")
            result = "returned normally"
        except RedisConnectionError:
            result = "Redis error propagated"
        findings.append({"case": "redis_outage", "observed": result,
                         "database_fallback_calls": db.execute.await_count})

    with patch.object(url_service, "get_url_by_id", AsyncMock(
            return_value=SimpleNamespace(owner_id=None))), patch.object(
            url_service, "delete_short_url", AsyncMock(return_value=True)) as deletion:
        await urls.delete_url(7, db, None)
        findings.append({"case": "anonymous_delete", "allowed": deletion.await_count == 1})

    request = Request({"type": "http", "method": "GET", "path": "/auditcode",
                       "headers": [(b"x-forwarded-for", b"192.0.2.123")],
                       "client": ("127.0.0.1", 1)})
    findings.append({"case": "proxy_header", "observed_ip": redirect._client_ip(request),
                     "peer": "127.0.0.1", "trust_configuration_present": False})

    with patch.object(redirect.url_service, "resolve_short_url", AsyncMock(
            return_value={"id": 7, "short_code": "auditcode",
                          "original_url": "https://example.com/audit"})), patch(
            "app.core.config.settings.CLICK_TRACKING_BACKEND", "celery"), patch.object(
            record_click, "delay", Mock(side_effect=RuntimeError("synthetic enqueue failure"))):
        try:
            response = await redirect.redirect("auditcode", request, db, None, BackgroundTasks(), None)
            result = response.status_code
        except RuntimeError:
            result = "enqueue exception propagated before 302"
        findings.append({"case": "broker_enqueue_failure", "observed": result})

    findings.append({"case": "scheduled_rollup_registration",
                     "registered_on_worker_module_import": "aggregate_daily_stats" in celery_app.tasks,
                     "schedule_names_task": celery_app.conf.beat_schedule[
                         "aggregate-daily-stats"]["task"]})

    long_password = "a" * 72 + "x"
    hashed = security.hash_password(long_password)
    findings.append({"case": "bcrypt_72_byte_boundary",
                     "different_suffix_authenticates": security.verify_password(
                         "a" * 72 + "y", hashed)})

    # Exercise the real optional-auth dependency on a cached redirect.
    from fastapi import FastAPI
    from fastapi.testclient import TestClient
    from app.api import deps
    from app.core.database import get_db
    cached_app = FastAPI()
    cached_app.include_router(redirect.router)
    async def fake_db():
        yield db
    cached_app.dependency_overrides[get_db] = fake_db
    for dependency in cached_app.routes[-1].dependant.dependencies:
        if dependency.name == "_":
            cached_app.dependency_overrides[dependency.call] = lambda: None
    with patch.object(deps, "get_user_by_email", AsyncMock(
            return_value=SimpleNamespace(id=1))) as user_query, patch.object(
            redirect.url_service, "resolve_short_url", AsyncMock(
                return_value={"id": 7, "short_code": "auditcode",
                              "original_url": "https://example.com/audit"})), patch.object(
            redirect, "track_click", Mock()):
        token = security.create_access_token("audit@example.com")
        response = TestClient(cached_app).get("/auditcode", follow_redirects=False,
                                              headers={"Authorization": "Bearer " + token})
        findings.append({"case": "authenticated_cache_hit_dependency",
                         "status": response.status_code,
                         "user_lookup_calls": user_query.await_count,
                         "mode": "controlled dependency probe, not a latency benchmark"})
    save("offline-probes.json", findings)

def serve():
    # Provider behavior is intentionally outside this reproducible local audit.
    from app.services import geoip_service
    async def local_country(ip):
        return "ZZ" if ip else None
    geoip_service.lookup_country_async = local_country
    from app.main import app
    @app.middleware("http")
    async def audit_identity(request, call_next):
        response = await call_next(request)
        response.headers["X-QR-Foundation-Audit"] = "20261003"
        return response
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=18000, log_level="warning")

def api_tests():
    import time
    import httpx
    import pytest
    deadline = time.monotonic() + 60
    while True:
        try:
            health = httpx.get("http://127.0.0.1:18000/health", timeout=1)
            if health.status_code == 200 and health.headers.get("X-QR-Foundation-Audit") == "20261003":
                break
        except httpx.HTTPError:
            pass
        if time.monotonic() >= deadline:
            raise RuntimeError("Audit server did not become ready within 60 seconds")
        time.sleep(0.2)
    class AuditEndpoint:
        def pytest_collection_modifyitems(self, items):
            for item in items:
                if item.module.__name__.endswith("test_api"):
                    item.module.BASE = "http://127.0.0.1:18000"
    return pytest.main(["tests/test_api.py", "-q",
                        "--junitxml=output/foundation-audit/api.xml"],
                       plugins=[AuditEndpoint()])

async def live():
    import httpx
    from uuid import uuid4
    from sqlalchemy import select
    from app.core.database import SessionLocal, engine
    from app.models.models import QRDestination, ShortURL
    findings = []
    async with httpx.AsyncClient(base_url="http://127.0.0.1:18000", timeout=10) as client:
        health = await client.get("/health")
        if health.headers.get("X-QR-Foundation-Audit") != "20261003":
            raise RuntimeError("Refusing probes against a server without audit identity")
        email = "audit-" + uuid4().hex + "@example.com"
        register = await client.post("/api/auth/register",
                                     json={"email": email, "password": "audit-password-2026"})
        login = await client.post("/api/auth/login",
                                  json={"email": email, "password": "audit-password-2026"})
        if register.status_code != 201 or login.status_code != 200:
            raise RuntimeError("Synthetic audit account setup failed")
        auth = {"Authorization": "Bearer " + login.json()["access_token"]}
        created = await client.post("/api/urls", headers=auth,
                                    json={"original_url": "https://example.com/audit#retained"})
        if created.status_code != 201:
            raise RuntimeError("Synthetic audit URL setup failed")
        owned = created.json()
        analytics = await client.get("/api/analytics/" + owned["short_code"])
        findings.append({"case": "anonymous_owned_analytics", "status": analytics.status_code})
        invalid_range = await client.get("/api/analytics/" + owned["short_code"],
                                          params={"days": 1000000000})
        findings.append({"case": "unbounded_analytics_days", "status": invalid_range.status_code})
        anonymous = (await client.post("/api/urls",
                                        json={"original_url": "https://example.com/anonymous"})).json()
        deleted = await client.delete("/api/urls/" + str(anonymous["id"]))
        findings.append({"case": "anonymous_delete_real_services", "status": deleted.status_code})
        code = uuid4().hex[:16]
        async with SessionLocal() as session:
            session.add(QRDestination(code=code, fingerprint=uuid4().hex.ljust(64, "0"),
                                       payload_url="http://127.0.0.1:18000/" + owned["short_code"] + "#kept",
                                       short_url_id=owned["id"]))
            await session.commit()
        qr = await client.get("/q/" + code, follow_redirects=False)
        findings.append({"case": "owned_qr_fragment", "status": qr.status_code,
                         "location": qr.headers.get("location")})
        # Model revision directly in the isolated database; no production data.
        async with SessionLocal() as session:
            row = (await session.execute(select(ShortURL).where(
                ShortURL.id == owned["id"]))).scalar_one()
            row.is_active = False
            await session.commit()
        stale = await client.get("/" + owned["short_code"], follow_redirects=False)
        revoked_qr = await client.get("/q/" + code, follow_redirects=False)
        findings.append({"case": "direct_db_deactivation_cache_consistency",
                         "short_link_status": stale.status_code,
                         "qr_status": revoked_qr.status_code,
                         "note": "Direct DB change: demonstrates TTL/invalidation policy gap, not API delete behavior."})
    await engine.dispose()
    save("live-probes.json", findings)

def compare():
    before = json.loads((OUTPUT / "snapshot.json").read_text(encoding="utf-8"))["source_sha256"]
    after = source_snapshot()
    changed = [p for p, digest in before.items() if after.get(p) != digest]
    save("source-preservation.json", {"preexisting_files_changed": changed,
                                    "checked_files": len(before)})
    return 1 if changed else 0

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=["snapshot", "offline", "serve", "api-tests", "live", "compare", "migrate", "focused"])
    mode = parser.parse_args().mode
    audit_environment()
    if mode in {"serve", "api-tests", "live", "migrate"}:
        require_disposable_services()
    if mode == "snapshot":
        snapshot()
    elif mode == "offline":
        asyncio.run(offline())
    elif mode == "serve":
        serve()
    elif mode == "api-tests":
        sys.exit(api_tests())
    elif mode == "live":
        asyncio.run(live())
    elif mode == "migrate":
        sys.exit(subprocess.call([sys.executable, "-m", "alembic", "upgrade", "head"], cwd=ROOT))
    elif mode == "focused":
        import pytest
        sys.exit(pytest.main([
            "tests/test_qart.py", "tests/test_qr.py", "tests/test_qr_api.py",
            "tests/test_qr_review.py", "tests/test_qr_destination.py",
            "tests/test_redirect_alias.py", "tests/test_url_service.py", "-q",
            "--junitxml=output/foundation-audit/focused.xml",
        ]))
    else:
        sys.exit(compare())
