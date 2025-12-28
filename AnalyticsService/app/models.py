from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional


class DeviceInfo(BaseModel):
    device_id: str
    device_name: str
    created_at: datetime
    last_seen: datetime
    total_cycles: int
    last_health_score: Optional[float] = None


class CycleInfo(BaseModel):
    cycle_id: str
    device_id: str
    started_at: datetime
    completed_at: datetime
    duration_minutes: int
    health_score: float
    capacity_degradation: float
    cycle_count: int
    charge_cycles_equivalent: Optional[float] = None
    min_level: Optional[int] = None
    max_level: Optional[int] = None
    avg_discharge_rate: Optional[float] = None
    avg_charge_rate: Optional[float] = None


class UpdateDeviceRequest(BaseModel):
    device_name: str


class AnalyticsResponse(BaseModel):
    user: dict
    devices: List[DeviceInfo]
    recent_cycles: List[CycleInfo]
    total_cycles: int