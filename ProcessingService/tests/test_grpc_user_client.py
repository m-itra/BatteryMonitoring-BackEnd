from unittest.mock import MagicMock, patch

import pytest

from app.utils import grpc_user_client


@pytest.fixture(autouse=True)
def reset_grpc_user_client_state():
    grpc_user_client._user_service_channel = None
    grpc_user_client._user_service_stub = None
    grpc_user_client._user_service_channel_target = None
    yield
    grpc_user_client._user_service_channel = None
    grpc_user_client._user_service_stub = None
    grpc_user_client._user_service_channel_target = None


def test_get_user_service_stub_reuses_cached_channel():
    channel = MagicMock()
    stub = MagicMock()

    with (
        patch("app.utils.grpc_user_client.grpc.aio.insecure_channel", return_value=channel) as channel_factory,
        patch("app.utils.grpc_user_client.user_service_pb2_grpc.UserServiceStub", return_value=stub) as stub_factory,
    ):
        first_stub = grpc_user_client._get_user_service_stub()
        second_stub = grpc_user_client._get_user_service_stub()

    assert first_stub is stub
    assert second_stub is stub
    channel_factory.assert_called_once_with(grpc_user_client.USER_SERVICE_GRPC_URL)
    stub_factory.assert_called_once_with(channel)
