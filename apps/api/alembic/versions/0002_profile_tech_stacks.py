"""add tech_stacks, field, summary to profiles

Revision ID: 0002_profile_tech_stacks
Revises: 0001_initial_schema
Create Date: 2026-06-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0002_profile_tech_stacks"
down_revision = "0001_initial_schema"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("profiles", sa.Column("field", sa.String(120), nullable=True))
    op.add_column("profiles", sa.Column("tech_stacks", sa.JSON(), nullable=False, server_default="[]"))
    op.add_column("profiles", sa.Column("summary", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("profiles", "summary")
    op.drop_column("profiles", "tech_stacks")
    op.drop_column("profiles", "field")
