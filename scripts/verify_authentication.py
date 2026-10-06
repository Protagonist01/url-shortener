"""JWT repair regressions against the guarded disposable foundation services.

Run worker-registration up/verify first, then this helper, then guarded down.
The historical fixture interpreter is mandatory via LEGACY_JWT_PYTHON.
"""
from configparser import ConfigParser
from datetime import datetime, timezone
from importlib.metadata import version
import hashlib
import json
import os
from pathlib import Path
import platform
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

from scripts.verify_worker_registration import environment, require_services
from scripts.audit_dependencies import stop_owned_process

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "authentication-verification"
BASE = "http://127.0.0.1:28000"
KEY = "synthetic-jwt-compatibility-only-key-20261006"


def fixture_environment():
    env = environment()
    env.update(SECRET_KEY=KEY, CLICK_TRACKING_BACKEND="background_tasks")
    return env


def initialize_settings():
    os.environ.update(fixture_environment())
    # The caller/descendants are in an empty cwd before settings first import.
    from app.core.config import settings
    if settings.SECRET_KEY != KEY or settings.REDIS_URL != fixture_environment()["REDIS_URL"]:
        raise RuntimeError("Refusing non-synthetic settings")


def serve(identity):
    require_services()
    initialize_settings()
    from app.services import geoip_service
    async def synthetic_country(ip):
        return "ZZ" if ip else None
    geoip_service.lookup_country_async = synthetic_country
    # Legacy static paths are relative; settings already loaded without dotenv.
    os.chdir(ROOT)
    from app.main import app
    @app.middleware("http")
    async def fixture_identity(request, call_next):
        response = await call_next(request)
        response.headers["X-QR-Auth-Fixture"] = identity
        return response
    import uvicorn
    uvicorn.run(app, host="127.0.0.1", port=28000, log_level="warning", access_log=False)


def historical(operation, **values):
    interpreter = os.environ.get("LEGACY_JWT_PYTHON")
    if not interpreter:
        raise RuntimeError("LEGACY_JWT_PYTHON must identify the isolated historical fixture")
    env = dict(os.environ)
    env.pop("PYTHONPATH", None)
    result = subprocess.run([interpreter, str(ROOT / "tests/legacy_jwt_fixture.py")],
                            input=json.dumps({"operation": operation, "key": KEY, **values}),
                            capture_output=True, text=True, env=env, cwd=Path.cwd(), timeout=15)
    if result.returncode:
        raise RuntimeError("Historical protocol failed; key/token output is not logged")
    return json.loads(result.stdout)


def run():
    import httpx
    import pytest
    require_services()
    initialize_settings()
    with socket.socket() as port_check:
        port_check.bind(("127.0.0.1", 28000))
    config = ConfigParser()
    config.read(ROOT / "alembic.ini")
    config.set("alembic", "script_location", str(ROOT / "alembic"))
    config.set("alembic", "prepend_sys_path", str(ROOT))
    config_path = Path.cwd() / "alembic-check.ini"
    with config_path.open("w") as output:
        config.write(output)
    with (OUTPUT / "migrations.log").open("w") as log:
        subprocess.run([sys.executable, "-m", "alembic", "-c", str(config_path), "upgrade", "head"],
                       stdout=log, stderr=log, env=fixture_environment(), check=True, timeout=45)
    identity = uuid4().hex
    process = None
    with (OUTPUT / "api.log").open("w") as log:
        try:
            process = subprocess.Popen([sys.executable, "-m", "scripts.verify_authentication", "serve", identity],
                                       env=fixture_environment(), cwd=Path.cwd(), stdout=log, stderr=log,
                                       creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0)
            deadline = time.monotonic() + 30
            while True:
                if process.poll() is not None:
                    raise RuntimeError("Owned API exited; inspect ignored api.log")
                try:
                    health = httpx.get(BASE + "/health", timeout=1)
                    if health.status_code == 200 and health.headers.get("X-QR-Auth-Fixture") == identity:
                        break
                except httpx.HTTPError:
                    pass
                if time.monotonic() > deadline:
                    raise RuntimeError("Owned API readiness timed out")
                time.sleep(0.1)
            class FixtureEndpoint:
                collected = 0
                def pytest_collection_modifyitems(self, items):
                    self.collected = len(items)
                    for item in items:
                        if item.module.__name__.endswith("test_api"):
                            item.module.BASE = BASE
            # This suite has broad cleanup. Guard exact owned services and API first.
            require_services()
            endpoint = FixtureEndpoint()
            test_status = pytest.main([str(ROOT / "tests/test_api.py"), "-c", str(ROOT / "pytest.ini"),
                                       "-q", "--junitxml=" + str(OUTPUT / "api.xml")],
                                      plugins=[endpoint])
            if test_status:
                raise RuntimeError("Existing isolated HTTP API regression suite failed")
            from app.core.security import create_access_token, decode_access_token, jwt
            with httpx.Client(base_url=BASE, timeout=10, follow_redirects=False) as client:
                # Redis cleanup is confined to the separately labeled disposable DB.
                import redis
                rc = redis.from_url(fixture_environment()["REDIS_URL"], socket_timeout=3)
                for key in rc.scan_iter(match="rate_limit:*"):
                    rc.delete(key)
                rc.close()
                email = "jwt-" + uuid4().hex + "@example.com"
                registered = client.post("/api/auth/register", json={"email": email, "password": "synthetic-jwt-password"})
                if registered.status_code != 201:
                    raise RuntimeError("Synthetic account registration failed")
                expiry = int(time.time()) + 3600
                old_token = historical("encode", claims={"sub": email, "exp": expiry})
                current = create_access_token(email)
                if historical("decode", token=current).get("sub") != email:
                    raise RuntimeError("New token failed the historical verifier")
                target = "https://example.com/printed-compatibility?x=1#retained-anchor"
                created = client.post("/api/urls", json={"original_url": target},
                                      headers={"Authorization": "Bearer " + old_token})
                if created.status_code != 201:
                    raise RuntimeError("Legacy token failed authenticated creation")
                code = created.json()["short_code"]
                for token in (old_token, current):
                    listed = client.get("/api/urls", headers={"Authorization": "Bearer " + token})
                    if listed.status_code != 200 or not any(row["short_code"] == code for row in listed.json()):
                        raise RuntimeError("Existing-token management interoperability failed")
                for claims in ({"sub": 1, "exp": expiry}, {"sub": email, "exp": None},
                               {"sub": email, "exp": "invalid"}, {"sub": email, "exp": 1}):
                    token = jwt.encode(claims, KEY, algorithm="HS256")
                    invalid = client.get("/api/urls", headers={"Authorization": "Bearer " + token})
                    if invalid.status_code != 200 or invalid.json() != []:
                        raise RuntimeError("Malformed claim did not fail safely as optional anonymous auth")
                # Cold and warm printed links must retain the complete destination.
                rc = redis.from_url(fixture_environment()["REDIS_URL"], socket_timeout=3)
                rc.delete("url:" + code)
                rc.close()
                for _ in range(2):
                    redirected = client.get("/" + code)
                    if redirected.status_code != 302 or redirected.headers.get("location") != target:
                        raise RuntimeError("Cold/warm printed destination or fragment changed")
                forbidden = client.delete("/api/urls/" + str(created.json()["id"]))
                if forbidden.status_code != 403:
                    raise RuntimeError("Owned deletion must reject anonymous access")
                deleted = client.delete("/api/urls/" + str(created.json()["id"]),
                                        headers={"Authorization": "Bearer " + current})
                if deleted.status_code != 204:
                    raise RuntimeError("Current-token authenticated deletion failed")
                # Small synthetic decode experiment; not HTTP/load/capacity evidence.
                for _ in range(200):
                    decode_access_token(current)
                timings = []
                errors = 0
                started = time.perf_counter()
                for _ in range(2000):
                    tick = time.perf_counter_ns()
                    if decode_access_token(current) != email:
                        errors += 1
                    timings.append((time.perf_counter_ns() - tick) / 1000)
                duration = time.perf_counter() - started
                timings.sort()
                def percentile(fraction):
                    return timings[min(len(timings) - 1, int((len(timings) - 1) * fraction))]
                report = {
                    "result": "passed", "recorded_at": datetime.now(timezone.utc).isoformat(),
                    "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                    "security_sha256": hashlib.sha256((ROOT / "app/core/security.py").read_bytes()).hexdigest(),
                    "requirements_sha256": hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest(),
                    "python": platform.python_version(), "platform": platform.platform(),
                    "cpu": platform.processor(), "pyjwt": version("PyJWT"),
                    "legacy_api_tests": endpoint.collected, "api_processes": 1, "tracking_profile": "background_tasks with synthetic GeoIP ZZ",
                    "legacy_current_hs256_interoperability": True, "cold_warm_destination_fragment": True,
                    "malformed_claims_safe": True, "token_decode_microseconds": {
                        "warmup": 200, "count": len(timings), "p50": percentile(.50),
                        "p95": percentile(.95), "p99": percentile(.99), "errors": errors,
                        "serial_operations_per_second": len(timings) / duration},
                    "limits": "synthetic serial decode, not load/device/capacity/SLO proof; no DB/query changes; real worker check is separate; unpublished /q prototype excluded",
                }
                if errors:
                    raise RuntimeError("Decode experiment had errors")
                (OUTPUT / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
                (OUTPUT / "decode-microseconds.json").write_text(json.dumps(timings) + "\n")
                print(json.dumps(report, indent=2))
        finally:
            if process is not None:
                stop_owned_process(process)


if __name__ == "__main__":
    OUTPUT.mkdir(parents=True, exist_ok=True)
    previous = Path.cwd()
    with TemporaryDirectory(prefix="run-", dir=OUTPUT) as directory:
        try:
            os.chdir(directory)
            if sys.argv[1:] == ["run"]:
                run()
            elif len(sys.argv) == 3 and sys.argv[1] == "serve":
                serve(sys.argv[2])
            else:
                raise RuntimeError("Use run, or the harness-owned serve mode")
        finally:
            os.chdir(previous)
