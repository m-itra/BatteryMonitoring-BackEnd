from fastapi import APIRouter, HTTPException
from sqlalchemy.exc import IntegrityError

from app.db.connection import get_db_session
from app.db.user_repository import create_user, get_user_by_email
from app.models.user import LoginRequest, RegisterRequest, UserResponse
from app.utils.auth_utils import create_jwt_token, hash_password, verify_password

router = APIRouter()


@router.post("/register", response_model=UserResponse)
async def register(data: RegisterRequest):
    async with get_db_session() as session:
        try:
            if await get_user_by_email(session, data.email):
                raise HTTPException(status_code=400, detail="Email already registered")

            password_hash = hash_password(data.password)
            user = await create_user(session, data.email, data.name, password_hash)
            await session.commit()

            print(f"Registered user: {data.email}")

            return UserResponse(
                user_id=str(user.user_id),
                email=user.email,
                name=user.name,
            )
        except IntegrityError:
            await session.rollback()
            raise HTTPException(status_code=400, detail="Email already registered")
        except HTTPException:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise


@router.post("/login")
async def login(data: LoginRequest):
    async with get_db_session() as session:
        user = await get_user_by_email(session, data.email)

        if not user:
            raise HTTPException(status_code=401, detail="Invalid credentials")

        if not verify_password(data.password, user.password_hash):
            raise HTTPException(status_code=401, detail="Invalid credentials")

        token = create_jwt_token(
            str(user.user_id),
            user.email,
            user.name,
        )

        print(f"Login completed: {data.email}")

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": str(user.user_id),
                "email": user.email,
                "name": user.name,
            },
        }
