"""Change equivalent cycle session linkage to cascade delete.

Revision ID: 0005_cycle_delete_cascade
Revises: 0004_cycle_exclusion_flags
Create Date: 2026-04-28
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0005_cycle_delete_cascade"
down_revision: Union[str, None] = "0004_cycle_exclusion_flags"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE battery_sessions DROP CONSTRAINT IF EXISTS battery_sessions_equivalent_cycle_id_fkey"
    )
    op.execute(
        """
        ALTER TABLE battery_sessions
        ADD CONSTRAINT battery_sessions_equivalent_cycle_id_fkey
        FOREIGN KEY (equivalent_cycle_id)
        REFERENCES battery_equivalent_cycles(cycle_id)
        ON DELETE CASCADE
        """
    )


def downgrade() -> None:
    op.execute(
        "ALTER TABLE battery_sessions DROP CONSTRAINT IF EXISTS battery_sessions_equivalent_cycle_id_fkey"
    )
    op.execute(
        """
        ALTER TABLE battery_sessions
        ADD CONSTRAINT battery_sessions_equivalent_cycle_id_fkey
        FOREIGN KEY (equivalent_cycle_id)
        REFERENCES battery_equivalent_cycles(cycle_id)
        ON DELETE SET NULL
        """
    )
