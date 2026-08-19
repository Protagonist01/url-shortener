"""add daily_stats table

Revision ID: 0002_daily_stats
Revises: 0001_initial
Create Date: 2026-08-16 05:30:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0002_daily_stats"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "daily_stats",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "url_id",
            sa.Integer(),
            sa.ForeignKey("short_urls.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("date", sa.DateTime(timezone=True), nullable=False),
        sa.Column("click_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("unique_ips", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("top_country", sa.String(64), nullable=True),
        sa.UniqueConstraint("url_id", "date", name="uq_daily_stats_url_date"),
    )
    op.create_index("ix_daily_stats_url_id", "daily_stats", ["url_id"])
    op.create_index("ix_daily_stats_date", "daily_stats", ["date"])


def downgrade() -> None:
    op.drop_index("ix_daily_stats_date", table_name="daily_stats")
    op.drop_index("ix_daily_stats_url_id", table_name="daily_stats")
    op.drop_table("daily_stats")
