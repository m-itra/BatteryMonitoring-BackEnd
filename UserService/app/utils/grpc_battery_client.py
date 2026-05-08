import threading

import grpc

import battery_data_service_pb2
import battery_data_service_pb2_grpc

from app.config import PROCESSING_SERVICE_GRPC_URL

_channel_lock = threading.Lock()
_processing_service_channel: grpc.aio.Channel | None = None
_processing_service_stub: battery_data_service_pb2_grpc.BatteryDataServiceStub | None = None
_processing_service_channel_target: str | None = None


class BatteryDataCleanupError(Exception):
    pass


def _get_processing_service_stub() -> battery_data_service_pb2_grpc.BatteryDataServiceStub:
    global _processing_service_channel
    global _processing_service_stub
    global _processing_service_channel_target

    if (
        _processing_service_stub is not None
        and _processing_service_channel is not None
        and _processing_service_channel_target == PROCESSING_SERVICE_GRPC_URL
    ):
        return _processing_service_stub

    with _channel_lock:
        if (
            _processing_service_stub is None
            or _processing_service_channel is None
            or _processing_service_channel_target != PROCESSING_SERVICE_GRPC_URL
        ):
            _processing_service_channel = grpc.aio.insecure_channel(PROCESSING_SERVICE_GRPC_URL)
            _processing_service_stub = battery_data_service_pb2_grpc.BatteryDataServiceStub(
                _processing_service_channel
            )
            _processing_service_channel_target = PROCESSING_SERVICE_GRPC_URL

    return _processing_service_stub


async def close_processing_service_grpc_channel() -> None:
    global _processing_service_channel
    global _processing_service_stub
    global _processing_service_channel_target

    channel = _processing_service_channel
    _processing_service_channel = None
    _processing_service_stub = None
    _processing_service_channel_target = None

    if channel is not None:
        await channel.close()


async def delete_user_battery_data_via_grpc(user_id: str):
    try:
        stub = _get_processing_service_stub()
        request = battery_data_service_pb2.DeleteUserBatteryDataRequest(user_id=user_id)
        response = await stub.DeleteUserBatteryData(request)

        if not response.success:
            raise BatteryDataCleanupError(response.message or "Battery data cleanup failed")

        return response
    except grpc.RpcError as exc:
        raise BatteryDataCleanupError(
            exc.details() or "ProcessingService gRPC request failed"
        ) from exc
