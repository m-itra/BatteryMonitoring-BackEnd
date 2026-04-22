from datetime import datetime

from sqlalchemy.ext.asyncio import AsyncSession

from app.db.device import update_device_snapshot
from app.db.models import BatteryActiveSession, Device
from app.models.battery import BatteryLogBatchRequest
from app.services.battery_batch_types import BatchIngestResult
from app.services.battery_math import is_duplicate_sample, order_samples
from app.services.battery_session_flow import (
    get_active_session,
    handle_active_session,
    handle_finish_candidate,
    handle_start_candidate,
    interrupt_stale_session_if_needed,
)


async def process_battery_batch(
    session: AsyncSession,
    *,
    device: Device,
    request_data: BatteryLogBatchRequest,
) -> BatchIngestResult:
    result = BatchIngestResult(device_id=str(device.device_id))
    active_session = await get_active_session(session, device.device_id)

    for sample in order_samples(request_data.samples):
        received_at = datetime.now()

        if is_duplicate_sample(device, sample):
            result.duplicate_samples += 1
            continue

        active_session = await interrupt_stale_session_if_needed(
            session,
            active_session,
            received_at=received_at,
            sample=sample,
        )

        if active_session is None:
            if not sample.ac_connected:
                active_session = BatteryActiveSession(
                    device_id=device.device_id,
                    user_id=device.user_id,
                    boot_session_id=sample.boot_session_id,
                    started_at_client=sample.client_time,
                    started_at_server=received_at,
                    last_client_time=sample.client_time,
                    last_server_received_at=received_at,
                    last_sample_seq=sample.sample_seq,
                    start_charge_percent=sample.charge_percent,
                    current_charge_percent=sample.charge_percent,
                    discharged_energy_mwh=0.0,
                    duration_seconds=0,
                    pending_transition="start_candidate",
                )
                session.add(active_session)
                await session.flush()
        elif active_session.pending_transition == "start_candidate":
            active_session = await handle_start_candidate(
                session,
                active_session,
                device=device,
                sample=sample,
                received_at=received_at,
            )
        elif active_session.pending_transition == "finish_candidate":
            active_session, completed_sessions, completed_cycles = await handle_finish_candidate(
                session,
                device,
                active_session,
                sample=sample,
                received_at=received_at,
            )
            result.completed_sessions += completed_sessions
            result.completed_cycles += completed_cycles
        else:
            active_session = await handle_active_session(
                active_session,
                device=device,
                sample=sample,
                received_at=received_at,
            )

        update_device_snapshot(
            device,
            sample=sample,
            received_at=received_at,
            battery_id=request_data.battery_id,
            requested_reference_capacity_mwh=request_data.reference_capacity_mwh,
        )
        result.processed_samples += 1

    await session.flush()
    return result
