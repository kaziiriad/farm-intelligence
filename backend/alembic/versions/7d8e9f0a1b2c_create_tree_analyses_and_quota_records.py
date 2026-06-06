"""create tree analyses and quota records tables

Revision ID: 7d8e9f0a1b2c
Revises: 5a9c3e7f1b2d
Create Date: 2026-06-07 00:20:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "7d8e9f0a1b2c"
down_revision: str | None = "5a9c3e7f1b2d"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "tree_analyses",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("farm_id", sa.Uuid(), nullable=False),
        sa.Column("image_url", sa.String(length=500), nullable=True),
        sa.Column("analysis_result", sa.JSON(), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["farm_id"], ["farms.id"]),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quota_records",
        sa.Column("farm_id", sa.Uuid(), nullable=False),
        sa.Column("month_year", sa.String(length=7), nullable=False),
        sa.Column("request_count", sa.Integer(), nullable=False),
        sa.Column(
            "last_incremented_at",
            sa.DateTime(),
            server_default=sa.text("(CURRENT_TIMESTAMP)"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("farm_id", "month_year"),
        sa.UniqueConstraint("farm_id", "month_year", name="uq_quota_farm_month"),
    )


def downgrade() -> None:
    op.drop_table("quota_records")
    op.drop_table("tree_analyses")
