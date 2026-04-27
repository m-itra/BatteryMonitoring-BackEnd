from fastapi import APIRouter, Header, HTTPException
from sqlalchemy.exc import IntegrityError

from app.db.connection import get_db_session
from app.db.models import User
from app.db.user_repository import create_user, delete_user, get_user_by_email, get_user_by_id
from app.models.user import DeleteUserResponse, LoginRequest, RegisterRequest, UserResponse
from app.utils.auth_utils import create_jwt_token, hash_password, verify_password
from app.utils.grpc_battery_client import BatteryDataCleanupError, delete_user_battery_data_via_grpc

router = APIRouter()


async def delete_user_with_battery_cleanup(user: User) -> DeleteUserResponse:
    cleanup_result = await delete_user_battery_data_via_grpc(str(user.user_id))
    return DeleteUserResponse(
        user_id=str(user.user_id),
        deleted_devices=cleanup_result.deleted_devices,
        message="User and battery data deleted",
    )


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
                role=user.role,
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
            user.role,
        )

        print(f"Login completed: {data.email}")

        return {
            "access_token": token,
            "token_type": "bearer",
            "user": {
                "user_id": str(user.user_id),
                "email": user.email,
                "name": user.name,
                "role": user.role,
            },
        }


@router.delete("/users/me", response_model=DeleteUserResponse)
async def delete_current_user(
    x_user_id: str = Header(..., description="User ID from Gateway"),
):
    async with get_db_session() as session:
        try:
            user = await get_user_by_id(session, x_user_id)
            if not user:
                raise HTTPException(status_code=404, detail="User not found")

            response_payload = await delete_user_with_battery_cleanup(user)
            await delete_user(session, user)
            await session.commit()

            return response_payload
        except BatteryDataCleanupError as exc:
            await session.rollback()
            raise HTTPException(status_code=502, detail=str(exc))
        except HTTPException:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise
