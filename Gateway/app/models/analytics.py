from typing import Optional
from pydantic import BaseModel, ConfigDict

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

    device_name: str