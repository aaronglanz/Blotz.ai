"""add cached_listings table for scraped property data

Revision ID: 006
Revises: 005
Create Date: 2026-04-28
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "006"
down_revision: Union[str, None] = "005"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "cached_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("source", sa.String(100), nullable=False),
        sa.Column("source_url", sa.String(2000), nullable=False),
        sa.Column("source_id", sa.String(200), nullable=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("location", sa.String(500), nullable=False),
        sa.Column("suburb", sa.String(200), nullable=True),
        sa.Column("city", sa.String(200), nullable=False, server_default="Cape Town"),
        sa.Column("price_amount", sa.Integer, nullable=True),
        sa.Column("price_display", sa.String(100), nullable=False),
        sa.Column("bedrooms", sa.Integer, nullable=True),
        sa.Column("bathrooms", sa.Integer, nullable=True),
        sa.Column("size_sqm", sa.Integer, nullable=True),
        sa.Column("property_type", sa.String(100), nullable=True),
        sa.Column("furnished", sa.Boolean, nullable=True),
        sa.Column("pets_allowed", sa.Boolean, nullable=True),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("amenities", JSON, nullable=False, server_default="[]"),
        sa.Column("image_url", sa.String(2000), nullable=True),
        sa.Column("image_urls", JSON, nullable=False, server_default="[]"),
        sa.Column("contact_name", sa.String(200), nullable=True),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("available_from", sa.String(50), nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_url", name="uq_cached_listing_source_url"),
    )
    # Indexes for common query patterns
    op.create_index("ix_cached_listings_suburb", "cached_listings", ["suburb"])
    op.create_index("ix_cached_listings_price", "cached_listings", ["price_amount"])
    op.create_index("ix_cached_listings_bedrooms", "cached_listings", ["bedrooms"])
    op.create_index("ix_cached_listings_is_active", "cached_listings", ["is_active"])


def downgrade() -> None:
    op.drop_index("ix_cached_listings_is_active")
    op.drop_index("ix_cached_listings_bedrooms")
    op.drop_index("ix_cached_listings_price")
    op.drop_index("ix_cached_listings_suburb")
    op.drop_table("cached_listings")
