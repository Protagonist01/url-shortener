"""Framework contracts and bounded mixed workload inside the owned API fixture.

No production route or policy is added. Called only by verify_authentication.
"""
import asyncio
from datetime import datetime, timezone
import hashlib
from importlib.metadata import version
import json
from pathlib import Path
import platform
import subprocess
import time

from scripts.verify_worker_registration import require_services

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/framework-dependency"


def install_fixture_routes(app):
    from fastapi import Request
    from starlette.datastructures import UploadFile
    observer = {"task": None, "lags": [], "running": False}

    async def observe():
        while observer["running"]:
            tick = time.perf_counter()
            await asyncio.sleep(.01)
            observer["lags"].append(max(0, (time.perf_counter() - tick - .01) * 1000))

    @app.post("/_verification/form", include_in_schema=False)
    async def fixture_form(request: Request):
        # Test-only limits, not an approved product upload quota.
        async with request.form(max_fields=8, max_files=1, max_part_size=256) as parsed:
            files = [v for v in parsed.values() if isinstance(v, UploadFile)]
            return {"fields": len(parsed), "file_sizes": [f.size for f in files]}

    @app.post("/_verification/observer/start", include_in_schema=False)
    async def begin():
        if observer["running"]:
            raise RuntimeError("Observer already running")
        observer.update(lags=[], running=True)
        observer["task"] = asyncio.create_task(observe())
        return {"started": True}

    @app.post("/_verification/observer/stop", include_in_schema=False)
    async def end():
        observer["running"] = False
        await observer["task"]
        return {"lag_ms": observer["lags"]}


def summary(samples):
    if not samples:
        raise RuntimeError("Measurement had no samples")
    values = sorted(samples)
    return {"count": len(values), "p50": values[int((len(values)-1)*.50)],
            "p95": values[int((len(values)-1)*.95)],
            "p99": values[int((len(values)-1)*.99)], "max": values[-1]}


async def measure(base, identity, api_process, code, target, mixed):
    import httpx
    import psutil
    process = psutil.Process(api_process.pid)
    if api_process.poll() is not None:
        raise RuntimeError("Owned API unavailable")
    timings = {"redirect_ms": [], "static_ms": [], "parser_ms": [], "file_ms": []}
    samples = []
    cpu_samples = []
    thread_samples = []
    process.cpu_percent()
    cpu_before = process.cpu_times()
    running = True
    async with httpx.AsyncClient(base_url=base, timeout=10, follow_redirects=False,
                               limits=httpx.Limits(max_connections=8)) as client:
        async def checked(method, path, expected, kind=None, **options):
            tick = time.perf_counter()
            response = await client.request(method, path, **options)
            elapsed = (time.perf_counter() - tick) * 1000
            if (response.status_code != expected or
                    response.headers.get("X-QR-Auth-Fixture") != identity):
                raise RuntimeError("Owned HTTP framework contract failed: " + path + " status=" + str(response.status_code))
            if kind:
                timings[kind].append(elapsed)
            return response

        async def resources():
            while running:
                samples.append(process.memory_info().rss)
                cpu_samples.append(process.cpu_percent())
                thread_samples.append(process.num_threads())
                await asyncio.sleep(.01)

        async def redirects():
            for _ in range(10):
                response = await checked("GET", "/" + code, 302, "redirect_ms")
                if response.headers["location"] != target:
                    raise RuntimeError("Mixed workload changed printed destination/anchor")

        async def static():
            for _ in range(12):
                await checked("GET", "/static/index.html", 206, "static_ms", headers={"Range": "bytes=0-15"})
                await checked("GET", "/", 400, "static_ms", headers={"Range": "bytes=" + "0" * 2000 + "a-"})

        async def parsers():
            for _ in range(8):
                await checked("POST", "/_verification/form", 400, "parser_ms",
                              content=b"a=1&" * 10000, headers={"Content-Type": "application/x-www-form-urlencoded"})
                await checked("POST", "/_verification/form", 400, "parser_ms",
                              content=b"a=" + b"x" * 4096, headers={"Content-Type": "application/x-www-form-urlencoded"})

        async def files():
            for _ in range(4):
                response = await checked("POST", "/_verification/form", 200, "file_ms",
                                         files={"upload": ("synthetic.bin", b"x" * (2 * 1024 * 1024))})
                if response.json()["file_sizes"] != [2 * 1024 * 1024]:
                    raise RuntimeError("Synthetic rolled file was truncated")

        await checked("POST", "/_verification/observer/start", 200)
        started = time.perf_counter()
        monitor = asyncio.create_task(resources())
        try:
            work = [redirects() for _ in range(4)]
            if mixed:
                work.extend((static(), parsers(), files()))
            await asyncio.wait_for(asyncio.gather(*work), timeout=30)
        finally:
            running = False
            await monitor
            lag = (await checked("POST", "/_verification/observer/stop", 200)).json()["lag_ms"]
        duration = time.perf_counter() - started
    cpu_after = process.cpu_times()
    cpu_seconds = (cpu_after.user + cpu_after.system) - (cpu_before.user + cpu_before.system)
    return {"profile": "mixed" if mixed else "redirect-only", "duration_seconds": duration,
            "redirects_per_second": len(timings["redirect_ms"]) / duration,
            "total_operations_per_second": sum(map(len, timings.values())) / duration,
            "errors": 0, "timeouts": 0, "latency_ms": {k: summary(v) for k,v in timings.items() if v},
            "event_loop_lag_ms": summary(lag), "rss_bytes": summary(samples),
            "cpu_one_core_percent": summary(cpu_samples), "process_threads": summary(thread_samples),
            "cpu_seconds": cpu_seconds, "average_cpu_one_core_percent": 100 * cpu_seconds / duration,
            "raw": {"latency_ms": timings, "event_loop_lag_ms": lag, "rss_bytes": samples,
                    "cpu_one_core_percent": cpu_samples, "process_threads": thread_samples}}


def verify_owned_api(base, identity, api_process, code, target):
    import httpx
    require_services()
    expected = (ROOT / "app/static/index.html").read_bytes()
    with httpx.Client(base_url=base, timeout=10, follow_redirects=False) as client:
        def checked(path, status, **options):
            response = client.get(path, **options)
            if response.status_code != status or response.headers.get("X-QR-Auth-Fixture") != identity:
                raise RuntimeError("Published file contract failed: " + path)
            return response
        for path in ("/", "/static/index.html"):
            if checked(path, 200).content != expected:
                raise RuntimeError("Static bytes changed")
            partial = checked(path, 206, headers={"Range": "bytes=0-15"})
            if partial.content != expected[:16] or partial.headers["content-range"] != "bytes 0-15/" + str(len(expected)):
                raise RuntimeError("Single range changed bytes")
            checked(path, 416, headers={"Range": "bytes=999999999-"})
            checked(path, 400, headers={"Range": "unsupported=0-1"})
            if checked(path, 200, headers={"Range": "bytes=" + ",".join(["0-0"] * 101)}).content != expected:
                raise RuntimeError("Excess ranges must fall back to full ordinary response")
        full = checked("/static/index.html", 200)
        checked("/static/index.html", 304, headers={"If-None-Match": full.headers["etag"]})
        checked("/static/%2e%2e/%2e%2e/requirements.txt", 404)
        metrics = checked("/metrics", 200).text
        if "http_requests_total" not in metrics or "url_shortener_cache_hits_total" not in metrics:
            raise RuntimeError("Prometheus metric contracts changed")
        for body, content_type in ((b"{", "application/json"), (b"a=1", "application/x-www-form-urlencoded")):
            invalid = client.post("/api/urls", content=body, headers={"Content-Type": content_type})
            if invalid.status_code != 422 or invalid.headers.get("X-QR-Auth-Fixture") != identity:
                raise RuntimeError("Malformed/non-JSON input must fail validation safely")
        missing_type = client.post("/api/urls", content=b'{"original_url":"https://example.com/synthetic"}')
        if missing_type.status_code != 422 or missing_type.headers.get("X-QR-Auth-Fixture") != identity:
            raise RuntimeError("Missing JSON content type must fail validation safely")
        normal = client.post("/_verification/form", content=b"a=1&b=two+words",
                             headers={"Content-Type": "application/x-www-form-urlencoded"})
        if normal.status_code != 200 or normal.json()["fields"] != 2:
            raise RuntimeError("Synthetic ordinary form control failed")
    # At most82 fixture redirects across both profiles, below the existing100/60s limit.
    results = [asyncio.run(measure(base, identity, api_process, code, target, mixed)) for mixed in (False, True)]
    OUTPUT.mkdir(parents=True, exist_ok=True)
    raw = [result.pop("raw") for result in results]
    (OUTPUT / "mixed-workload-raw.json").write_text(json.dumps(raw) + "\n")
    report = {"result": "passed", "recorded_at": datetime.now(timezone.utc).isoformat(),
              "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
              "requirements_sha256": hashlib.sha256((ROOT / "requirements.txt").read_bytes()).hexdigest(),
              "python": platform.python_version(), "platform": platform.platform(),
              "packages": {n: version(n) for n in ("fastapi", "starlette", "python-multipart", "prometheus-fastapi-instrumentator")},
              "profile": "One owned loopback API, actual disposable PostgreSQL/Redis; synthetic GeoIP; BackgroundTasks tracking;4 redirect lanes;8 HTTP connections;10ms resource/loop sampling",
              "static_sha256": hashlib.sha256(expected).hexdigest(), "measurements": results,
              "limits": "Small bounded compatibility experiment, not saturation/soak/device/SLO or zero-DB-read proof; parser route/limits are fixture-only; no published upload or /q prototype coverage; F01/F05 and parent release gates stay open"}
    (OUTPUT / "evidence.json").write_text(json.dumps(report, indent=2) + "\n")
    print(json.dumps(report, indent=2))
