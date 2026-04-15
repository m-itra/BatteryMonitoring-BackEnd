from typing import Optional

from fastapi import APIRouter, Header, Query
from sqlalchemy import select

from app.db.connection import get_db_session
from app.db.models import BatteryCycle
from app.db.query_helpers import parse_uuid_or_400
from app.models import CycleInfo

router = APIRouter()


@router.get("/cycles")
async def get_cycles(
        x_user_id: str = Header(...),
        device_id: Optional[str] = Query(default=None, min_length=1),
        limit: int = Query(default=50, ge=1, le=200)
):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    statement = (
        select(BatteryCycle)
        .where(BatteryCycle.user_id == user_id)
        .order_by(BatteryCycle.completed_at.desc())
        .limit(limit)
    )

    if device_id:
        statement = statement.where(BatteryCycle.device_id == parse_uuid_or_400(device_id, "device_id"))

    async with get_db_session() as session:
        result = await session.execute(statement)
        cycles = result.scalars().all()

        return {
            "cycles": [
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
            ]
        }
