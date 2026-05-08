from datetime import datetime
from uuid import uuid4

from app.db.models import Device
from app.models.battery import BatterySample
from app.services.battery_math import (
    avg_load_mw,
    integrate_discharge,
    is_duplicate_sample,
    order_samples,
)


def test_integrate_discharge_preserves_subsecond_intervals():
    previous = datetime.fromisoformat("2026-05-05T20:48:44.285")
    current = datetime.fromisoformat("2026-05-05T20:48:45.150")

    energy_mwh, duration_seconds = integrate_discharge(previous, 10000, current)

    assert duration_seconds == 0.865
    assert round(energy_mwh, 4) == round(10000 * (0.865 / 3600), 4)


def test_avg_load_uses_fractional_duration_seconds():
    load = avg_load_mw(12.5, 0.75)

    assert round(load or 0.0, 4) == 60000.0


def test_order_samples_sorts_by_client_time_then_sample_seq():
    boot_session_id = uuid4()
    samples = [
        BatterySample(
            boot_session_id=boot_session_id,
            sample_seq=3,
            client_time=datetime.fromisoformat("2026-05-08T10:00:01"),
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
        ),
        BatterySample(
            boot_session_id=boot_session_id,
            sample_seq=1,
            client_time=datetime.fromisoformat("2026-05-08T10:00:00"),
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
        ),
        BatterySample(
            boot_session_id=boot_session_id,
            sample_seq=2,
            client_time=datetime.fromisoformat("2026-05-08T10:00:01"),
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
        ),
    ]

    ordered = order_samples(samples)

    assert [sample.sample_seq for sample in ordered] == [1, 2, 3]


def test_is_duplicate_sample_checks_boot_session_id_and_sequence():
    boot_session_id = uuid4()
    device = Device(
        device_id=uuid4(),
        user_id=uuid4(),
        last_boot_session_id=boot_session_id,
        last_sample_seq=10,
    )
    duplicate_sample = BatterySample(
        boot_session_id=boot_session_id,
        sample_seq=10,
        client_time=datetime.fromisoformat("2026-05-08T10:00:01"),
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
    new_boot_sample = BatterySample(
        boot_session_id=uuid4(),
        sample_seq=1,
        client_time=datetime.fromisoformat("2026-05-08T10:00:02"),
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

    assert is_duplicate_sample(device, duplicate_sample) is True
    assert is_duplicate_sample(device, new_boot_sample) is False
