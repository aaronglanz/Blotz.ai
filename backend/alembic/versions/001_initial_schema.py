"""initial schema

Revision ID: 001
Revises:
Create Date: 2026-03-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "searches",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("query_text", sa.String(2000), nullable=False),
        sa.Column("interpreted_intent", JSON, nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="pending"),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "search_results",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("search_id", UUID(as_uuid=True), sa.ForeignKey("searches.id"), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("price", sa.String(100), nullable=True),
        sa.Column("beds", sa.Integer, nullable=True),
        sa.Column("baths", sa.Integer, nullable=True),
        sa.Column("size", sa.String(100), nullable=True),
        sa.Column("furnished", sa.Boolean, nullable=True),
        sa.Column("pets", sa.Boolean, nullable=True),
        sa.Column("lease", sa.String(200), nullable=True),
        sa.Column("amenities", JSON, nullable=False, server_default="[]"),
        sa.Column("match_score", sa.Integer, nullable=True),
        sa.Column("matched", JSON, nullable=False, server_default="[]"),
        sa.Column("not_matched", JSON, nullable=False, server_default="[]"),
        sa.Column("match_reason", sa.Text, nullable=True),
        sa.Column("url", sa.String(2000), nullable=True),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("image_url", sa.String(2000), nullable=True),
        sa.Column("availability", sa.String(50), nullable=True),
        sa.Column("rank", sa.Integer, nullable=False),
    )

    op.create_table(
        "saved_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("url", sa.String(2000), nullable=False, unique=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("location", sa.String(500), nullable=True),
        sa.Column("price", sa.String(100), nullable=True),
        sa.Column("source", sa.String(200), nullable=True),
        sa.Column("image_url", sa.String(2000), nullable=True),
        sa.Column("saved_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("saved_listings")
    op.drop_table("search_results")
    op.drop_table("searches")
