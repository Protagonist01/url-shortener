"""Build the actual Dockerfile from committed files and check runtime tools."""
import io
import json
from pathlib import Path
import subprocess
import tarfile
from tempfile import TemporaryDirectory
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "output/test-dependency"
LABEL = "qr.dependency.verification"


def main():
    OUTPUT.mkdir(parents=True, exist_ok=True)
    tracked = subprocess.check_output(
        ["git", "ls-tree", "-r", "--name-only", "HEAD"], cwd=ROOT, text=True).splitlines()
    if any(Path(p).name.startswith(".env") and Path(p).name != ".env.example" for p in tracked):
        raise RuntimeError("Refusing archive with private configuration")
    identity = uuid4().hex
    image = "qr-runtime-verification:" + identity
    built = False
    commands = []
    try:
        with TemporaryDirectory(prefix="runtime-context-", dir=OUTPUT) as directory:
            context = Path(directory).resolve()
            context.relative_to(OUTPUT.resolve())
            archive = subprocess.check_output(["git", "archive", "--format=tar", "HEAD"], cwd=ROOT)
            with tarfile.open(fileobj=io.BytesIO(archive)) as files:
                files.extractall(context, filter="data")
            with (OUTPUT / "runtime-build.log").open("w") as log:
                subprocess.run(["docker", "build", "--label", LABEL + "=" + identity,
                                "--tag", image, str(context)], check=True, timeout=600,
                               stdout=log, stderr=subprocess.STDOUT)
            built = True
        metadata = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
        assert metadata["Config"]["Labels"][LABEL] == identity
        assert metadata["Config"]["Cmd"] == ["./start.sh"]
        assert metadata["Config"]["User"] == "appuser"
        env = {"APP_ENV": "test", "SECRET_KEY": "dependency-image-synthetic-only",
               "DATABASE_URL": "postgresql://qr_test:qr_test@127.0.0.1:25432/qr_worker_test",
               "REDIS_URL": "redis://127.0.0.1:26379/0",
               "CELERY_BROKER_URL": "redis://127.0.0.1:26379/1",
               "CELERY_RESULT_BACKEND": "redis://127.0.0.1:26379/2", "PYTHONPATH": "/app"}
        prefix = ["docker", "run", "--rm", "--network", "none", "--workdir", "/tmp"]
        for key, value in env.items():
            prefix += ["--env", key + "=" + value]
        prefix += ["--entrypoint", "python", image]
        probe = """
import asyncio, importlib.util, os
for name in ('pytest', 'pytest_asyncio', 'flower', 'psutil', 'pip_audit'):
    assert importlib.util.find_spec(name) is None, name
from app.core.config import settings
assert settings.APP_ENV == 'test'
os.chdir('/app')
from app.main import app
from app.worker.celery_app import celery_app
celery_app.loader.import_default_modules()
assert 'aggregate_daily_stats' in celery_app.tasks
import httpx
async def check_health():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                 base_url='http://fixture') as client:
        result = await client.get('/health')
        assert result.status_code == 200 and result.json()['status'] == 'ok'
asyncio.run(check_health())
print('Runtime API health/task discovery passed; test/monitoring/scanner tools absent')
"""
        checks = [["-m", "pip", "check"], ["-c", probe], ["-m", "alembic", "--help"],
                  ["-m", "uvicorn", "--help"],
                  ["-m", "celery", "-A", "app.worker.celery_app", "worker", "--help"],
                  ["-m", "celery", "-A", "app.worker.celery_app", "beat", "--help"]]
        with (OUTPUT / "runtime-check.log").open("w") as log:
            for command in checks:
                subprocess.run(prefix + command, check=True, timeout=45,
                               stdout=log, stderr=subprocess.STDOUT)
                commands.append("API health/imports" if command[0] == "-c" else " ".join(command))
        report = {"source_head": subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT,
                                                        text=True).strip(),
                  "result": "passed", "checks": commands, "network": "none",
                  "limitations": "Entrypoint availability and in-process health; real migrations/worker/API are separate guarded checks. No size/time improvement claim."}
        (OUTPUT / "runtime.json").write_text(json.dumps(report, indent=2) + "\n")
        print(json.dumps(report, indent=2))
    finally:
        if built:
            metadata = json.loads(subprocess.check_output(["docker", "image", "inspect", image]))[0]
            if metadata["Config"].get("Labels", {}).get(LABEL) != identity:
                raise RuntimeError("Refusing cleanup of an image without owned label")
            subprocess.run(["docker", "image", "rm", image], check=True, timeout=30)


if __name__ == "__main__":
    main()
