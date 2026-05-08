from contextlib import asynccontextmanager
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient


TEST_USER_ID = str(uuid4())
TEST_DEVICE_ID = str(uuid4())


def _fake_session_context(session_obj):
    @asynccontextmanager
    async def _context_manager():
        yield session_obj

    return _context_manager


def _batch_payload(*, device_id: str | None = TEST_DEVICE_ID, reference_capacity_mwh: int = 40000):
    payload = {
        "device_name": "Office Laptop",
        "battery_id": "battery-1",
        "reference_capacity_mwh": reference_capacity_mwh,
        "samples": [
            {
                "boot_session_id": str(uuid4()),
                "sample_seq": 1,
                "client_time": "2026-05-08T12:00:00",
                "ac_connected": False,
                "is_charging": False,
                "charge_percent": 55.0,
                "remaining_capacity_mwh": 25000,
                "full_charge_capacity_mwh": 50000,
                "design_capacity_mwh": 52000,
                "voltage_mv": 12000,
                "net_power_mw": 10000,
                "temperature_c": None,
                "status": "discharging",
            }
        ],
    }
    if device_id is not None:
        payload["device_id"] = device_id
    return payload


def _response_payload():
    return {
        "device_id": TEST_DEVICE_ID,
        "processed_samples": 1,
        "duplicate_samples": 0,
        "completed_sessions": 0,
        "completed_cycles": 0,
    }
def _build_client():
    from app.routes.submit import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


class TestSubmitBatteryLogsBatchRoute:
    def test_successful_submit_accepts_zero_reference_capacity_and_returns_batch_response(self):
        session = SimpleNamespace(
            commit=AsyncMock(),
            rollback=AsyncMock(),
        )
        device = SimpleNamespace(
            device_id=uuid4(),
            user_id=uuid4(),
        )
        ingest_result = SimpleNamespace(**_response_payload())

        with (
            patch("app.routes.submit.validate_user_via_grpc", new=AsyncMock(return_value={"exists": True})),
            patch("app.routes.submit.get_db_session", _fake_session_context(session)),
            patch("app.routes.submit.get_device_record_by_id", new=AsyncMock(return_value=device)),
            patch("app.routes.submit.process_battery_batch", new=AsyncMock(return_value=ingest_result)) as process_mock,
        ):
            client = _build_client()
            response = client.post(
                "/logs/batch",
                json=_batch_payload(reference_capacity_mwh=0),
                headers={"X-User-Id": str(device.user_id)},
            )

        assert response.status_code == 200
        assert response.json() == {
            "status": "success",
            "message": "Battery batch processed",
            **_response_payload(),
        }
        assert process_mock.await_args.kwargs["request_data"].reference_capacity_mwh == 0
        session.commit.assert_awaited_once()

    def test_missing_user_from_grpc_returns_404(self):
        with patch("app.routes.submit.validate_user_via_grpc", new=AsyncMock(return_value={"exists": False})):
            client = _build_client()
            response = client.post(
                "/logs/batch",
                json=_batch_payload(),
                headers={"X-User-Id": TEST_USER_ID},
            )

        assert response.status_code == 404
        assert "not found" in response.json()["detail"]

    def test_submit_returns_403_when_device_belongs_to_another_user(self):
        session = SimpleNamespace(
            commit=AsyncMock(),
            rollback=AsyncMock(),
        )
        other_user_id = str(uuid4())
        device = SimpleNamespace(
            device_id=uuid4(),
            user_id=uuid4(),
        )

        with (
            patch("app.routes.submit.validate_user_via_grpc", new=AsyncMock(return_value={"exists": True})),
            patch("app.routes.submit.get_db_session", _fake_session_context(session)),
            patch("app.routes.submit.get_device_record_by_id", new=AsyncMock(return_value=device)),
        ):
            client = _build_client()
            response = client.post(
                "/logs/batch",
                json=_batch_payload(),
                headers={"X-User-Id": other_user_id},
            )

        assert response.status_code == 403
        assert response.json()["detail"] == "Device belongs to another user"
        session.rollback.assert_awaited_once()
