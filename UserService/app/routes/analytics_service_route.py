from app.db.connection import get_db_connection
from app.db.connection import get_db_cursor

from fastapi import HTTPException, APIRouter
from app.models.user import UserResponse

from fastapi import Path

router = APIRouter()


@router.get("/internal/user/{user_id}", response_model=UserResponse)
def get_user_by_id(user_id: str = Path(..., description="ID пользователя")):
    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            cur.execute(
                "SELECT user_id, email, name FROM users WHERE user_id = %s",
                (user_id,)
            )
            user = cur.fetchone()
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            return UserResponse(
                user_id=str(user["user_id"]),
                email=user["email"],
                name=user["name"]
            )
