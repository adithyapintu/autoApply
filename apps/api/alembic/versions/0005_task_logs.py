"""phase 4 - task_logs for background job tracking

Revision ID: 0005_task_logs
Revises: 0004_phase3
Create Date: 2026-06-30
"""

import sqlalchemy as sa
from alembic import op

revision = "0005_task_logs"
down_revision = "0004_phase3"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "task_logs",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("celery_task_id", sa.String(255), nullable=False),
        sa.Column("task_name", sa.String(120), nullable=False),
        sa.Column("status", sa.String(64), nullable=False, server_default="pending"),
        sa.Column("params", sa.JSON(), nullable=False, server_default="{}"),
        sa.Column("result", sa.JSON(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )
    op.create_index("ix_task_logs_user_id", "task_logs", ["user_id"])
    op.create_index("ix_task_logs_celery_task_id", "task_logs", ["celery_task_id"])


def downgrade() -> None:
    op.drop_table("task_logs")
