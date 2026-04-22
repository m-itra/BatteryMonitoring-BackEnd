"""Remove legacy fake battery tables.

Revision ID: 0003_remove_legacy_tables
Revises: 0002_real_battery_ingest
Create Date: 2026-04-22
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0003_remove_legacy_tables"
down_revision: Union[str, None] = "0002_real_battery_ingest"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_cycles_completed_at")
    op.execute("DROP INDEX IF EXISTS idx_cycles_device_id")
    op.execute("DROP INDEX IF EXISTS idx_cycles_user_id")
    op.execute("DROP TABLE IF EXISTS battery_cycles")
    op.execute("DROP TABLE IF EXISTS battery_current_cycles")


def downgrade() -> None:
    op.execute(
        """
        CREATE TABLE IF NOT EXISTS battery_current_cycles (
            device_id UUID PRIMARY KEY REFERENCES devices(device_id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            started_at TIMESTAMP,
            last_update TIMESTAMP,
            discharge_start_level INT,
            current_level INT,
            is_charging BOOLEAN,
            state VARCHAR(20)
        )
        """
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS battery_cycles (
            cycle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            started_at TIMESTAMP NOT NULL,
            completed_at TIMESTAMP NOT NULL,
            duration_minutes INT NOT NULL,
            health_score FLOAT,
            capacity_degradation FLOAT,
            cycle_count INT NOT NULL,
            charge_cycles_equivalent FLOAT,
            min_level INT,
            max_level INT,
            avg_discharge_rate FLOAT,
            avg_charge_rate FLOAT,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_cycles_user_id ON battery_cycles(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cycles_device_id ON battery_cycles(device_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_cycles_completed_at ON battery_cycles(completed_at DESC)")
