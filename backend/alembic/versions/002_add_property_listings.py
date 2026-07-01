"""add property listings table

Revision ID: 002
Revises: 001
Create Date: 2026-04-01
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSON

revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "property_listings",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("location", sa.String(500), nullable=False),
        sa.Column("price", sa.String(100), nullable=False),
        sa.Column("bedrooms", sa.Integer, nullable=False),
        sa.Column("bathrooms", sa.Integer, nullable=False),
        sa.Column("size", sa.String(100), nullable=True),
        sa.Column("furnished", sa.String(20), nullable=False, server_default="no"),
        sa.Column("pets_allowed", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("lease_type", sa.String(200), nullable=True),
        sa.Column("amenities", JSON, nullable=False, server_default="[]"),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("contact_name", sa.String(200), nullable=False),
        sa.Column("contact_email", sa.String(300), nullable=False),
        sa.Column("contact_phone", sa.String(50), nullable=True),
        sa.Column("image_url", sa.String(2000), nullable=True),
        sa.Column("available_from", sa.String(50), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("property_listings")
