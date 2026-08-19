from datetime import datetime, timezone

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import DateTime


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )


class User(TimestampMixin, Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    hashed_password: Mapped[str] = mapped_column(String(255))

    urls: Mapped[list["ShortURL"]] = relationship(
        back_populates="owner", cascade="all, delete-orphan"
    )


class ShortURL(TimestampMixin, Base):
    __tablename__ = "short_urls"

    id: Mapped[int] = mapped_column(primary_key=True)
    short_code: Mapped[str] = mapped_column(String(32), unique=True, index=True)
    original_url: Mapped[str] = mapped_column(Text)
    owner_id: Mapped[int | None] = mapped_column(
        ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True
    )
    is_active: Mapped[bool] = mapped_column(default=True)

    owner: Mapped["User | None"] = relationship(back_populates="urls")
    clicks: Mapped[list["ClickEvent"]] = relationship(
        back_populates="url", cascade="all, delete-orphan"
    )


class ClickEvent(Base):
    __tablename__ = "click_events"

    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(
        ForeignKey("short_urls.id", ondelete="CASCADE"), index=True
    )
    ip_address: Mapped[str | None] = mapped_column(String(45))
    user_agent: Mapped[str | None] = mapped_column(Text)
    referer: Mapped[str | None] = mapped_column(Text)
    country: Mapped[str | None] = mapped_column(String(64), index=True)
    clicked_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        index=True,
    )

    url: Mapped["ShortURL"] = relationship(back_populates="clicks")


class DailyStats(Base):
    """Pre-aggregated click counts per URL per day.

    Populated by a Celery beat job (`aggregate_daily_stats`) that runs
    hourly. The analytics endpoint reads from this table for the timeseries
    instead of re-scanning the full click_events table on every request.
    """
    __tablename__ = "daily_stats"

    id: Mapped[int] = mapped_column(primary_key=True)
    url_id: Mapped[int] = mapped_column(
        ForeignKey("short_urls.id", ondelete="CASCADE"), index=True
    )
    date: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    click_count: Mapped[int] = mapped_column(default=0)
    unique_ips: Mapped[int] = mapped_column(default=0)
    top_country: Mapped[str | None] = mapped_column(String(64))

    __table_args__ = (
        UniqueConstraint("url_id", "date", name="uq_daily_stats_url_date"),
    )
