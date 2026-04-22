from datetime import datetime
from typing import Optional

from app.db.models import Device
from app.models.battery import BatterySample


def order_samples(samples: list[BatterySample]) -> list[BatterySample]:
    return sorted(samples, key=lambda sample: (sample.client_time, sample.sample_seq))


def is_duplicate_sample(device: Device, sample: BatterySample) -> bool:
    return (
        device.last_boot_session_id == sample.boot_session_id
        and device.last_sample_seq is not None
        and sample.sample_seq <= device.last_sample_seq
    )


def integrate_discharge(
    previous_client_time: Optional[datetime],
    previous_net_power_mw: Optional[int],
    current_client_time: datetime,
) -> tuple[float, int]:
    if previous_client_time is None or previous_net_power_mw is None:
        return 0.0, 0

    dt_seconds = max(int((current_client_time - previous_client_time).total_seconds()), 0)
    if dt_seconds == 0:
        return 0.0, 0

    energy_step_mwh = max(previous_net_power_mw, 0) * (dt_seconds / 3600)
    return energy_step_mwh, dt_seconds


def avg_load_mw(energy_mwh: float, duration_seconds: int) -> Optional[float]:
    if duration_seconds <= 0:
        return None

    return energy_mwh / (duration_seconds / 3600)
