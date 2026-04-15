import asyncio

import grpc
import user_service_pb2
import user_service_pb2_grpc

from app.db.connection import get_db_session
from app.db.user_repository import get_user_by_id


async def fetch_user_by_id(user_id: str):
    async with get_db_session() as session:
        return await get_user_by_id(session, user_id)


class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    async def GetUser(self, request, context):
        user_id = request.user_id
        try:
            user = await fetch_user_by_id(user_id)

            if not user:
                context.set_code(grpc.StatusCode.NOT_FOUND)
                context.set_details(f"User with ID {user_id} not found")
                return user_service_pb2.UserResponse()

            return user_service_pb2.UserResponse(
                user_id=str(user.user_id),
                email=user.email,
                name=user.name,
            )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {str(e)}")
            return user_service_pb2.UserResponse()

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
    server.add_insecure_port("[::]:50051")
    await server.start()
    print("UserService gRPC Server started on port 50051")
    await server.wait_for_termination()


def serve():
    asyncio.run(serve_async())


if __name__ == "__main__":
    serve()
