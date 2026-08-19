from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


def _ensure_driver(url: str, driver: str) -> str:
    """Normalize a Postgres URL to use a specific SQLAlchemy driver.

    Render provides `postgresql://user:pass@host:port/db` (no driver suffix).
    SQLAlchemy needs an explicit driver:
      - async API:  postgresql+asyncpg://   (for the FastAPI process)
      - sync API:   postgresql+psycopg2://  (for Celery workers + Alembic)

    This function inserts the driver if it's missing, and replaces it if
    a different one is present. This lets the same DATABASE_URL env var
    work for both local dev (where we set it with +asyncpg manually) and
    Render (where the platform provides it without a driver).
    """
    if "postgresql+asyncpg://" in url:
        base = url.replace("postgresql+asyncpg://", "postgresql://")
    elif "postgresql+psycopg2://" in url:
        base = url.replace("postgresql+psycopg2://", "postgresql://")
    else:
        base = url

    return base.replace("postgresql://", f"postgresql+{driver}://")


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    APP_ENV: str = "development"
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 7

    DATABASE_URL: str
    REDIS_URL: str

    CELERY_BROKER_URL: str
    CELERY_RESULT_BACKEND: str

    CACHE_TTL_SECONDS: int = 3600
    SHORT_URL_BASE: str = "http://localhost:8000"

    @property
    def async_database_url(self) -> str:
        """URL with asyncpg driver for the FastAPI process."""
        return _ensure_driver(self.DATABASE_URL, "asyncpg")

    @property
    def sync_database_url(self) -> str:
        """URL with psycopg2 driver for Celery + Alembic."""
        return _ensure_driver(self.DATABASE_URL, "psycopg2")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
