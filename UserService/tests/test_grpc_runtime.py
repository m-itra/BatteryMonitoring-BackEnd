from unittest.mock import MagicMock, patch

import pytest

from app.grpc_server import _grpc_port_from_target
from app.utils import grpc_battery_client


@pytest.fixture(autouse=True)
def reset_grpc_battery_client_state():
    grpc_battery_client._processing_service_channel = None
    grpc_battery_client._processing_service_stub = None
    grpc_battery_client._processing_service_channel_target = None
    yield
    grpc_battery_client._processing_service_channel = None
    grpc_battery_client._processing_service_stub = None
    grpc_battery_client._processing_service_channel_target = None


def test_grpc_port_from_target_uses_configured_port_and_has_default():
    assert _grpc_port_from_target("user-service:50051") == 50051
    assert _grpc_port_from_target("bad-target") == 50051


def test_processing_service_stub_reuses_cached_channel():
    channel = MagicMock()
    stub = MagicMock()

    with (
        patch(
            "app.utils.grpc_battery_client.grpc.aio.insecure_channel",
            return_value=channel,
        ) as channel_factory,
        patch(
            "app.utils.grpc_battery_client.battery_data_service_pb2_grpc.BatteryDataServiceStub",
            return_value=stub,
        ) as stub_factory,
    ):
        first_stub = grpc_battery_client._get_processing_service_stub()
        second_stub = grpc_battery_client._get_processing_service_stub()

    assert first_stub is stub
    assert second_stub is stub
    channel_factory.assert_called_once_with(grpc_battery_client.PROCESSING_SERVICE_GRPC_URL)
    stub_factory.assert_called_once_with(channel)
