from fastapi import APIRouter, HTTPException

from app.db.connection import get_db_connection, get_db_cursor
from app.models.user import LoginRequest, RegisterRequest, UserResponse
from app.utils.auth_utils import create_jwt_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=UserResponse)
def register(data: RegisterRequest):
    with get_db_connection() as conn:
        try:
            with get_db_cursor(conn) as cur:
                cur.execute("SELECT email FROM users WHERE email = %s", (data.email,))
                if cur.fetchone():
                    raise HTTPException(status_code=400, detail="Email already registered")

                password_hash = hash_password(data.password)

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

                print(f"Registered user: {data.email}")

                return UserResponse(
                    user_id=str(user["user_id"]),
                    email=user["email"],
                    name=user["name"]
                )
        except Exception:
            conn.rollback()
            raise


@router.post("/login")
def login(data: LoginRequest):
    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            cur.execute(
                "SELECT user_id, email, name, password_hash FROM users WHERE email = %s",
                (data.email,)
            )
            user = cur.fetchone()

            if not user:
                raise HTTPException(status_code=401, detail="Invalid credentials")

            if not verify_password(data.password, user["password_hash"]):
                raise HTTPException(status_code=401, detail="Invalid credentials")

            token = create_jwt_token(
                str(user["user_id"]),
                user["email"],
                user["name"]
            )

            print(f"Login completed: {data.email}")

            return {
                "access_token": token,
                "token_type": "bearer",
                "user": {
                    "user_id": str(user["user_id"]),
                    "email": user["email"],
                    "name": user["name"]
                }
            }
