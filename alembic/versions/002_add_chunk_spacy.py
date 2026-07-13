"""Add chunk_spacy table for spaCy embedding experiments (300d).

Revision ID: 002
Revises: 001
Create Date: 2026-07-11
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "chunk_spacy",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(300), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("chunk_spacy")
