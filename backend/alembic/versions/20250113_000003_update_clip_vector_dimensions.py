"""Update CLIP vector dimensions from 512 to 768.

Revision ID: 20250113_000003
Revises: 20250113_000002
Create Date: 2025-01-13 20:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '20250113_000003'
down_revision = '20250113_000002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update description_clip_vector from 512 to 768 dimensions
    # Note: pgvector doesn't support direct ALTER COLUMN for vector dimensions.
    # We drop and recreate the columns. 
    # WARNING: If you have existing rows, you'll need to either:
    #   1. Delete them before running this migration, OR
    #   2. Regenerate their embeddings after the migration
    
    # Make description_clip_vector nullable temporarily to allow dropping
    op.alter_column('items', 'description_clip_vector', nullable=True)
    
    # Drop the old columns
    op.drop_column('items', 'description_clip_vector')
    op.drop_column('items', 'image_vector')
    
    # Recreate with correct dimensions (768)
    op.add_column('items', sa.Column('description_clip_vector', Vector(768), nullable=False))
    op.add_column('items', sa.Column('image_vector', Vector(768), nullable=True))


def downgrade() -> None:
    # Revert description_clip_vector and image_vector from 768 to 512 dimensions
    
    # Drop the 768-dim columns
    op.drop_column('items', 'description_clip_vector')
    op.drop_column('items', 'image_vector')
    
    # Recreate with 512 dimensions
    op.add_column('items', sa.Column('description_clip_vector', Vector(512), nullable=False))
    op.add_column('items', sa.Column('image_vector', Vector(512), nullable=True))

