from contextlib import asynccontextmanager
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, call, patch
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.db.models import Device
from app.models import ActiveSessionInfo, CapacityHistoryPoint, CycleInfo, DeviceInfo, SessionInfo


TEST_USER_ID = str(uuid4())
TEST_DEVICE_ID = str(uuid4())


def _fake_session_context(session_obj):
    @asynccontextmanager
    async def _context_manager():
        yield session_obj

    return _context_manager


def _device_info() -> DeviceInfo:
    now = datetime.fromisoformat("2026-05-08T12:00:00")
    return DeviceInfo(
        device_id=TEST_DEVICE_ID,
        device_name="Office Laptop",
        created_at=now,
        last_seen=now,
        current_charge_percent=55.0,
        current_net_power_mw=10000,
        current_full_charge_capacity_mwh=50000,
        current_soe_percent=50.0,
        current_soh_capacity_percent=95.0,
        current_soh_energy_percent=90.0,
        reference_capacity_mwh=50000,
        reference_capacity_source="user",
        total_cycles=3,
        has_active_session=True,
    )


def _active_session() -> ActiveSessionInfo:
    now = datetime.fromisoformat("2026-05-08T12:00:00")
    return ActiveSessionInfo(
        device_id=TEST_DEVICE_ID,
        started_at_client=now,
        started_at_server=now,
        last_client_time=now,
        last_server_received_at=now,
        start_charge_percent=70.0,
        current_charge_percent=55.0,
        discharged_energy_mwh=1234.5,
        duration_seconds=321.0,
        pending_transition="none",
    )


def _session_info() -> SessionInfo:
    now = datetime.fromisoformat("2026-05-08T12:00:00")
    return SessionInfo(
        session_id=str(uuid4()),
        device_id=TEST_DEVICE_ID,
        boot_session_id=str(uuid4()),
        started_at_client=now,
        ended_at_client=now,
        started_at_server=now,
        ended_at_server=now,
        start_charge_percent=70.0,
        end_charge_percent=50.0,
        discharge_delta_percent=20.0,
        discharged_energy_mwh=5000.0,
        duration_seconds=1200.0,
        avg_load_mw=15000.0,
        status="completed",
        equivalent_cycle_id=None,
    )


def _cycle_info(cycle_id: str) -> CycleInfo:
    now = datetime.fromisoformat("2026-05-08T12:00:00")
    return CycleInfo(
        cycle_id=cycle_id,
        device_id=TEST_DEVICE_ID,
        started_at_client=now,
        ended_at_client=now,
        session_count=1,
        total_discharge_percent=100.0,
        total_energy_mwh=36000.0,
        total_duration_seconds=7200.0,
        avg_load_mw=18000.0,
        reference_capacity_mwh_used=40000,
        full_charge_capacity_mwh_at_cycle_end=38000,
        soh_capacity_percent=95.0,
        degradation_capacity_percent=5.0,
        soh_energy_percent=90.0,
        degradation_energy_percent=10.0,
        is_excluded=False,
        excluded_at=None,
        created_at=now,
    )


def _capacity_point() -> CapacityHistoryPoint:
    now = datetime.fromisoformat("2026-05-08T12:00:00")
    return CapacityHistoryPoint(
        recorded_at=now,
        full_charge_capacity_mwh=38000,
        total_energy_mwh=36000.0,
        reference_capacity_mwh_used=40000,
        soh_capacity_percent=95.0,
        soh_energy_percent=90.0,
        degradation_capacity_percent=5.0,
        degradation_energy_percent=10.0,
    )


def _build_client():
    from app.routes.devices import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app, raise_server_exceptions=False)


def _mappings_result(row):
    result = MagicMock()
    result.mappings.return_value.one_or_none.return_value = row
    return result


def _scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    result.scalars.return_value.all.return_value = value
    return result


class TestDeviceRoutes:
    def test_get_device_analytics_returns_all_sections_and_uses_current_reference_for_cycles(self):
        now = datetime.fromisoformat("2026-05-08T12:00:00")
        device_row = {
            "device_id": uuid4(),
            "device_name": "Office Laptop",
            "created_at": now,
            "last_seen": now,
            "last_charge_percent": 55.0,
            "last_net_power_mw": 10000,
            "last_full_charge_capacity_mwh": 50000,
            "reference_capacity_mwh": 50000,
            "reference_capacity_source": "user",
            "total_cycles": 3,
            "current_soh_energy_percent": 90.0,
            "has_active_session": True,
            "current_soe_percent": 50.0,
            "current_soh_capacity_percent": 95.0,
        }
        active_session_row = SimpleNamespace()
        session_row = SimpleNamespace()
        included_cycle = SimpleNamespace(is_excluded=False)
        excluded_cycle = SimpleNamespace(is_excluded=True)
        db_session = SimpleNamespace(
            execute=AsyncMock(
                side_effect=[
                    _mappings_result(device_row),
                    _scalar_result(active_session_row),
                    _scalar_result([session_row]),
                    _scalar_result([included_cycle, excluded_cycle]),
                ]
            )
        )

        with (
            patch("app.routes.devices.get_db_session", _fake_session_context(db_session)),
            patch("app.routes.devices.build_device_info", return_value=_device_info()) as build_device_info_mock,
            patch("app.routes.devices.build_active_session_info", return_value=_active_session()) as build_active_session_mock,
            patch("app.routes.devices.build_session_info", return_value=_session_info()) as build_session_mock,
            patch(
                "app.routes.devices.build_cycle_info",
                side_effect=[_cycle_info(str(uuid4())), _cycle_info(str(uuid4()))],
            ) as build_cycle_mock,
            patch(
                "app.routes.devices.build_capacity_history_point",
                return_value=_capacity_point(),
            ) as build_capacity_mock,
        ):
            client = _build_client()
            response = client.get(
                f"/devices/{TEST_DEVICE_ID}",
                headers={"X-User-Id": str(uuid4())},
            )

        assert response.status_code == 200
        body = response.json()
        assert set(body.keys()) == {"device", "active_session", "recent_sessions", "cycles", "capacity_history"}
        assert len(body["recent_sessions"]) == 1
        assert len(body["cycles"]) == 2
        assert len(body["capacity_history"]) == 1
        build_device_info_mock.assert_called_once_with(device_row)
        build_active_session_mock.assert_called_once_with(active_session_row)
        build_session_mock.assert_called_once_with(session_row)
        assert build_cycle_mock.call_args_list == [
            call(included_cycle, 50000),
            call(excluded_cycle, 50000),
        ]
        build_capacity_mock.assert_called_once_with(included_cycle, 50000)

    def test_update_device_switches_back_to_design_reference_when_zero_is_sent(self):
        device = Device(
            device_id=uuid4(),
            user_id=uuid4(),
            device_name="Office Laptop",
            reference_capacity_mwh=40000,
            reference_capacity_source="user",
            last_design_capacity_mwh=52000,
            last_full_charge_capacity_mwh=50000,
        )
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = device
        db_session = SimpleNamespace(
            execute=AsyncMock(return_value=execute_result),
            commit=AsyncMock(),
            rollback=AsyncMock(),
        )

        with patch("app.routes.devices.get_db_session", _fake_session_context(db_session)):
            client = _build_client()
            response = client.put(
                f"/devices/{device.device_id}",
                json={"reference_capacity_mwh": 0},
                headers={"X-User-Id": str(device.user_id)},
            )

        assert response.status_code == 200
        assert response.json() == {
            "status": "updated",
            "device_id": str(device.device_id),
            "device_name": "Office Laptop",
            "reference_capacity_mwh": 52000,
            "reference_capacity_source": "design",
        }
        db_session.commit.assert_awaited_once()

    def test_update_device_returns_404_when_device_is_missing(self):
        execute_result = MagicMock()
        execute_result.scalar_one_or_none.return_value = None
        db_session = SimpleNamespace(
            execute=AsyncMock(return_value=execute_result),
            commit=AsyncMock(),
            rollback=AsyncMock(),
        )

        with patch("app.routes.devices.get_db_session", _fake_session_context(db_session)):
            client = _build_client()
            response = client.put(
                f"/devices/{uuid4()}",
                json={"reference_capacity_mwh": 0},
                headers={"X-User-Id": str(uuid4())},
            )

        assert response.status_code == 404
        assert response.json()["detail"] == "Device not found"
        db_session.rollback.assert_awaited_once()
