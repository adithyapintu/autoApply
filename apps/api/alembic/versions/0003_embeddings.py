"""add vector embeddings to jobs and profiles

Revision ID: 0003_embeddings
Revises: 0002_profile_tech_stacks
Create Date: 2026-06-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0003_embeddings"
down_revision = "0002_profile_tech_stacks"
branch_labels = None
depends_on = None

VECTOR_DIM = 384


def upgrade() -> None:
    # Ensure the vector extension is available (pgvector/pgvector Docker image includes it)
    conn = op.get_bind()
    conn.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector"))

    # Add embedding columns using raw SQL so we don't need pgvector installed at migration time
    op.execute(f"ALTER TABLE jobs ADD COLUMN IF NOT EXISTS embedding vector({VECTOR_DIM})")
    op.execute(f"ALTER TABLE profiles ADD COLUMN IF NOT EXISTS embedding vector({VECTOR_DIM})")

    # IVFFlat index for approximate nearest-neighbour cosine search on jobs
    # lists=100 is a good starting point; increase as job count grows
    op.execute(
        "CREATE INDEX IF NOT EXISTS ix_jobs_embedding_cosine "
        "ON jobs USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_jobs_embedding_cosine")
    op.execute("ALTER TABLE profiles DROP COLUMN IF EXISTS embedding")
    op.execute("ALTER TABLE jobs DROP COLUMN IF EXISTS embedding")
