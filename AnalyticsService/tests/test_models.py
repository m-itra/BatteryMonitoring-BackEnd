import pytest
from pydantic import ValidationError

from app.models import UpdateDeviceRequest


def test_update_device_request_accepts_reference_capacity_without_device_name():
    request = UpdateDeviceRequest(reference_capacity_mwh=0)

    assert request.reference_capacity_mwh == 0
    assert request.device_name is None


def test_update_device_request_requires_at_least_one_mutation_field():
    with pytest.raises(ValidationError) as exc_info:
        UpdateDeviceRequest()

    assert "device_name or reference_capacity_mwh is required" in str(exc_info.value)
