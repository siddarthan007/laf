"""Add has_match_found field to items table.

Revision ID: 20250113_000002
Revises: 3713cb3a645a
Create Date: 2025-01-13 18:32:35
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20250113_000002'
down_revision = '3713cb3a645a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add has_match_found column to items table
    op.add_column('items', sa.Column('has_match_found', sa.Boolean(), nullable=False, server_default='false'))


def downgrade() -> None:
    # Remove has_match_found column from items table
    op.drop_column('items', 'has_match_found')

