import grpc
import user_service_pb2
import user_service_pb2_grpc
from app.config import USER_SERVICE_GRPC_URL


async def validate_user_via_grpc(user_id: str) -> dict:
    """
    Проверка существования пользователя через gRPC

    Returns:
        dict: {"exists": bool, "user_id": str, "name": str}

    Пример использования:
    result = await validate_user_via_grpc("123e4567-e89b-12d3-a456-426614174000")
    if not result["exists"]:
        raise HTTPException(status_code=404, detail="User not found")
    """
    try:
        # Создаём gRPC канал
        async with grpc.aio.insecure_channel(USER_SERVICE_GRPC_URL) as channel:
            stub = user_service_pb2_grpc.UserServiceStub(channel)

            # Создаём запрос
            request = user_service_pb2.ValidateUserRequest(user_id=user_id)

            # Выполняем gRPC вызов
            response = await stub.ValidateUser(request)

            return {
                "exists": response.exists,
                "user_id": response.user_id,
                "name": response.name
            }

    except grpc.RpcError as e:
        print(f"gRPC Error validating user {user_id}: {e.code()} - {e.details()}")
        return {"exists": False, "user_id": "", "name": ""}
    except Exception as e:
        print(f"Error validating user {user_id}: {e}")
        return {"exists": False, "user_id": "", "name": ""}