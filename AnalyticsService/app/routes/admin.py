from fastapi import APIRouter
from sqlalchemy import func, select

from app.db.connection import get_db_session
from app.db.models import BatteryActiveSession, BatteryEquivalentCycle, BatterySession, Device
from app.models import AdminBatteryStatsResponse

router = APIRouter()


@router.get("/admin/stats", response_model=AdminBatteryStatsResponse)
async def get_admin_battery_stats():
    async with get_db_session() as session:
        devices_count = (
            await session.execute(select(func.count(Device.device_id)))
        ).scalar_one()
        active_sessions_count = (
            await session.execute(select(func.count(BatteryActiveSession.device_id)))
        ).scalar_one()
        completed_sessions_count = (
            await session.execute(
                select(func.count(BatterySession.session_id)).where(BatterySession.status == "completed")
            )
        ).scalar_one()
        interrupted_sessions_count = (
            await session.execute(
                select(func.count(BatterySession.session_id)).where(BatterySession.status == "interrupted")
            )
        ).scalar_one()
        equivalent_cycles_count = (
            await session.execute(select(func.count(BatteryEquivalentCycle.cycle_id)))
        ).scalar_one()
        excluded_cycles_count = (
            await session.execute(
                select(func.count(BatteryEquivalentCycle.cycle_id)).where(
                    BatteryEquivalentCycle.is_excluded.is_(True)
                )
            )
        ).scalar_one()

        return AdminBatteryStatsResponse(
            devices_count=devices_count,
            active_sessions_count=active_sessions_count,
            completed_sessions_count=completed_sessions_count,
            interrupted_sessions_count=interrupted_sessions_count,
            equivalent_cycles_count=equivalent_cycles_count,
            excluded_cycles_count=excluded_cycles_count,
        )
