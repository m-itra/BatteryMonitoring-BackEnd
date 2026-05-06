"""Store battery durations as floating-point seconds.

Revision ID: 0006_duration_float_precision
Revises: 0005_cycle_delete_cascade
Create Date: 2026-05-05
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0006_duration_float_precision"
down_revision: Union[str, None] = "0005_cycle_delete_cascade"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        ALTER TABLE battery_active_sessions
        ALTER COLUMN duration_seconds TYPE DOUBLE PRECISION
        USING duration_seconds::double precision
        """
    )
    op.execute(
        """
        ALTER TABLE battery_sessions
        ALTER COLUMN duration_seconds TYPE DOUBLE PRECISION
        USING duration_seconds::double precision
        """
    )
    op.execute(
        """
        ALTER TABLE battery_equivalent_cycles
        ALTER COLUMN total_duration_seconds TYPE DOUBLE PRECISION
        USING total_duration_seconds::double precision
        """
    )


def downgrade() -> None:
    op.execute(
        """
        ALTER TABLE battery_active_sessions
        ALTER COLUMN duration_seconds TYPE INTEGER
        USING ROUND(duration_seconds)::integer
        """
    )
    op.execute(
        """
        ALTER TABLE battery_sessions
        ALTER COLUMN duration_seconds TYPE INTEGER
        USING ROUND(duration_seconds)::integer
        """
    )
    op.execute(
        """
        ALTER TABLE battery_equivalent_cycles
        ALTER COLUMN total_duration_seconds TYPE INTEGER
        USING ROUND(total_duration_seconds)::integer
        """
    )
