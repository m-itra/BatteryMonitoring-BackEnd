from datetime import datetime, timedelta
from uuid import UUID

import random

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BatteryCycle, Device


class DeviceNotFoundError(Exception):
    pass


async def create_fake_cycle(session: AsyncSession, device_id: str, user_id: str):
    parsed_device_id = UUID(device_id)
    parsed_user_id = UUID(user_id)

    locked_device = await session.execute(
        select(Device.device_id)
        .where(Device.device_id == parsed_device_id)
        .with_for_update()
    )
    if locked_device.scalar_one_or_none() is None:
        raise DeviceNotFoundError(f"Device with device_id '{device_id}' not found")

    result = await session.execute(
        select(func.max(BatteryCycle.cycle_count)).where(BatteryCycle.device_id == parsed_device_id)
    )
    cycle_count = (result.scalar_one() or 0) + 1

    health_score = random.uniform(75.0, 98.0)
    capacity_degradation = random.uniform(0.5, 15.0)
    duration = random.randint(180, 480)
    completed_at = datetime.now()

    session.add(
        BatteryCycle(
            device_id=parsed_device_id,
            user_id=parsed_user_id,
            started_at=completed_at - timedelta(minutes=duration),
            completed_at=completed_at,
            duration_minutes=duration,
            health_score=round(health_score, 2),
            capacity_degradation=round(capacity_degradation, 2),
            cycle_count=cycle_count,
            charge_cycles_equivalent=round(random.uniform(0.8, 1.2), 2),
            min_level=random.randint(5, 20),
            max_level=random.randint(95, 100),
            avg_discharge_rate=round(random.uniform(10.0, 25.0), 2),
            avg_charge_rate=round(random.uniform(15.0, 40.0), 2),
        )
    )
