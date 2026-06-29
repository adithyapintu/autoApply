"""phase 3 - saved_searches, referral fields, applied_at

Revision ID: 0004_phase3
Revises: 0003_embeddings
Create Date: 2026-06-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0004_phase3"
down_revision = "0003_embeddings"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Application: referral tracking + applied_at
    op.add_column("applications", sa.Column("referred_by", sa.String(220), nullable=True))
    op.add_column("applications", sa.Column("referral_channel", sa.String(64), nullable=True))
    op.add_column("applications", sa.Column("applied_at", sa.DateTime(timezone=True), nullable=True))

    # Saved searches
    op.create_table(
        "saved_searches",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(180), nullable=False),
        sa.Column("source", sa.String(64), nullable=False),
        sa.Column("query", sa.String(512), nullable=False, server_default=""),
        sa.Column("location", sa.String(220), nullable=True),
        sa.Column("remote_only", sa.Boolean(), nullable=False, server_default="false"),
        sa.Column("salary_min", sa.Integer(), nullable=True),
        sa.Column("score_threshold", sa.Numeric(5, 2), nullable=False, server_default="60.0"),
        sa.Column("interval_hours", sa.Integer(), nullable=False, server_default="24"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default="true"),
        sa.Column("last_run_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_saved_searches_user", "saved_searches", ["user_id"])


def downgrade() -> None:
    op.drop_index("ix_saved_searches_user", "saved_searches")
    op.drop_table("saved_searches")
    op.drop_column("applications", "applied_at")
    op.drop_column("applications", "referral_channel")
    op.drop_column("applications", "referred_by")
