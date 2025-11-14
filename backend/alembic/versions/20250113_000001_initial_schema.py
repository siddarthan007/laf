"""Initial schema for lost & found domain.

Revision ID: 20250113_000001
Revises:
Create Date: 2025-11-13 12:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


revision = "20250113_000001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Create enum types using raw SQL to handle existing types gracefully
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE user_role AS ENUM ('USER', 'ADMIN');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE item_status AS ENUM ('LOST', 'FOUND');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE match_status AS ENUM ('PENDING', 'APPROVED', 'REJECTED');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)

    # Check if tables already exist to avoid errors
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    existing_tables = inspector.get_table_names()

    # Use PostgreSQL ENUM type directly without creation
    # Monkey-patch the create method to prevent automatic creation
    user_role_type = sa.dialects.postgresql.ENUM("USER", "ADMIN", name="user_role", create_type=False)
    item_status_type = sa.dialects.postgresql.ENUM("LOST", "FOUND", name="item_status", create_type=False)
    match_status_type = sa.dialects.postgresql.ENUM("PENDING", "APPROVED", "REJECTED", name="match_status", create_type=False)
    
    # Disable automatic enum creation by patching the create method
    def noop_create(*args, **kwargs):
        pass
    
    user_role_type.create = noop_create
    item_status_type.create = noop_create
    match_status_type.create = noop_create

    if "users" not in existing_tables:
        op.create_table(
            "users",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column("name", sa.String(length=255), nullable=False),
            sa.Column("email", sa.String(length=255), nullable=False, unique=True),
            sa.Column("hashed_password", sa.String(length=255), nullable=False),
            sa.Column("roll_number", sa.String(length=64), nullable=False, unique=True),
            sa.Column("hostel", sa.String(length=128)),
            sa.Column("contact_number", sa.String(length=32), nullable=False),
            sa.Column("role", user_role_type, nullable=False, server_default="USER"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_users_email", "users", ["email"], unique=True)

    if "items" not in existing_tables:
        op.create_table(
            "items",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "reported_by_user_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("status", item_status_type, nullable=False, index=True),
            sa.Column("description", sa.Text, nullable=False),
            sa.Column("location", sa.String(length=255), nullable=False),
            sa.Column("image_url", sa.String(length=512)),
            sa.Column("description_vector", Vector(384), nullable=False),
            sa.Column("description_clip_vector", Vector(512), nullable=False),
            sa.Column("image_vector", Vector(512)),
            sa.Column("is_active", sa.Boolean, nullable=False, server_default=sa.text("true")),
            sa.Column("is_admin_report", sa.Boolean, nullable=False, server_default=sa.text("false")),
            sa.Column(
                "reported_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
        )
        op.create_index("ix_items_reported_at", "items", ["reported_at"])

    if "matches" not in existing_tables:
        op.create_table(
            "matches",
            sa.Column("id", sa.dialects.postgresql.UUID(as_uuid=True), primary_key=True),
            sa.Column(
                "lost_item_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "found_item_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("items.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "loser_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column(
                "finder_id",
                sa.dialects.postgresql.UUID(as_uuid=True),
                sa.ForeignKey("users.id", ondelete="CASCADE"),
                nullable=False,
            ),
            sa.Column("confidence_score", sa.Float, nullable=False),
            sa.Column("match_status", match_status_type, nullable=False, server_default="PENDING"),
            sa.Column(
                "created_at",
                sa.DateTime(timezone=True),
                nullable=False,
                server_default=sa.func.now(),
            ),
            sa.UniqueConstraint("lost_item_id", "found_item_id", name="uq_match_lost_found"),
        )
        op.create_index("ix_matches_lost_item_id", "matches", ["lost_item_id"])
        op.create_index("ix_matches_found_item_id", "matches", ["found_item_id"])
        op.create_index("ix_matches_status", "matches", ["match_status"])


def downgrade() -> None:
    op.drop_index("ix_matches_status", table_name="matches")
    op.drop_index("ix_matches_found_item_id", table_name="matches")
    op.drop_index("ix_matches_lost_item_id", table_name="matches")
    op.drop_table("matches")

    op.drop_index("ix_items_reported_at", table_name="items")
    op.drop_table("items")

    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")

    sa.Enum(name="match_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="item_status").drop(op.get_bind(), checkfirst=True)
    sa.Enum(name="user_role").drop(op.get_bind(), checkfirst=True)
    op.execute("DROP EXTENSION IF EXISTS vector")

