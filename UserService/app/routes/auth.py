from app.models.user import UserResponse, RegisterRequest, LoginRequest
from app.db.connection import get_db_cursor, get_db_connection
from app.utils.auth_utils import hash_password, verify_password, create_jwt_token
from fastapi import HTTPException, APIRouter


router = APIRouter()

@router.post("/register", response_model=UserResponse)
def register(data: RegisterRequest):
    """Регистрация нового пользователя"""

    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            # Проверка существования email
            cur.execute("SELECT email FROM users WHERE email = %s", (data.email,))
            if cur.fetchone():
                raise HTTPException(status_code=400, detail="Email already registered")

            # Хеширование пароля
            password_hash = hash_password(data.password)

            # Создание пользователя
            cur.execute(
                """
                INSERT INTO users (email, name, password_hash)
                VALUES (%s, %s, %s)
                RETURNING user_id, email, name
                """,
                (data.email, data.name, password_hash)
            )

            user = cur.fetchone()
            conn.commit()

            print(f"Зарегистрирован пользователь: {data.email}")

            return UserResponse(
                user_id=str(user['user_id']),
                email=user['email'],
                name=user['name']
            )

@router.post("/login")
def login(data: LoginRequest):
    """Вход пользователя и получение JWT токена"""

    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            # Поиск пользователя
            cur.execute(
                "SELECT user_id, email, name, password_hash FROM users WHERE email = %s",
                (data.email,)
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Проверка пароля
            if not verify_password(data.password, user['password_hash']):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            # Генерация JWT
            token = create_jwt_token(
                str(user['user_id']),
                user['email'],
                user['name']
            )

            print(f"Вход выполнен: {data.email}")

            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "user_id": str(user['user_id']),
                    "email": user['email'],
                    "name": user['name']
                }
            }