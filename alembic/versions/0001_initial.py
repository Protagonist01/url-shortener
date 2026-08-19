"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-08-16 00:00:00

"""
from __future__ import annotations

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

revision: str = "0001_initial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"])

    op.create_table(
        "short_urls",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("short_code", sa.String(32), nullable=False),
        sa.Column("original_url", sa.Text(), nullable=False),
        sa.Column("owner_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("short_code", name="uq_short_urls_code"),
    )
    op.create_index("ix_short_urls_short_code", "short_urls", ["short_code"])
    op.create_index("ix_short_urls_owner_id", "short_urls", ["owner_id"])

    op.create_table(
        "click_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("url_id", sa.Integer(), sa.ForeignKey("short_urls.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ip_address", sa.String(45), nullable=True),
        sa.Column("user_agent", sa.Text(), nullable=True),
        sa.Column("referer", sa.Text(), nullable=True),
        sa.Column("country", sa.String(64), nullable=True),
        sa.Column("clicked_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_click_events_url_id", "click_events", ["url_id"])
    op.create_index("ix_click_events_country", "click_events", ["country"])
    op.create_index("ix_click_events_clicked_at", "click_events", ["clicked_at"])


def downgrade() -> None:
    op.drop_index("ix_click_events_clicked_at", table_name="click_events")
    op.drop_index("ix_click_events_country", table_name="click_events")
    op.drop_index("ix_click_events_url_id", table_name="click_events")
    op.drop_table("click_events")

    op.drop_index("ix_short_urls_owner_id", table_name="short_urls")
    op.drop_index("ix_short_urls_short_code", table_name="short_urls")
    op.drop_table("short_urls")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
