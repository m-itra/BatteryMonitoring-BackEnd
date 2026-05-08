from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.models.battery import BatteryLogBatchRequest


def _sample_payload() -> dict:
    return {
        "boot_session_id": str(uuid4()),
        "sample_seq": 1,
        "client_time": "2026-05-08T10:00:00",
        "ac_connected": False,
        "is_charging": False,
        "charge_percent": 55.0,
        "remaining_capacity_mwh": 25000,
        "full_charge_capacity_mwh": 50000,
        "design_capacity_mwh": 52000,
        "voltage_mv": 12000,
        "net_power_mw": 10000,
        "temperature_c": None,
        "status": "discharging",
    }


def test_batch_request_requires_device_name_when_device_id_is_missing():
    with pytest.raises(ValidationError) as exc_info:
        BatteryLogBatchRequest(
            battery_id="battery-1",
            samples=[_sample_payload()],
        )

    assert "device_name is required when device_id is not provided" in str(exc_info.value)


def test_batch_request_accepts_non_positive_reference_capacity_for_system_mode():
    request = BatteryLogBatchRequest(
        device_name="Office Laptop",
        battery_id="battery-1",
        reference_capacity_mwh=0,
        samples=[_sample_payload()],
    )

    assert request.reference_capacity_mwh == 0


def test_batch_request_normalizes_blank_optional_status_to_none():
    sample = _sample_payload()
    sample["status"] = "   "

    request = BatteryLogBatchRequest(
        device_name="Office Laptop",
        battery_id="battery-1",
        samples=[sample],
    )

    assert request.samples[0].status is None
