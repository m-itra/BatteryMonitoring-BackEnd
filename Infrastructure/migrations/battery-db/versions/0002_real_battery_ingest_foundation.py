"""Add real battery ingest foundation.

Revision ID: 0002_real_battery_ingest
Revises: 0001_battery_schema
Create Date: 2026-04-22
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002_real_battery_ingest"
down_revision: Union[str, None] = "0001_battery_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS battery_id VARCHAR(255)")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_client_time TIMESTAMP")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_boot_session_id UUID")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_sample_seq INT")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_ac_connected BOOLEAN")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_is_charging BOOLEAN")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_charge_percent DOUBLE PRECISION")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_full_charge_capacity_mwh INT")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_remaining_capacity_mwh INT")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS last_net_power_mw INT")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS reference_capacity_mwh INT")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS reference_capacity_source VARCHAR(20)")
    op.execute("ALTER TABLE devices ADD COLUMN IF NOT EXISTS baseline_capacity_mwh INT")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS battery_active_sessions (
            device_id UUID PRIMARY KEY REFERENCES devices(device_id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            boot_session_id UUID NOT NULL,
            started_at_client TIMESTAMP NOT NULL,
            started_at_server TIMESTAMP NOT NULL,
            last_client_time TIMESTAMP NOT NULL,
            last_server_received_at TIMESTAMP NOT NULL,
            last_sample_seq INT NOT NULL,
            start_charge_percent DOUBLE PRECISION NOT NULL,
            current_charge_percent DOUBLE PRECISION NOT NULL,
            discharged_energy_mwh DOUBLE PRECISION NOT NULL DEFAULT 0,
            duration_seconds INT NOT NULL DEFAULT 0,
            pending_transition VARCHAR(20) NOT NULL DEFAULT 'none',
            pending_transition_at_client TIMESTAMP,
            pending_transition_at_server TIMESTAMP,
            pending_transition_charge_percent DOUBLE PRECISION
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_active_sessions_user_id ON battery_active_sessions(user_id)")

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS battery_equivalent_cycles (
            cycle_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            started_at_client TIMESTAMP NOT NULL,
            ended_at_client TIMESTAMP NOT NULL,
            session_count INT NOT NULL,
            total_discharge_percent DOUBLE PRECISION NOT NULL,
            total_energy_mwh DOUBLE PRECISION NOT NULL,
            total_duration_seconds INT NOT NULL,
            avg_load_mw DOUBLE PRECISION,
            reference_capacity_mwh_used INT NOT NULL,
            full_charge_capacity_mwh_at_cycle_end INT,
            soh_capacity_percent DOUBLE PRECISION,
            degradation_capacity_percent DOUBLE PRECISION,
            soh_energy_percent DOUBLE PRECISION,
            degradation_energy_percent DOUBLE PRECISION,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_equivalent_cycles_user_id ON battery_equivalent_cycles(user_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_equivalent_cycles_device_id ON battery_equivalent_cycles(device_id)"
    )
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_equivalent_cycles_ended_at ON battery_equivalent_cycles(ended_at_client DESC)"
    )

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS battery_sessions (
            session_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            device_id UUID NOT NULL REFERENCES devices(device_id) ON DELETE CASCADE,
            user_id UUID NOT NULL,
            boot_session_id UUID NOT NULL,
            started_at_client TIMESTAMP NOT NULL,
            ended_at_client TIMESTAMP NOT NULL,
            started_at_server TIMESTAMP NOT NULL,
            ended_at_server TIMESTAMP NOT NULL,
            start_charge_percent DOUBLE PRECISION NOT NULL,
            end_charge_percent DOUBLE PRECISION NOT NULL,
            discharge_delta_percent DOUBLE PRECISION NOT NULL,
            discharged_energy_mwh DOUBLE PRECISION NOT NULL,
            duration_seconds INT NOT NULL,
            avg_load_mw DOUBLE PRECISION,
            status VARCHAR(20) NOT NULL,
            equivalent_cycle_id UUID REFERENCES battery_equivalent_cycles(cycle_id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_user_id ON battery_sessions(user_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_device_id ON battery_sessions(device_id)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_status ON battery_sessions(status)")
    op.execute("CREATE INDEX IF NOT EXISTS idx_sessions_ended_at ON battery_sessions(ended_at_client DESC)")
    op.execute(
        "CREATE INDEX IF NOT EXISTS idx_sessions_equivalent_cycle_id ON battery_sessions(equivalent_cycle_id)"
    )


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_sessions_equivalent_cycle_id")
    op.execute("DROP INDEX IF EXISTS idx_sessions_ended_at")
    op.execute("DROP INDEX IF EXISTS idx_sessions_status")
    op.execute("DROP INDEX IF EXISTS idx_sessions_device_id")
    op.execute("DROP INDEX IF EXISTS idx_sessions_user_id")
    op.execute("DROP TABLE IF EXISTS battery_sessions")

    op.execute("DROP INDEX IF EXISTS idx_equivalent_cycles_ended_at")
    op.execute("DROP INDEX IF EXISTS idx_equivalent_cycles_device_id")
    op.execute("DROP INDEX IF EXISTS idx_equivalent_cycles_user_id")
    op.execute("DROP TABLE IF EXISTS battery_equivalent_cycles")

    op.execute("DROP INDEX IF EXISTS idx_active_sessions_user_id")
    op.execute("DROP TABLE IF EXISTS battery_active_sessions")

    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS baseline_capacity_mwh")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS reference_capacity_source")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS reference_capacity_mwh")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_net_power_mw")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_remaining_capacity_mwh")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_full_charge_capacity_mwh")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_charge_percent")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_is_charging")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_ac_connected")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_sample_seq")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_boot_session_id")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS last_client_time")
    op.execute("ALTER TABLE devices DROP COLUMN IF EXISTS battery_id")
