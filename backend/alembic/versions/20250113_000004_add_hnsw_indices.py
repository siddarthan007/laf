"""Add HNSW indices for vector columns.

Revision ID: 20250113_000004
Revises: 20250113_000003
Create Date: 2025-01-13 21:00:00
"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector


# revision identifiers, used by Alembic.
revision = '20250113_000004'
down_revision = '20250113_000003'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add HNSW indices for vector columns
    # We use cosine distance (vector_cosine_ops) as that's what our similarity logic uses
    
    # Index for description_vector (384 dim)
    op.create_index(
        'ix_items_description_vector',
        'items',
        ['description_vector'],
        postgresql_using='hnsw',
        postgresql_with={'m': 16, 'ef_construction': 64},
        postgresql_ops={'description_vector': 'vector_cosine_ops'}
    )

    # Index for description_clip_vector (768 dim)
    op.create_index(
        'ix_items_description_clip_vector',
        'items',
        ['description_clip_vector'],
        postgresql_using='hnsw',
        postgresql_with={'m': 16, 'ef_construction': 64},
        postgresql_ops={'description_clip_vector': 'vector_cosine_ops'}
    )

    # Index for image_vector (768 dim)
    # Note: image_vector is nullable, so we might want a partial index or just a regular one.
    # HNSW handles nulls by ignoring them usually, but let's be standard.
    op.create_index(
        'ix_items_image_vector',
        'items',
        ['image_vector'],
        postgresql_using='hnsw',
        postgresql_with={'m': 16, 'ef_construction': 64},
        postgresql_ops={'image_vector': 'vector_cosine_ops'}
    )


def downgrade() -> None:
    op.drop_index('ix_items_image_vector', table_name='items')
    op.drop_index('ix_items_description_clip_vector', table_name='items')
    op.drop_index('ix_items_description_vector', table_name='items')
