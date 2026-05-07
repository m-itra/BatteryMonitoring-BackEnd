from fastapi import APIRouter, Header
from sqlalchemy import func, select

from app.db.connection import get_db_session
from app.db.models import BatteryEquivalentCycle, Device
from app.db.query_helpers import build_cycle_info, build_device_info, device_summary_statement, parse_uuid_or_400
from app.models import AnalyticsDataResponse

router = APIRouter()


@router.get("/analytics", response_model=AnalyticsDataResponse)
async def get_full_analytics(x_user_id: str = Header(..., alias="X-User-Id")):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    async with get_db_session() as session:
        devices_result = await session.execute(device_summary_statement(user_id))
        devices = devices_result.mappings().all()

        cycles_result = await session.execute(
            select(BatteryEquivalentCycle, Device.reference_capacity_mwh)
            .join(Device, Device.device_id == BatteryEquivalentCycle.device_id)
            .where(BatteryEquivalentCycle.user_id == user_id)
            .order_by(BatteryEquivalentCycle.ended_at_client.desc())
            .limit(20)
        )
        cycle_rows = cycles_result.all()

        total_cycles_result = await session.execute(
            select(func.count(BatteryEquivalentCycle.cycle_id))
            .where(
                BatteryEquivalentCycle.user_id == user_id,
                BatteryEquivalentCycle.is_excluded.is_(False),
            )
        )
        total_cycles = total_cycles_result.scalar_one()

        return AnalyticsDataResponse(
            devices=[build_device_info(device) for device in devices],
            recent_cycles=[
                build_cycle_info(cycle, reference_capacity_mwh)
                for cycle, reference_capacity_mwh in cycle_rows
            ],
            total_cycles=total_cycles,
        )
