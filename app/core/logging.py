"""Structured JSON logging configuration.

Outputs one JSON object per log line, so logs can be ingested by Loki,
Elasticsearch, or any log aggregator that expects structured data.

In development (APP_ENV != "production"), logs are human-readable text for
console readability. In production, they switch to JSON.
"""
from __future__ import annotations

import json
import logging
import sys
from datetime import datetime, timezone

from app.core.config import settings


class JSONFormatter(logging.Formatter):
    """Format log records as single-line JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        if record.exc_info and record.exc_info[1] is not None:
            log_entry["exception"] = self.formatException(record.exc_info)
        if hasattr(record, "extra_fields"):
            log_entry.update(record.extra_fields)
        return json.dumps(log_entry, default=str)


def setup_logging() -> None:
    """Configure root logger. Call once at app startup."""
    root = logging.getLogger()
    root.setLevel(logging.INFO)

    handler = logging.StreamHandler(sys.stdout)
    if settings.APP_ENV == "production":
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(
            logging.Formatter(
                "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
                datefmt="%H:%M:%S",
            )
        )

    root.handlers = [handler]

    # Quiet down noisy libraries.
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
