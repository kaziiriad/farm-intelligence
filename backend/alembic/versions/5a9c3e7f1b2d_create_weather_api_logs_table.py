"""create weather_api_logs table

Revision ID: 5a9c3e7f1b2d
Revises: 01ccf7d5a461
Create Date: 2026-06-06 23:10:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5a9c3e7f1b2d'
down_revision: Union[str, None] = '01ccf7d5a461'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'weather_api_logs',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('endpoint', sa.String(length=255), nullable=False),
        sa.Column('request_params', sa.JSON(), nullable=False),
        sa.Column('status_code', sa.Integer(), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=False),
        sa.Column('cache_hit', sa.Boolean(), nullable=False),
        sa.Column('error_message', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_weather_api_logs_endpoint'), 'weather_api_logs', ['endpoint'], unique=False)
    op.create_index(op.f('ix_weather_api_logs_created_at'), 'weather_api_logs', ['created_at'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_weather_api_logs_created_at'), table_name='weather_api_logs')
    op.drop_index(op.f('ix_weather_api_logs_endpoint'), table_name='weather_api_logs')
    op.drop_table('weather_api_logs')