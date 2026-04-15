from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select

from app.db.models import BatteryCycle, Device


def parse_uuid_or_400(value: str, field_name: str) -> UUID:
    try:
        return UUID(value)
    except (TypeError, ValueError):
        raise HTTPException(status_code=400, detail=f"Invalid {field_name}")


def device_summary_statement(user_id: UUID):
    last_health_score = (
        select(BatteryCycle.health_score)
        .where(BatteryCycle.device_id == Device.device_id)
        .order_by(BatteryCycle.completed_at.desc())
        .limit(1)
        .correlate(Device)
        .scalar_subquery()
    )

    return (
        select(
            Device.device_id,
            Device.device_name,
            Device.created_at,
            Device.last_seen,
            func.count(BatteryCycle.cycle_id).label("total_cycles"),
            last_health_score.label("last_health_score"),
        )
        .outerjoin(BatteryCycle, Device.device_id == BatteryCycle.device_id)
        .where(Device.user_id == user_id)
        .group_by(Device.device_id, Device.device_name, Device.created_at, Device.last_seen)
        .order_by(Device.last_seen.desc())
    )
