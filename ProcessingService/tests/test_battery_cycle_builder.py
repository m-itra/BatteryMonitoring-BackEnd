import asyncio
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

from sqlalchemy.dialects import postgresql

from app.db.models import BatteryEquivalentCycle, BatterySession, Device
from app.services.battery_cycle_builder import (
    ELIGIBLE_CYCLE_SESSION_STATUSES,
    create_equivalent_cycles,
)


def _scalar_result(items):
    result = MagicMock()
    result.scalars.return_value.all.return_value = items
    return result


def test_create_equivalent_cycles_queries_completed_and_interrupted_sessions():
    device = Device(
        device_id=uuid4(),
        user_id=uuid4(),
        reference_capacity_mwh=40000,
    )
    session = SimpleNamespace(
        execute=AsyncMock(side_effect=[_scalar_result([])]),
        add=MagicMock(),
        flush=AsyncMock(),
    )

    asyncio.run(create_equivalent_cycles(session, device))

    statement = session.execute.await_args_list[0].args[0]
    compiled = str(
        statement.compile(
            dialect=postgresql.dialect(),
            compile_kwargs={"literal_binds": True},
        )
    )

    for status in ELIGIBLE_CYCLE_SESSION_STATUSES:
        assert status in compiled


def test_interrupted_session_can_form_equivalent_cycle():
    device_id = uuid4()
    user_id = uuid4()
    started_at = datetime.fromisoformat("2026-05-07T10:00:00")
    ended_at = datetime.fromisoformat("2026-05-07T12:00:00")

    device = Device(
        device_id=device_id,
        user_id=user_id,
        reference_capacity_mwh=40000,
        last_full_charge_capacity_mwh=38000,
    )
    interrupted_session = BatterySession(
        session_id=uuid4(),
        device_id=device_id,
        user_id=user_id,
        boot_session_id=uuid4(),
        started_at_client=started_at,
        ended_at_client=ended_at,
        started_at_server=started_at,
        ended_at_server=ended_at,
        start_charge_percent=80.0,
        end_charge_percent=0.0,
        discharge_delta_percent=100.0,
        discharged_energy_mwh=36000.0,
        duration_seconds=7200.0,
        avg_load_mw=18000.0,
        status="interrupted",
    )

    session = SimpleNamespace(
        execute=AsyncMock(
            side_effect=[
                _scalar_result([interrupted_session]),
                _scalar_result([]),
            ]
        ),
        add=MagicMock(),
        flush=AsyncMock(),
    )

    created_cycles = asyncio.run(create_equivalent_cycles(session, device))

    assert created_cycles == 1
    added_cycle = session.add.call_args.args[0]
    assert isinstance(added_cycle, BatteryEquivalentCycle)
    assert added_cycle.session_count == 1
    assert added_cycle.total_discharge_percent == 100.0
    assert added_cycle.total_energy_mwh == 36000.0
    assert added_cycle.total_duration_seconds == 7200.0

