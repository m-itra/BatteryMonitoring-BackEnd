from typing import Annotated, Optional

from pydantic import BaseModel, ConfigDict, StringConstraints, model_validator

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
                "device_name": "My MacBook Pro",
                "reference_capacity_mwh": 40000,
            }
        }
    )

    device_name: Optional[NonEmptyStr] = None
    reference_capacity_mwh: Optional[int] = None

    @model_validator(mode="after")
    def validate_has_updatable_fields(self):
        if self.device_name is None and self.reference_capacity_mwh is None:
            raise ValueError("device_name or reference_capacity_mwh is required")
        return self


class CycleExclusionResponse(BaseModel):
    status: str
    message: str
    device_id: str
    cycle_id: str
    is_excluded: bool
    excluded_at: Optional[str] = None


class CycleDeletionResponse(BaseModel):
    status: str
    message: str
    device_id: str
    cycle_id: str
    deleted_sessions: int
