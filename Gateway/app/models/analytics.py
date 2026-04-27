from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints

NonEmptyStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]


class DeviceInfo(BaseModel):
    device_id: str
    device_name: str
    created_at: str
    last_seen: str
    total_cycles: int
    last_health_score: Optional[float] = None


class UpdateDeviceRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_name": "My MacBook Pro"
            }
        }
    )

    device_name: NonEmptyStr


class CycleExclusionResponse(BaseModel):
    status: str
    message: str
    device_id: str
    cycle_id: str
    is_excluded: bool
    excluded_at: Optional[str] = None
