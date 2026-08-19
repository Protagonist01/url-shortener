#!/bin/sh
set -e

# Run pending migrations before starting the server.
# This runs in the web service container on every deploy.
# Alembic is idempotent — if no new migrations, it's a no-op.
echo "Running database migrations..."
alembic upgrade head

echo "Starting uvicorn..."
exec uvicorn app.main:app --host 0.0.0.0 --port "${PORT:-8000}" --workers 2
