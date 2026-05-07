import asyncio
from datetime import datetime, timedelta
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from app.db.models import BatteryActiveSession, Device
from app.models.battery import BatterySample
from app.services.battery_session_flow import interrupt_stale_session_if_needed


def test_interrupt_stale_session_attempts_cycle_build_for_persisted_session():
    device = Device(
        device_id=uuid4(),
        user_id=uuid4(),
        reference_capacity_mwh=40000,
    )
    active_session = BatteryActiveSession(
        device_id=device.device_id,
        user_id=device.user_id,
        boot_session_id=uuid4(),
        started_at_client=datetime.fromisoformat("2026-05-07T10:00:00"),
        started_at_server=datetime.fromisoformat("2026-05-07T10:00:00"),
        last_client_time=datetime.fromisoformat("2026-05-07T10:05:00"),
        last_server_received_at=datetime.fromisoformat("2026-05-07T10:05:00"),
        last_sample_seq=42,
        start_charge_percent=80.0,
        current_charge_percent=55.0,
        discharged_energy_mwh=9000.0,
        duration_seconds=300.0,
        pending_transition="none",
    )
    sample = BatterySample(
        boot_session_id=active_session.boot_session_id,
        sample_seq=43,
        client_time=active_session.last_client_time + timedelta(seconds=121),
        ac_connected=False,
        is_charging=False,
        charge_percent=54.8,
        remaining_capacity_mwh=20000,
        full_charge_capacity_mwh=40000,
        design_capacity_mwh=42000,
        voltage_mv=12000,
        net_power_mw=10000,
        temperature_c=None,
        status="discharging",
    )
    saved_session = SimpleNamespace(session_id=uuid4())

    with (
        patch(
            "app.services.battery_session_flow.close_active_session",
            new=AsyncMock(return_value=saved_session),
        ) as close_mock,
        patch(
            "app.services.battery_session_flow.create_equivalent_cycles",
            new=AsyncMock(return_value=1),
        ) as cycle_mock,
    ):
        next_active_session, completed_cycles = asyncio.run(
            interrupt_stale_session_if_needed(
                session=SimpleNamespace(),
                active_session=active_session,
                device=device,
                received_at=datetime.fromisoformat("2026-05-07T10:07:10"),
                sample=sample,
            )
        )

    assert next_active_session is None
    assert completed_cycles == 1
    close_mock.assert_awaited_once()
    cycle_mock.assert_awaited_once()
