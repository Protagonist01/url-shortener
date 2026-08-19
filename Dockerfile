FROM python:3.12-slim AS base

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Non-root user for production security.
# The app files and start.sh must be owned by this user.
RUN useradd -m -u 1000 appuser

COPY . .
RUN chmod +x start.sh && chown -R appuser:appuser /app

USER appuser

# Production: no --reload, 2 workers, PORT from env (Render sets this).
# Dev: docker-compose overrides with --reload.
CMD ["./start.sh"]
