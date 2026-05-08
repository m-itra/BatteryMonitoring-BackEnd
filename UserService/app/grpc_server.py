import asyncio

import grpc
import user_service_pb2
import user_service_pb2_grpc

from app.config import USER_SERVICE_GRPC_URL
from app.db.connection import get_db_session
from app.db.user_repository import get_user_by_id


def _grpc_port_from_target(target: str) -> int:
    try:
        return int(target.rsplit(":", 1)[1])
    except (IndexError, ValueError):
        return 50051


async def fetch_user_by_id(user_id: str):
    async with get_db_session() as session:
        return await get_user_by_id(session, user_id)


class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    async def ValidateUser(self, request, context):
        user_id = request.user_id

        try:
            user = await fetch_user_by_id(user_id)

            if not user:
                return user_service_pb2.ValidateUserResponse(
                    exists=False,
                    user_id="",
                    name="",
                )

            return user_service_pb2.ValidateUserResponse(
                exists=True,
                user_id=str(user.user_id),
                name=user.name,
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {str(e)}")
            return user_service_pb2.ValidateUserResponse(exists=False)


async def serve_async():
    server = grpc.aio.server()
    user_service_pb2_grpc.add_UserServiceServicer_to_server(
        UserServiceServicer(), server
    )
    grpc_port = _grpc_port_from_target(USER_SERVICE_GRPC_URL)
    server.add_insecure_port(f"[::]:{grpc_port}")
    await server.start()
    print(f"UserService gRPC Server started on port {grpc_port}")
    await server.wait_for_termination()


def serve():
    asyncio.run(serve_async())


if __name__ == "__main__":
    serve()
