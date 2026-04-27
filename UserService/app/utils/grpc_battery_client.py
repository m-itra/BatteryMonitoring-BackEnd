import grpc

import battery_data_service_pb2
import battery_data_service_pb2_grpc

from app.config import PROCESSING_SERVICE_GRPC_URL


class BatteryDataCleanupError(Exception):
    pass


async def delete_user_battery_data_via_grpc(user_id: str):
    try:
        async with grpc.aio.insecure_channel(PROCESSING_SERVICE_GRPC_URL) as channel:
            stub = battery_data_service_pb2_grpc.BatteryDataServiceStub(channel)
            request = battery_data_service_pb2.DeleteUserBatteryDataRequest(user_id=user_id)
            response = await stub.DeleteUserBatteryData(request)

        if not response.success:
            raise BatteryDataCleanupError(response.message or "Battery data cleanup failed")

        return response
    except grpc.RpcError as exc:
        raise BatteryDataCleanupError(
            exc.details() or "ProcessingService gRPC request failed"
        ) from exc
