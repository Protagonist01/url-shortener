"""A fresh worker must recognize every task its scheduler publishes."""
import json
import os
from pathlib import Path
import subprocess
import sys


def test_scheduled_tasks_are_registered_at_worker_startup():
    # No imports in this pytest process may accidentally register a task first.
    env = dict(os.environ)
    env.update({
        "APP_ENV": "test",
        "SECRET_KEY": "registration-test-only",
        "DATABASE_URL": "postgresql://test:test@127.0.0.1:9/test",
        "REDIS_URL": "redis://127.0.0.1:9/0",
        "CELERY_BROKER_URL": "redis://127.0.0.1:9/1",
        "CELERY_RESULT_BACKEND": "redis://127.0.0.1:9/2",
    })
    code = """
import json
from app.worker.celery_app import celery_app
celery_app.loader.init_worker()
names = [entry['task'] for entry in celery_app.conf.beat_schedule.values()]
print(json.dumps({'scheduled': names,
                  'missing': [name for name in names if name not in celery_app.tasks]}))
"""
    result = subprocess.run(
        [sys.executable, "-c", code],
        cwd=Path(__file__).resolve().parents[1], env=env,
        capture_output=True, text=True, check=True, timeout=20,
    )
    report = json.loads(result.stdout)
    assert report["scheduled"], "The test must exercise a real periodic task"
    assert report["missing"] == [], f"Worker cannot consume scheduled tasks: {report['missing']}"
