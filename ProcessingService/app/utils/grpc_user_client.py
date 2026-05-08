import threading

import grpc

import user_service_pb2
import user_service_pb2_grpc

from app.config import USER_SERVICE_GRPC_URL

_channel_lock = threading.Lock()
_user_service_channel: grpc.aio.Channel | None = None
_user_service_stub: user_service_pb2_grpc.UserServiceStub | None = None
_user_service_channel_target: str | None = None


def _get_user_service_stub() -> user_service_pb2_grpc.UserServiceStub:
    global _user_service_channel
    global _user_service_stub
    global _user_service_channel_target

    if (
        _user_service_stub is not None
        and _user_service_channel is not None
        and _user_service_channel_target == USER_SERVICE_GRPC_URL
    ):
        return _user_service_stub

    with _channel_lock:
        if (
            _user_service_stub is None
            or _user_service_channel is None
            or _user_service_channel_target != USER_SERVICE_GRPC_URL
        ):
            _user_service_channel = grpc.aio.insecure_channel(USER_SERVICE_GRPC_URL)
            _user_service_stub = user_service_pb2_grpc.UserServiceStub(_user_service_channel)
            _user_service_channel_target = USER_SERVICE_GRPC_URL

    return _user_service_stub


async def close_user_service_grpc_channel() -> None:
    global _user_service_channel
    global _user_service_stub
    global _user_service_channel_target

    channel = _user_service_channel
    _user_service_channel = None
    _user_service_stub = None
    _user_service_channel_target = None

    if channel is not None:
        await channel.close()


async def validate_user_via_grpc(user_id: str) -> dict:
    try:
        stub = _get_user_service_stub()
        request = user_service_pb2.ValidateUserRequest(user_id=user_id)
        response = await stub.ValidateUser(request)

        return {
            "exists": response.exists,
            "user_id": response.user_id,
            "name": response.name,
        }
    except grpc.RpcError as exc:
        print(f"gRPC Error validating user {user_id}: {exc.code()} - {exc.details()}")
        return {"exists": False, "user_id": "", "name": ""}
    except Exception as exc:
        print(f"Error validating user {user_id}: {exc}")
        return {"exists": False, "user_id": "", "name": ""}
