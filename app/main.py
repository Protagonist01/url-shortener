from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.api import analytics, auth, redirect, urls
from app.core.config import settings
from app.core.logging import setup_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    setup_logging()
    yield
    from app.core.redis import redis_client

    await redis_client.aclose()


app = FastAPI(
    title="URL Shortener with Analytics",
    description=(
        "FastAPI + PostgreSQL + Redis + Celery. "
        "Shorten URLs, cache redirects in Redis, and track clicks "
        "asynchronously via a Celery worker."
    ),
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Prometheus metrics: auto-tracks http_requests_total, http_request_duration_seconds,
# and http_responses_total by route + status + method. Exposed at /metrics.
Instrumentator(
    should_group_status_codes=True,
    should_ignore_untemplated=True,
    should_respect_env_var=False,
    excluded_handlers=["/metrics"],
).instrument(app).expose(app, endpoint="/metrics")

app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(auth.router)
app.include_router(urls.router)
app.include_router(analytics.router)


@app.get("/health", tags=["meta"])
async def health() -> dict:
    return {"status": "ok", "env": settings.APP_ENV}


@app.get("/", include_in_schema=False)
async def root():
    return FileResponse("app/static/index.html")


# redirect router LAST: it matches /{short_code} which would otherwise
# shadow every other top-level route registered after it.
app.include_router(redirect.router)
