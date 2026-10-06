"""Real scheduled task delivery using disposable PostgreSQL/Redis only.

python -m scripts.verify_worker_registration up
python -m scripts.verify_worker_registration verify
python -m scripts.verify_worker_registration down

No production env file/credentials are needed. 'up' refuses existing names/ports;
all service operations check the exact ownership label and loopback bindings.
"""
from __future__ import annotations

import argparse
from configparser import ConfigParser
from datetime import datetime, timedelta, timezone
from importlib.metadata import version
import hashlib
import json
import os
from pathlib import Path
import socket
import subprocess
import sys
from tempfile import TemporaryDirectory
import time
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output" / "worker-registration"
LABEL = "qr.worker.registration"
IDENTITY = "20261006"
SERVICES = {
    "db": ("postgres:16-alpine", 25432, "5432/tcp"),
    "redis": ("redis:7-alpine", 26379, "6379/tcp"),
}


def environment():
    env = dict(os.environ)
    env.update({
        "APP_ENV": "test", "SECRET_KEY": "worker-registration-synthetic-only",
        "DATABASE_URL": "postgresql://qr_test:qr_test@127.0.0.1:25432/qr_worker_test",
        "REDIS_URL": "redis://127.0.0.1:26379/0",
        "CELERY_BROKER_URL": "redis://127.0.0.1:26379/1",
        "CELERY_RESULT_BACKEND": "redis://127.0.0.1:26379/2",
        "SHORT_URL_BASE": "http://127.0.0.1:28000",
        "CLICK_TRACKING_BACKEND": "celery",
        "PYTHONPATH": str(ROOT),
    })
    return env


def name(service):
    return "qr-worker-registration-" + IDENTITY + "-" + service


def inspect(service):
    result = subprocess.run(["docker", "inspect", name(service)],
                            capture_output=True, text=True, timeout=15)
    if result.returncode:
        if "no such object" in result.stderr.lower():
            return None
        raise RuntimeError("Docker inspect failed; no service state inferred")
    container = json.loads(result.stdout)[0]
    if container["Config"].get("Labels", {}).get(LABEL) != IDENTITY:
        raise RuntimeError("Refusing a container without the owned test label")
    port = SERVICES[service][1]
    bindings = container["HostConfig"]["PortBindings"].get(SERVICES[service][2])
    if bindings != [{"HostIp": "127.0.0.1", "HostPort": str(port)}]:
        raise RuntimeError("Owned test service has unexpected port bindings")
    return container


def require_services():
    for service in SERVICES:
        container = inspect(service)
        if not container or not container["State"]["Running"]:
            raise RuntimeError("Owned disposable service is not running: " + service)


def down():
    for service in SERVICES:
        if inspect(service) is not None:
            subprocess.run(["docker", "rm", "--force", name(service)],
                           check=True, timeout=20)


def up():
    subprocess.run(["docker", "version", "--format", "{{.Server.Version}}"],
                   check=True, timeout=15)
    for service, (_, port, _) in SERVICES.items():
        if inspect(service) is not None:
            raise RuntimeError("Create fresh fixtures; owned service already exists: " + service)
        with socket.socket() as port_check:
            port_check.bind(("127.0.0.1", port))
    created = []
    try:
        for service, (image, port, inner_port) in SERVICES.items():
            command = ["docker", "run", "--detach", "--name", name(service),
                       "--label", LABEL + "=" + IDENTITY,
                       "--publish", f"127.0.0.1:{port}:{inner_port.split('/')[0]}"]
            if service == "db":
                command += ["--env", "POSTGRES_USER=qr_test", "--env",
                            "POSTGRES_PASSWORD=qr_test", "--env", "POSTGRES_DB=qr_worker_test"]
            command += [image]
            subprocess.run(command, check=True, timeout=120)
            created.append(service)
        deadline = time.monotonic() + 45
        while True:
            require_services()
            ready = subprocess.run(["docker", "exec", name("db"), "pg_isready",
                                    "-U", "qr_test", "-d", "qr_worker_test"],
                                   stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=5)
            if ready.returncode == 0:
                break
            if time.monotonic() >= deadline:
                raise RuntimeError("Disposable PostgreSQL readiness timed out")
            time.sleep(0.25)
    except BaseException:
        for service in created:
            if inspect(service) is not None:
                subprocess.run(["docker", "rm", "--force", name(service)], check=True, timeout=20)
        raise


def application(queue):
    os.environ.update(environment())
    from app.worker.celery_app import celery_app
    celery_app.conf.update(task_default_queue=queue, task_publish_retry=False,
                          broker_connection_timeout=3, redis_socket_connect_timeout=3,
                          redis_socket_timeout=3)
    return celery_app


def stop_worker(process):
    import psutil
    # These are descendants of the Popen handle created by this run, not a global kill.
    if process.poll() is not None:
        return
    parent = psutil.Process(process.pid)
    children = parent.children(recursive=True)
    for child in children:
        child.terminate()
    process.terminate()
    _, remaining = psutil.wait_procs(children + [parent], timeout=5)
    for child in remaining:
        child.kill()
    process.wait(timeout=5)


def verify():
    require_services()
    OUTPUT.mkdir(parents=True, exist_ok=True)
    env = environment()
    # Descendant temporary directories stay inside this owned run directory;
    # parent cleanup also removes them after terminating the worker.
    env.update({key: str(Path.cwd()) for key in ("TMPDIR", "TEMP", "TMP")})
    os.environ.update(env)
    # Resolve migration paths explicitly while the subprocess stays in an
    # empty directory. Relative .env loading cannot reach repository secrets.
    migration_config = ConfigParser()
    migration_config.read(ROOT / "alembic.ini")
    migration_config.set("alembic", "script_location", str(ROOT / "alembic"))
    migration_config.set("alembic", "prepend_sys_path", str(ROOT))
    migration_path = Path.cwd() / "alembic-check.ini"
    with migration_path.open("w") as config_file:
        migration_config.write(config_file)
    with (OUTPUT / "migrations.log").open("w") as log:
        subprocess.run([sys.executable, "-m", "alembic", "-c", str(migration_path), "upgrade", "head"],
                       cwd=Path.cwd(), env=env, stdout=log, stderr=log, check=True, timeout=45)
    from sqlalchemy import create_engine, select
    from sqlalchemy.orm import Session
    from app.models.models import ClickEvent, DailyStats, ShortURL
    from celery.beat import Scheduler
    engine = create_engine(env["DATABASE_URL"].replace("postgresql://", "postgresql+psycopg2://"),
                           connect_args={"connect_timeout": 3}, pool_size=1, max_overflow=0)
    worker = None
    scheduler = None
    app = None
    try:
        queue = "registration-test-" + uuid4().hex
        app = application(queue)
        production_period = app.conf.beat_schedule["aggregate-daily-stats"]["schedule"]
        assert production_period == 3600, "Existing hourly schedule changed"
        with Session(engine) as session:
            urls = [ShortURL(short_code=uuid4().hex[:12], original_url="https://example.com/fixture")
                    for _ in range(2)]
            session.add_all(urls)
            session.flush()
            ids = [url.id for url in urls]
            for url_id, count in zip(ids, (3, 2)):
                session.add_all([ClickEvent(url_id=url_id, country="ZZ") for _ in range(count)])
            session.commit()
        with (OUTPUT / "worker.log").open("w") as log:
            worker = subprocess.Popen(
                [sys.executable, "-m", "scripts.verify_worker_registration", "worker", "--queue", queue],
                cwd=Path.cwd(), env=env, stdout=log, stderr=log,
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0,
            )
            deadline = time.monotonic() + 30
            while True:
                if worker.poll() is not None:
                    raise RuntimeError("Real worker exited; inspect ignored worker.log")
                reply = app.control.ping(timeout=1, destination=["registration@" + queue])
                if reply:
                    break
                if time.monotonic() >= deadline:
                    raise RuntimeError("Real worker did not become ready")
            # Also verify the already-existing click task through the actual broker/worker.
            click = app.send_task("record_click", kwargs={"url_id": ids[0], "short_code": "fixture",
                                  "ip_address": None, "user_agent": None, "referer": None})
            click.get(timeout=20)
            class ObservedScheduler(Scheduler):
                dispatched = []
                def apply_async(self, entry, producer=None, advance=True, **kwargs):
                    result = super().apply_async(entry, producer=producer, advance=advance, **kwargs)
                    self.dispatched.append((entry.task, result))
                    return result
            scheduler = ObservedScheduler(app=app, max_interval=1)
            entry = scheduler.schedule["aggregate-daily-stats"]
            entry.last_run_at = datetime.now(timezone.utc) - timedelta(seconds=3601)
            assert entry.is_due().is_due, "Experiment must publish a due periodic task"
            scheduler.tick()
            assert len(scheduler.dispatched) == 1, "One scheduler should publish exactly one due task"
            task_name, result = scheduler.dispatched[0]
            assert task_name == "aggregate_daily_stats"
            aggregate = result.get(timeout=20)
            with Session(engine) as session:
                rows = session.scalars(select(DailyStats).where(DailyStats.url_id.in_(ids))).all()
                observed = {row.url_id: (row.click_count, row.unique_ips, row.top_country) for row in rows}
                assert observed == {ids[0]: (4, 0, "ZZ"), ids[1]: (2, 0, "ZZ")}, observed
            report = {"result": "passed", "celery": version("celery"),
                      "source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip(),
                      "runtime": {"python": sys.version, "platform": sys.platform},
                      "source_sha256": {str(path.relative_to(ROOT)).replace("\\", "/"):
                                         hashlib.sha256(path.read_bytes()).hexdigest()
                                         for path in (ROOT / "app/worker/celery_app.py",
                                                      ROOT / "app/worker/beat_tasks.py",
                                                      ROOT / "app/models/models.py")},
                      "worker_pool": "solo", "worker_count": 1, "scheduler_count": 1,
                      "scheduled_messages": 1, "period_seconds_preserved": production_period,
                      "aggregate_rows": len(rows), "click_counts": [4, 2],
                      "task_result": aggregate, "geoip_network": "none; IP absent, synthetic ZZ fixtures",
                      "limitations": "correctness check, not prefork/load/retry/idempotency proof"}
            (OUTPUT / "evidence.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
            print(json.dumps(report, indent=2))
    finally:
        if scheduler is not None:
            scheduler.close()
        if worker is not None:
            stop_worker(worker)
        if app is not None:
            app.close()
        engine.dispose()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("mode", choices=("up", "verify", "down", "worker"))
    parser.add_argument("--queue")
    args = parser.parse_args()
    if args.mode == "up":
        up()
    elif args.mode == "down":
        down()
    elif args.mode == "verify":
        verify()
    else:
        require_services()
        if not args.queue or not args.queue.startswith("registration-test-"):
            raise RuntimeError("Worker mode requires this experiment's isolated queue")
        application(args.queue).worker_main([
            "worker", "--pool=solo", "--concurrency=1", "--loglevel=INFO",
            "--hostname=registration@" + args.queue, "--queues=" + args.queue,
            "--without-gossip", "--without-mingle",
        ])


if __name__ == "__main__":
    # Tests need no local dotenv file. Keep all application/migration/worker
    # imports in an empty cwd, including descendant subprocesses.
    previous_directory = Path.cwd()
    with TemporaryDirectory(prefix="qr-worker-delivery-") as directory:
        try:
            os.chdir(directory)
            main()
        finally:
            # Windows cannot remove the process's current directory.
            os.chdir(previous_directory)
