"""Initial schema: create chunk table with pgvector support.

Revision ID: 001
Revises:
Create Date: 2026-07-11
"""

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    op.create_table(
        "chunk",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("snippet", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(768), nullable=False),
        sa.Column("page", sa.Integer(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("chunk")
