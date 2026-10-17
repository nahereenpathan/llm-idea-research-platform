"""add assumptions to evaluations

Revision ID: 002_add_assumptions_to_evaluations
Revises: 001_initial_schema
Create Date: 2026-10-17 17:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


revision: str = '002_add_assumptions_to_evaluations'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add assumptions column to evaluations table
    with op.batch_alter_table('evaluations') as batch_op:
        batch_op.add_column(sa.Column('assumptions', sa.JSON(), nullable=True))


def downgrade() -> None:
    with op.batch_alter_table('evaluations') as batch_op:
        batch_op.drop_column('assumptions')
