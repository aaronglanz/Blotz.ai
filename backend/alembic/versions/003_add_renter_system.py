"""add renter profiles, documents, applications, access log tables

Revision ID: 003
Revises: 002
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "003"
down_revision: Union[str, None] = "002"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add user_id to property_listings
    op.add_column("property_listings", sa.Column("user_id", sa.String(100), nullable=True))

    op.create_table(
        "renter_profiles",
        sa.Column("user_id", sa.String(100), primary_key=True),
        sa.Column("full_name", sa.String(300), nullable=True),
        sa.Column("id_number", sa.String(20), nullable=True),
        sa.Column("phone", sa.String(50), nullable=True),
        sa.Column("email", sa.String(300), nullable=True),
        sa.Column("employment_status", sa.String(50), nullable=True),
        sa.Column("monthly_income", sa.String(100), nullable=True),
        sa.Column("employer_name", sa.String(300), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "renter_documents",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("document_type", sa.String(50), nullable=False),
        sa.Column("file_path", sa.String(1000), nullable=False),
        sa.Column("file_name", sa.String(500), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "applications",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", sa.String(100), nullable=False),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("property_listings.id"), nullable=False),
        sa.Column("agent_user_id", sa.String(100), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="Applied"),
        sa.Column("applied_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )

    op.create_table(
        "document_access_log",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("agent_id", sa.String(100), nullable=False),
        sa.Column("document_id", UUID(as_uuid=True), sa.ForeignKey("renter_documents.id"), nullable=False),
        sa.Column("accessed_at", sa.DateTime(timezone=True), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("document_access_log")
    op.drop_table("applications")
    op.drop_table("renter_documents")
    op.drop_table("renter_profiles")
    op.drop_column("property_listings", "user_id")
