from datetime import datetime
from uuid import uuid4

from app.db.device import update_device_reference_capacity, update_device_snapshot
from app.db.models import Device
from app.models.battery import BatterySample


def test_non_positive_reference_capacity_switches_device_back_to_design_mode():
    device = Device(
        device_id=uuid4(),
        user_id=uuid4(),
        reference_capacity_mwh=40000,
        reference_capacity_source="user",
    )

    update_device_reference_capacity(
        device,
        requested_reference_capacity_mwh=0,
        design_capacity_mwh=52000,
        full_charge_capacity_mwh=50000,
    )

    assert device.reference_capacity_mwh == 52000
    assert device.reference_capacity_source == "design"


def test_update_device_snapshot_stores_last_design_capacity():
    device = Device(
        device_id=uuid4(),
        user_id=uuid4(),
    )
    sample = BatterySample(
        boot_session_id=uuid4(),
        sample_seq=1,
        client_time=datetime.fromisoformat("2026-05-07T12:00:00"),
        ac_connected=False,
        is_charging=False,
        charge_percent=55.0,
        remaining_capacity_mwh=25000,
        full_charge_capacity_mwh=50000,
        design_capacity_mwh=52000,
        voltage_mv=12000,
        net_power_mw=10000,
        temperature_c=None,
        status="discharging",
    )

    update_device_snapshot(
        device,
        sample=sample,
        received_at=datetime.fromisoformat("2026-05-07T12:00:05"),
        battery_id="battery-1",
        requested_reference_capacity_mwh=None,
    )

    assert device.last_design_capacity_mwh == 52000
    assert device.reference_capacity_mwh == 52000
    assert device.reference_capacity_source == "design"
