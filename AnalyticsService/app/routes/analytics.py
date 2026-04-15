from fastapi import APIRouter, Header
from sqlalchemy import func, select

from app.db.connection import get_db_session
from app.db.models import BatteryCycle
from app.db.query_helpers import device_summary_statement, parse_uuid_or_400
from app.models import AnalyticsResponse, CycleInfo, DeviceInfo
from app.utils.user_info import get_user_info

router = APIRouter()


@router.get("/analytics")
async def get_full_analytics(x_user_id: str = Header(..., alias="X-User-Id")):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")
    user_info = await get_user_info(x_user_id)

    async with get_db_session() as session:
        devices_result = await session.execute(device_summary_statement(user_id))
        devices = devices_result.mappings().all()

        cycles_result = await session.execute(
            select(BatteryCycle)
            .where(BatteryCycle.user_id == user_id)
            .order_by(BatteryCycle.completed_at.desc())
            .limit(20)
        )
        cycles = cycles_result.scalars().all()

        total_cycles_result = await session.execute(
            select(func.count(BatteryCycle.cycle_id)).where(BatteryCycle.user_id == user_id)
        )
        total_cycles = total_cycles_result.scalar_one()

        return AnalyticsResponse(
            user=user_info,
            devices=[
                DeviceInfo(
                    device_id=str(device["device_id"]),
                    device_name=device["device_name"],
                    created_at=device["created_at"],
                    last_seen=device["last_seen"],
                    total_cycles=device["total_cycles"],
                    last_health_score=device["last_health_score"],
                )
                for device in devices
            ],
            recent_cycles=[
                CycleInfo(
                    cycle_id=str(cycle.cycle_id),
                    device_id=str(cycle.device_id),
                    started_at=cycle.started_at,
                    completed_at=cycle.completed_at,
                    duration_minutes=cycle.duration_minutes,
                    health_score=cycle.health_score,
                    capacity_degradation=cycle.capacity_degradation,
                    cycle_count=cycle.cycle_count,
                    charge_cycles_equivalent=cycle.charge_cycles_equivalent,
                    min_level=cycle.min_level,
                    max_level=cycle.max_level,
                    avg_discharge_rate=cycle.avg_discharge_rate,
                    avg_charge_rate=cycle.avg_charge_rate,
                )
                for cycle in cycles
            ],
            total_cycles=total_cycles
        )
