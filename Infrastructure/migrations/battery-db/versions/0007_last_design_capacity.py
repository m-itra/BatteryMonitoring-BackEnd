"""Store last design capacity on devices.

Revision ID: 0007_last_design_capacity
Revises: 0006_duration_float_precision
Create Date: 2026-05-07
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0007_last_design_capacity"
down_revision: Union[str, None] = "0006_duration_float_precision"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("devices", sa.Column("last_design_capacity_mwh", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("devices", "last_design_capacity_mwh")
