from datetime import datetime
from uuid import uuid4

from app.db.models import BatteryEquivalentCycle
from app.db.query_helpers import build_capacity_history_point, build_cycle_info


def _make_cycle() -> BatteryEquivalentCycle:
    now = datetime.fromisoformat("2026-05-07T12:00:00")
    return BatteryEquivalentCycle(
        cycle_id=uuid4(),
        device_id=uuid4(),
        user_id=uuid4(),
        started_at_client=now,
        ended_at_client=now,
        session_count=1,
        total_discharge_percent=100.0,
        total_energy_mwh=36000.0,
        total_duration_seconds=7200.0,
        avg_load_mw=18000.0,
        reference_capacity_mwh_used=40000,
        full_charge_capacity_mwh_at_cycle_end=38000,
        soh_capacity_percent=95.0,
        degradation_capacity_percent=5.0,
        soh_energy_percent=90.0,
        degradation_energy_percent=10.0,
        is_excluded=False,
        created_at=now,
    )


def test_build_cycle_info_uses_current_reference_capacity_when_present():
    cycle = _make_cycle()

    info = build_cycle_info(cycle, current_reference_capacity_mwh=50000)

    assert info.soh_capacity_percent == 76.0
    assert info.degradation_capacity_percent == 24.0
    assert info.soh_energy_percent == 72.0
    assert info.degradation_energy_percent == 28.0


def test_build_capacity_history_point_exposes_raw_values_for_frontend_recalculation():
    cycle = _make_cycle()

    point = build_capacity_history_point(cycle, current_reference_capacity_mwh=50000)

    assert point.full_charge_capacity_mwh == 38000
    assert point.total_energy_mwh == 36000.0
    assert point.reference_capacity_mwh_used == 40000
    assert point.soh_capacity_percent == 76.0
    assert point.soh_energy_percent == 72.0
