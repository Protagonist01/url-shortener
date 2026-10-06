"""Verify Git/Docker configuration boundaries without reading real .env values."""
import argparse
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def verify_git():
    paths = subprocess.check_output(["git", "ls-files", "--cached"], cwd=ROOT, text=True).splitlines()
    private = [p for p in paths if Path(p).name.startswith(".env") and Path(p).name != ".env.example"]
    if private:
        raise RuntimeError("Private environment configuration remains tracked: " + ", ".join(private))
    assert ".env.example" in paths, "Public configuration template must be tracked"
    for path in (".env", ".env.local", ".env.production", "nested/.env"):
        result = subprocess.run(["git", "check-ignore", "--no-index", "--quiet", path], cwd=ROOT)
        assert result.returncode == 0, "Private environment file is not ignored: " + path
    result = subprocess.run(["git", "check-ignore", "--no-index", "--quiet", ".env.example"], cwd=ROOT)
    assert result.returncode == 1, "Public template should remain trackable"
    print("Git boundaries passed; no private dotenv values read", flush=True)


def verify_template():
    from dotenv import dotenv_values
    # Only the deliberately public fake template is read. Import app config
    # from an empty working directory so its relative .env cannot read ours.
    values = {key: value for key, value in dotenv_values(ROOT / ".env.example").items() if value is not None}
    env = dict(os.environ)
    env.update(values)
    env["PYTHONPATH"] = str(ROOT)
    code = """
from app.core.config import settings
assert settings.APP_ENV == 'development'
assert settings.sync_database_url.startswith('postgresql+psycopg2://')
assert settings.async_database_url.startswith('postgresql+asyncpg://')
assert settings.REDIS_URL and settings.CELERY_BROKER_URL and settings.CELERY_RESULT_BACKEND
print('Public template satisfies application configuration; no connections opened')
"""
    with TemporaryDirectory(prefix="qr-public-config-") as directory:
        subprocess.run([sys.executable, "-c", code], cwd=directory, env=env, check=True, timeout=20)


def verify_docker():
    output = ROOT / "output" / "configuration-check"
    output.mkdir(parents=True, exist_ok=True)
    with TemporaryDirectory(prefix="synthetic-", dir=output) as directory:
        temporary = Path(directory).resolve()
        temporary.relative_to(output.resolve())  # Verify cleanup target is owned.
        context = temporary / "context"
        context.mkdir()
        (context / ".dockerignore").write_bytes((ROOT / ".dockerignore").read_bytes())
        (context / "Dockerfile").write_text("FROM scratch\nCOPY . /context/\n", encoding="utf-8")
        for path in (".env", ".env.local", ".env.example", "nested/.env.production",
                     ".git/config", ".venv/test.txt", "output/test.txt"):
            destination = context / path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text("synthetic-not-a-secret\n", encoding="utf-8")
        (context / "application.txt").write_text("synthetic application fixture\n", encoding="utf-8")
        exported = temporary / "exported"
        subprocess.run(["docker", "build", "--output", "type=local,dest=" + str(exported),
                        str(context)], check=True, timeout=60)
        packaged = exported / "context"
        assert (packaged / "application.txt").exists(), "Build must actually copy allowed context"
        relative_paths = [p.relative_to(packaged) for p in packaged.rglob("*")]
        forbidden = [str(p) for p in relative_paths
                     if p.name.startswith(".env") or ".git" in p.parts or ".venv" in p.parts or "output" in p.parts]
        assert not forbidden, "Synthetic ignored files reached Docker COPY: " + ", ".join(forbidden)
        print("Docker boundaries passed using only synthetic files; no repository secrets sent to build")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docker", action="store_true", help="also run synthetic actual Docker COPY check")
    args = parser.parse_args()
    verify_git()
    verify_template()
    if args.docker:
        verify_docker()
