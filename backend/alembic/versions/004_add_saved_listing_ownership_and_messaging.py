"""add per-user saved listings and messaging tables

Revision ID: 004
Revises: 003
Create Date: 2026-04-02
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID

revision: str = "004"
down_revision: Union[str, None] = "003"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "saved_listings",
        sa.Column("user_id", sa.String(length=100), nullable=False, server_default="legacy"),
    )
    op.add_column(
        "saved_listings",
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("property_listings.id"), nullable=True),
    )
    op.drop_constraint("saved_listings_url_key", "saved_listings", type_="unique")
    op.alter_column("saved_listings", "url", existing_type=sa.String(length=2000), nullable=True)
    op.create_index("ix_saved_listings_user_id", "saved_listings", ["user_id"])
    op.create_unique_constraint(
        "uq_saved_listings_user_url",
        "saved_listings",
        ["user_id", "url"],
    )
    op.create_unique_constraint(
        "uq_saved_listings_user_listing_id",
        "saved_listings",
        ["user_id", "listing_id"],
    )
    op.alter_column("saved_listings", "user_id", server_default=None)

    op.create_table(
        "conversations",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("renter_user_id", sa.String(100), nullable=False),
        sa.Column("agent_user_id", sa.String(100), nullable=False),
        sa.Column("listing_id", UUID(as_uuid=True), sa.ForeignKey("property_listings.id"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_message_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("renter_user_id", "listing_id", name="uq_conversations_renter_listing"),
    )
    op.create_index("ix_conversations_renter_user_id", "conversations", ["renter_user_id"])
    op.create_index("ix_conversations_agent_user_id", "conversations", ["agent_user_id"])

    op.create_table(
        "conversation_messages",
        sa.Column("id", UUID(as_uuid=True), primary_key=True),
        sa.Column("conversation_id", UUID(as_uuid=True), sa.ForeignKey("conversations.id"), nullable=False),
        sa.Column("sender_user_id", sa.String(100), nullable=False),
        sa.Column("body", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "ix_conversation_messages_conversation_id",
        "conversation_messages",
        ["conversation_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_conversation_id", table_name="conversation_messages")
    op.drop_table("conversation_messages")
    op.drop_index("ix_conversations_agent_user_id", table_name="conversations")
    op.drop_index("ix_conversations_renter_user_id", table_name="conversations")
    op.drop_table("conversations")

    op.drop_constraint("uq_saved_listings_user_listing_id", "saved_listings", type_="unique")
    op.drop_constraint("uq_saved_listings_user_url", "saved_listings", type_="unique")
    op.drop_index("ix_saved_listings_user_id", table_name="saved_listings")
    op.alter_column("saved_listings", "url", existing_type=sa.String(length=2000), nullable=False)
    op.create_unique_constraint("saved_listings_url_key", "saved_listings", ["url"])
    op.drop_column("saved_listings", "listing_id")
    op.drop_column("saved_listings", "user_id")
