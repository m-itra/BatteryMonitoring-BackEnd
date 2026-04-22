from typing import Optional

from fastapi import APIRouter, Header, Query
from sqlalchemy import select

from app.db.connection import get_db_session
from app.db.models import BatteryEquivalentCycle
from app.db.query_helpers import build_cycle_info, parse_uuid_or_400

router = APIRouter()


@router.get("/cycles")
async def get_cycles(
    x_user_id: str = Header(..., alias="X-User-Id"),
    device_id: Optional[str] = Query(default=None, min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    statement = (
        select(BatteryEquivalentCycle)
        .where(BatteryEquivalentCycle.user_id == user_id)
        .order_by(BatteryEquivalentCycle.ended_at_client.desc())
        .limit(limit)
    )

    if device_id:
        statement = statement.where(
            BatteryEquivalentCycle.device_id == parse_uuid_or_400(device_id, "device_id")
        )

    async with get_db_session() as session:
        result = await session.execute(statement)
        cycles = result.scalars().all()

        return {
            "cycles": [build_cycle_info(cycle) for cycle in cycles]
        }
