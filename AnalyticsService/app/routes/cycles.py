from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Header, HTTPException, Query
from sqlalchemy import func, select

from app.db.connection import get_db_session
from app.db.models import BatteryEquivalentCycle, BatterySession
from app.db.query_helpers import build_cycle_info, parse_uuid_or_400
from app.models import CycleDeletionResponse, CycleExclusionResponse

router = APIRouter()


@router.get("/cycles")
async def get_cycles(
    x_user_id: str = Header(..., alias="X-User-Id"),
    device_id: Optional[str] = Query(default=None, min_length=1),
    limit: int = Query(default=50, ge=1, le=200),
    include_excluded: bool = Query(default=True),
):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")

    statement = (
        select(BatteryEquivalentCycle)
        .where(BatteryEquivalentCycle.user_id == user_id)
        .order_by(BatteryEquivalentCycle.ended_at_client.desc())
        .limit(limit)
    )

    if not include_excluded:
        statement = statement.where(BatteryEquivalentCycle.is_excluded.is_(False))

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


def _set_cycle_excluded(cycle: BatteryEquivalentCycle, *, excluded: bool) -> None:
    cycle.is_excluded = excluded
    cycle.excluded_at = datetime.now() if excluded else None


@router.post(
    "/devices/{device_id}/cycles/{cycle_id}/exclude",
    response_model=CycleExclusionResponse,
)
async def exclude_cycle(
    device_id: str,
    cycle_id: str,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")
    parsed_device_id = parse_uuid_or_400(device_id, "device_id")
    parsed_cycle_id = parse_uuid_or_400(cycle_id, "cycle_id")

    async with get_db_session() as session:
        try:
            result = await session.execute(
                select(BatteryEquivalentCycle)
                .where(
                    BatteryEquivalentCycle.cycle_id == parsed_cycle_id,
                    BatteryEquivalentCycle.device_id == parsed_device_id,
                    BatteryEquivalentCycle.user_id == user_id,
                )
                .with_for_update()
            )
            cycle = result.scalar_one_or_none()
            if cycle is None:
                raise HTTPException(status_code=404, detail="Cycle not found")

            _set_cycle_excluded(cycle, excluded=True)
            await session.commit()

            return CycleExclusionResponse(
                status="success",
                message="Cycle excluded from analytics",
                device_id=device_id,
                cycle_id=cycle_id,
                is_excluded=True,
                excluded_at=cycle.excluded_at,
            )
        except HTTPException:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise


@router.post(
    "/devices/{device_id}/cycles/{cycle_id}/include",
    response_model=CycleExclusionResponse,
)
async def include_cycle(
    device_id: str,
    cycle_id: str,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")
    parsed_device_id = parse_uuid_or_400(device_id, "device_id")
    parsed_cycle_id = parse_uuid_or_400(cycle_id, "cycle_id")

    async with get_db_session() as session:
        try:
            result = await session.execute(
                select(BatteryEquivalentCycle)
                .where(
                    BatteryEquivalentCycle.cycle_id == parsed_cycle_id,
                    BatteryEquivalentCycle.device_id == parsed_device_id,
                    BatteryEquivalentCycle.user_id == user_id,
                )
                .with_for_update()
            )
            cycle = result.scalar_one_or_none()
            if cycle is None:
                raise HTTPException(status_code=404, detail="Cycle not found")

            _set_cycle_excluded(cycle, excluded=False)
            await session.commit()

            return CycleExclusionResponse(
                status="success",
                message="Cycle included in analytics",
                device_id=device_id,
                cycle_id=cycle_id,
                is_excluded=False,
                excluded_at=None,
            )
        except HTTPException:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise


@router.delete(
    "/devices/{device_id}/cycles/{cycle_id}",
    response_model=CycleDeletionResponse,
)
async def delete_cycle(
    device_id: str,
    cycle_id: str,
    x_user_id: str = Header(..., alias="X-User-Id"),
):
    user_id = parse_uuid_or_400(x_user_id, "X-User-Id")
    parsed_device_id = parse_uuid_or_400(device_id, "device_id")
    parsed_cycle_id = parse_uuid_or_400(cycle_id, "cycle_id")

    async with get_db_session() as session:
        try:
            cycle_result = await session.execute(
                select(BatteryEquivalentCycle)
                .where(
                    BatteryEquivalentCycle.cycle_id == parsed_cycle_id,
                    BatteryEquivalentCycle.device_id == parsed_device_id,
                    BatteryEquivalentCycle.user_id == user_id,
                )
                .with_for_update()
            )
            cycle = cycle_result.scalar_one_or_none()
            if cycle is None:
                raise HTTPException(status_code=404, detail="Cycle not found")

            session_count_result = await session.execute(
                select(func.count(BatterySession.session_id))
                .where(
                    BatterySession.equivalent_cycle_id == parsed_cycle_id,
                    BatterySession.device_id == parsed_device_id,
                    BatterySession.user_id == user_id,
                )
            )
            deleted_sessions = session_count_result.scalar_one()

            await session.delete(cycle)
            await session.commit()

            return CycleDeletionResponse(
                status="success",
                message="Cycle deleted from analytics",
                device_id=device_id,
                cycle_id=cycle_id,
                deleted_sessions=deleted_sessions,
            )
        except HTTPException:
            await session.rollback()
            raise
        except Exception:
            await session.rollback()
            raise
