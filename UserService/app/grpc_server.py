import grpc
from concurrent import futures
import user_service_pb2
import user_service_pb2_grpc
from app.db.connection import get_db_connection, get_db_cursor


class UserServiceServicer(user_service_pb2_grpc.UserServiceServicer):
    """Реализация gRPC сервиса для UserService"""

    def GetUser(self, request, context):
        """Получить информацию о пользователе"""
        user_id = request.user_id
        try:
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute(
                        "SELECT user_id, email, name FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    user = cur.fetchone()

                    if not user:
                        context.set_code(grpc.StatusCode.NOT_FOUND)
                        context.set_details(f"User with ID {user_id} not found")
                        return user_service_pb2.UserResponse()

                    return user_service_pb2.UserResponse(
                        user_id=str(user["user_id"]),
                        email=user["email"],
                        name=user["name"]
                    )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {str(e)}")
            return user_service_pb2.UserResponse()

    def ValidateUser(self, request, context):
        """Проверить существование пользователя"""
        user_id = request.user_id

        try:
            with get_db_connection() as conn:
                with get_db_cursor(conn) as cur:
                    cur.execute(
                        "SELECT user_id, name FROM users WHERE user_id = %s",
                        (user_id,)
                    )
                    user = cur.fetchone()

                    if not user:
                        return user_service_pb2.ValidateUserResponse(
                            exists=False,
                            user_id="",
                            name=""
                        )

                    return user_service_pb2.ValidateUserResponse(
                        exists=True,
                        user_id=str(user["user_id"]),
                        name=user["name"]
                    )
        except Exception as e:
            context.set_code(grpc.StatusCode.INTERNAL)
            context.set_details(f"Database error: {str(e)}")
            return user_service_pb2.ValidateUserResponse(exists=False)


def serve():
    """Запуск gRPC сервера"""
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    user_service_pb2_grpc.add_UserServiceServicer_to_server(
        UserServiceServicer(), server
    )
    server.add_insecure_port('[::]:50051')
    server.start()
    print("UserService gRPC Server started on port 50051")
    server.wait_for_termination()


if __name__ == '__main__':
    serve()