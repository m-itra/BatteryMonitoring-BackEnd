"""Add exclusion flags to equivalent cycles.

Revision ID: 0004_cycle_exclusion_flags
Revises: 0003_remove_legacy_tables
Create Date: 2026-04-27
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0004_cycle_exclusion_flags"
down_revision: Union[str, None] = "0003_remove_legacy_tables"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        "ALTER TABLE battery_equivalent_cycles ADD COLUMN IF NOT EXISTS is_excluded BOOLEAN NOT NULL DEFAULT false"
    )
    op.execute(
        "ALTER TABLE battery_equivalent_cycles ADD COLUMN IF NOT EXISTS excluded_at TIMESTAMP"
    )


def downgrade() -> None:
    op.execute("ALTER TABLE battery_equivalent_cycles DROP COLUMN IF EXISTS excluded_at")
    op.execute("ALTER TABLE battery_equivalent_cycles DROP COLUMN IF EXISTS is_excluded")
