from fastapi import APIRouter, HTTPException
from sqlalchemy import func, select

from app.db.connection import get_db_session
from app.db.models import User
from app.db.user_repository import delete_user, get_user_by_id, list_users
from app.models.user import AdminUserInfo, AdminUserStatsResponse, AdminUsersResponse
from app.routes.auth import delete_user_with_battery_cleanup
from app.utils.grpc_battery_client import BatteryDataCleanupError

router = APIRouter()


@router.get("/admin/users", response_model=AdminUsersResponse)
async def get_admin_users():
    async with get_db_session() as session:
        users = await list_users(session)
        return AdminUsersResponse(
            users=[
                AdminUserInfo(
                    user_id=str(user.user_id),
                    email=user.email,
                    name=user.name,
                    role=user.role,
                    created_at=user.created_at,
                )
                for user in users
            ]
        )


@router.get("/admin/stats", response_model=AdminUserStatsResponse)
async def get_admin_user_stats():
    async with get_db_session() as session:
        result = await session.execute(select(func.count(User.user_id)))
        users_count = result.scalar_one()
        return AdminUserStatsResponse(users_count=users_count)


@router.delete("/admin/users/{user_id}")
async def delete_user_as_admin(user_id: str):
    async with get_db_session() as session:
        try:
            user = await get_user_by_id(session, user_id)
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
