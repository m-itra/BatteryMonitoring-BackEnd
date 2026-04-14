from pydantic import BaseModel, ConfigDict, model_validator
from typing import Optional


class BatteryLogRequest(BaseModel):
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "device_id": "my-laptop",
                "device_name": "MacBook Pro 2023",
                "battery_level": 85,
                "is_charging": False
            }
        }
    )

    device_id: Optional[str] = None
    device_name: Optional[str] = None
    battery_level: int
    is_charging: bool
    timestamp: Optional[str] = None

    @model_validator(mode="before")
    def check_device_info(cls, values):
        device_id = values.get("device_id")
        device_name = values.get("device_name")
        if not device_id and not device_name:
            raise ValueError("Если device_id не передан, device_name обязателен")
        return values


class SubmitResponse(BaseModel):
    status: str
    message: str
    device_id: str
    cycle_created: bool = False
