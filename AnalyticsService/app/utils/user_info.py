import grpc
import user_service_pb2
import user_service_pb2_grpc
from app.config import USER_SERVICE_GRPC_URL


async def get_user_info(user_id: str) -> dict:
    """
    Получение информации о пользователе через gRPC

    Пример использования:
    user = await get_user_info("123e4567-e89b-12d3-a456-426614174000")
    """
    try:
        # Создаём gRPC канал
        async with grpc.aio.insecure_channel(USER_SERVICE_GRPC_URL) as channel:
            stub = user_service_pb2_grpc.UserServiceStub(channel)

            # Создаём запрос
            request = user_service_pb2.GetUserRequest(user_id=user_id)

            # Выполняем gRPC вызов
            response = await stub.GetUser(request)

            return {
                "user_id": response.user_id,
                "name": response.name,
                "email": response.email
            }

    except grpc.RpcError as e:
        print(f"gRPC Error fetching user info for user_id {user_id}: {e.code()} - {e.details()}")
        return {"name": "Unknown User", "email": "", "user_id": user_id}
    except Exception as e:
        print(f"Error fetching user info for user_id {user_id}: {e}")
        return {"name": "Unknown User", "email": "", "user_id": user_id}