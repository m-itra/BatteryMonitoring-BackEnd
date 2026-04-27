import asyncio

import battery_data_service_pb2
import battery_data_service_pb2_grpc
import grpc

from app.config import PROCESSING_SERVICE_GRPC_URL
from app.db.connection import get_db_session
from app.db.device import delete_devices_by_user_id, parse_uuid


def _grpc_port_from_target(target: str) -> int:
    try:
        return int(target.rsplit(":", 1)[1])
    except (IndexError, ValueError):
        return 50052


class BatteryDataServiceServicer(battery_data_service_pb2_grpc.BatteryDataServiceServicer):
    async def DeleteUserBatteryData(self, request, context):
        user_id = request.user_id
        if parse_uuid(user_id) is None:
            context.set_code(grpc.StatusCode.INVALID_ARGUMENT)
            context.set_details("Invalid user_id")
            return battery_data_service_pb2.DeleteUserBatteryDataResponse(
                success=False,
                deleted_devices=0,
                message="Invalid user_id",
            )

        async with get_db_session() as session:
            try:
                deleted_devices = await delete_devices_by_user_id(session, user_id)
                await session.commit()
                message = (
                    f"Deleted {deleted_devices} device(s)"
                    if deleted_devices
                    else "No battery data found"
                )
                return battery_data_service_pb2.DeleteUserBatteryDataResponse(
                    success=True,
                    deleted_devices=deleted_devices,
                    message=message,
                )
            except Exception as exc:
                await session.rollback()
                context.set_code(grpc.StatusCode.INTERNAL)
                context.set_details(f"Database error: {str(exc)}")
                return battery_data_service_pb2.DeleteUserBatteryDataResponse(
                    success=False,
                    deleted_devices=0,
                    message="Failed to delete battery data",
                )


async def serve_async():
    server = grpc.aio.server()
    battery_data_service_pb2_grpc.add_BatteryDataServiceServicer_to_server(
        BatteryDataServiceServicer(),
        server,
    )
    grpc_port = _grpc_port_from_target(PROCESSING_SERVICE_GRPC_URL)
    server.add_insecure_port(f"[::]:{grpc_port}")
    await server.start()
    print(f"ProcessingService gRPC Server started on port {grpc_port}")
    await server.wait_for_termination()


def serve():
    asyncio.run(serve_async())
