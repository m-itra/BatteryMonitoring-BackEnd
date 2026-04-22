from datetime import datetime
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import BatteryEquivalentCycle, BatterySession, Device

from app.services.battery_math import avg_load_mw


def ensure_reference_capacity(device: Device, fallback_energy_mwh: float) -> int:
    if device.reference_capacity_mwh is not None and device.reference_capacity_mwh > 0:
        return device.reference_capacity_mwh

    baseline_capacity_mwh = max(int(round(fallback_energy_mwh)), 1)
    if device.baseline_capacity_mwh is None:
        device.baseline_capacity_mwh = baseline_capacity_mwh

    device.reference_capacity_mwh = device.baseline_capacity_mwh
    device.reference_capacity_source = "baseline"
    return device.reference_capacity_mwh


async def create_equivalent_cycles(
    session: AsyncSession,
    device: Device,
) -> int:
    created_cycles = 0

    while True:
        result = await session.execute(
            select(BatterySession)
            .where(
                BatterySession.device_id == device.device_id,
                BatterySession.status == "completed",
                BatterySession.equivalent_cycle_id.is_(None),
                BatterySession.discharge_delta_percent > 0,
            )
            .order_by(BatterySession.ended_at_client.asc(), BatterySession.session_id.asc())
            .with_for_update()
        )
        pending_sessions = result.scalars().all()

        if not pending_sessions:
            break

        accumulated_percent = 0.0
        total_energy_mwh = 0.0
        total_duration_seconds = 0
        selected_sessions: list[BatterySession] = []
        cycle_started_at: Optional[datetime] = None
        cycle_ended_at: Optional[datetime] = None

        for pending_session in pending_sessions:
            remaining_percent = 100.0 - accumulated_percent
            session_percent = pending_session.discharge_delta_percent

            if cycle_started_at is None:
                cycle_started_at = pending_session.started_at_client

            selected_sessions.append(pending_session)
            cycle_ended_at = pending_session.ended_at_client

            if session_percent < remaining_percent:
                accumulated_percent += session_percent
                total_energy_mwh += pending_session.discharged_energy_mwh
                total_duration_seconds += pending_session.duration_seconds
                continue

            usage_ratio = remaining_percent / session_percent if session_percent > 0 else 0.0
            total_energy_mwh += pending_session.discharged_energy_mwh * usage_ratio
            total_duration_seconds += int(round(pending_session.duration_seconds * usage_ratio))
            accumulated_percent = 100.0
            break

        if accumulated_percent < 100.0 or cycle_started_at is None or cycle_ended_at is None:
            break

        reference_capacity_mwh = ensure_reference_capacity(device, total_energy_mwh)
        full_charge_capacity_mwh = device.last_full_charge_capacity_mwh

        soh_capacity_percent = None
        degradation_capacity_percent = None
        if full_charge_capacity_mwh is not None and reference_capacity_mwh > 0:
            soh_capacity_percent = (full_charge_capacity_mwh / reference_capacity_mwh) * 100
            degradation_capacity_percent = max(0.0, 100.0 - soh_capacity_percent)

        soh_energy_percent = None
        degradation_energy_percent = None
        if reference_capacity_mwh > 0:
            soh_energy_percent = (total_energy_mwh / reference_capacity_mwh) * 100
            degradation_energy_percent = max(0.0, 100.0 - soh_energy_percent)

        average_load_mw = avg_load_mw(total_energy_mwh, total_duration_seconds)
        cycle = BatteryEquivalentCycle(
            device_id=device.device_id,
            user_id=device.user_id,
            started_at_client=cycle_started_at,
            ended_at_client=cycle_ended_at,
            session_count=len(selected_sessions),
            total_discharge_percent=100.0,
            total_energy_mwh=round(total_energy_mwh, 4),
            total_duration_seconds=total_duration_seconds,
            avg_load_mw=round(average_load_mw, 4) if average_load_mw is not None else None,
            reference_capacity_mwh_used=reference_capacity_mwh,
            full_charge_capacity_mwh_at_cycle_end=full_charge_capacity_mwh,
            soh_capacity_percent=round(soh_capacity_percent, 4) if soh_capacity_percent is not None else None,
            degradation_capacity_percent=(
                round(degradation_capacity_percent, 4)
                if degradation_capacity_percent is not None
                else None
            ),
            soh_energy_percent=round(soh_energy_percent, 4) if soh_energy_percent is not None else None,
            degradation_energy_percent=(
                round(degradation_energy_percent, 4)
                if degradation_energy_percent is not None
                else None
            ),
        )
        session.add(cycle)
        await session.flush()

        for selected_session in selected_sessions:
            selected_session.equivalent_cycle_id = cycle.cycle_id

        created_cycles += 1

    return created_cycles
