"""
Unit-tests for app/routes/battery.py

Covered endpoint:
  POST /api/battery/logs/batch
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

USER_ID = "user-123"
VALID_PAYLOAD = {"user_id": USER_ID}
AUTH_HEADER = {"Authorization": "Bearer sometoken"}

VALID_BATCH_BODY = {
    "device_id": "74fd26ad-5f67-489c-a17b-7f8eef3d9612",
    "device_name": "Test Device",
    "battery_id": r"\\?\acpi#pnp0c0a#battery",
    "reference_capacity_mwh": 40000,
    "samples": [
        {
            "boot_session_id": "3a0481a3-ab9b-4a9d-8d82-0f85cf822dbc",
            "sample_seq": 1,
            "client_time": "2026-04-21T13:40:17.967102",
            "ac_connected": True,
            "is_charging": True,
            "charge_percent": 94.7,
            "remaining_capacity_mwh": 37648,
            "full_charge_capacity_mwh": 39735,
            "design_capacity_mwh": 39735,
            "voltage_mv": 12940,
            "net_power_mw": -11793,
            "temperature_c": None,
            "status": "charging,ac_online",
        }
    ],
}


def _mock_response(data: dict, status: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = data
    mock_response.status_code = status
    return mock_response


@pytest.fixture()
def client():
    with (
        patch("app.utils.auth_dependencies.verify_jwt_token", return_value=VALID_PAYLOAD),
        patch("app.routes.battery.PROCESSING_SERVICE_URL", "http://processing-svc"),
    ):
        from app.routes.battery import router

        app = FastAPI()
        app.include_router(router)
        yield TestClient(app, raise_server_exceptions=False)


class TestSubmitBatteryBatch:
    def test_successful_batch_submit_returns_200(self, client):
        result = {
            "status": "ok",
            "device_id": "74fd26ad-5f67-489c-a17b-7f8eef3d9612",
            "processed_samples": 1,
            "duplicate_samples": 0,
            "completed_sessions": 0,
            "completed_cycles": 0,
        }
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(result)
            response = client.post(
                "/api/battery/logs/batch",
                json=VALID_BATCH_BODY,
                headers=AUTH_HEADER,
            )

        assert response.status_code == 200
        assert response.json()["processed_samples"] == 1

    def test_batch_proxy_called_with_correct_url(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.post("/api/battery/logs/batch", json=VALID_BATCH_BODY, headers=AUTH_HEADER)

        call_args = mock_proxy.call_args
        assert call_args[0][0] == "http://processing-svc/logs/batch"
        assert call_args[0][1] == "POST"

    def test_user_id_passed_in_header(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.post("/api/battery/logs/batch", json=VALID_BATCH_BODY, headers=AUTH_HEADER)

        headers = mock_proxy.call_args[1]["headers"]
        assert headers["X-User-Id"] == USER_ID

    def test_content_type_json_in_header(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.post("/api/battery/logs/batch", json=VALID_BATCH_BODY, headers=AUTH_HEADER)

        headers = mock_proxy.call_args[1]["headers"]
        assert headers["Content-Type"] == "application/json"

    def test_body_bytes_sent_to_proxy(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.post("/api/battery/logs/batch", json=VALID_BATCH_BODY, headers=AUTH_HEADER)

        body = mock_proxy.call_args[1]["body"]
        assert isinstance(body, bytes)
        assert b"sample_seq" in body

    def test_cookie_auth_works_without_authorization_header(self, client):
        result = {
            "status": "ok",
            "device_id": "74fd26ad-5f67-489c-a17b-7f8eef3d9612",
            "processed_samples": 1,
            "duplicate_samples": 0,
            "completed_sessions": 0,
            "completed_cycles": 0,
        }
        client.cookies.set("access_token", "cookie-token")
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(result)
            response = client.post("/api/battery/logs/batch", json=VALID_BATCH_BODY)

        assert response.status_code == 200
        assert mock_proxy.call_args[1]["headers"]["X-User-Id"] == USER_ID

    def test_authorization_header_has_priority_over_cookie(self, client):
        client.cookies.set("access_token", "cookie-token")
        with patch("app.utils.auth_dependencies.verify_jwt_token", return_value=VALID_PAYLOAD) as mock_verify:
            with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
                mock_proxy.return_value = _mock_response({})
                client.post(
                    "/api/battery/logs/batch",
                    json=VALID_BATCH_BODY,
                    headers=AUTH_HEADER,
                )

        mock_verify.assert_called_once_with("sometoken")

    def test_no_auth_returns_401(self, client):
        response = client.post("/api/battery/logs/batch", json=VALID_BATCH_BODY)
        assert response.status_code == 401

    def test_invalid_jwt_returns_401(self):
        with (
            patch(
                "app.utils.auth_dependencies.verify_jwt_token",
                side_effect=HTTPException(status_code=401, detail="Invalid token"),
            ),
            patch("app.routes.battery.PROCESSING_SERVICE_URL", "http://processing-svc"),
        ):
            from app.routes.battery import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app, raise_server_exceptions=False)
            response = client.post(
                "/api/battery/logs/batch",
                json=VALID_BATCH_BODY,
                headers=AUTH_HEADER,
            )

        assert response.status_code == 401

    def test_service_unavailable_returns_503(self, client):
        with patch(
            "app.routes.battery.proxy_request",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=503, detail="Service unavailable"),
        ):
            response = client.post(
                "/api/battery/logs/batch",
                json=VALID_BATCH_BODY,
                headers=AUTH_HEADER,
            )

        assert response.status_code == 503

    def test_upstream_400_passes_through(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "bad data"}, 400)
            response = client.post(
                "/api/battery/logs/batch",
                json=VALID_BATCH_BODY,
                headers=AUTH_HEADER,
            )

        assert response.status_code == 400

    def test_batch_without_samples_returns_422(self, client):
        body = {**VALID_BATCH_BODY, "samples": []}
        response = client.post(
            "/api/battery/logs/batch",
            json=body,
            headers=AUTH_HEADER,
        )

        assert response.status_code == 422

    @pytest.mark.parametrize("charge_percent", [-1, 101])
    def test_invalid_charge_percent_returns_422(self, client, charge_percent):
        body = {
            **VALID_BATCH_BODY,
            "samples": [{**VALID_BATCH_BODY["samples"][0], "charge_percent": charge_percent}],
        }
        response = client.post(
            "/api/battery/logs/batch",
            json=body,
            headers=AUTH_HEADER,
        )

        assert response.status_code == 422

    def test_blank_device_info_returns_422(self, client):
        body = {
            **VALID_BATCH_BODY,
            "device_id": "   ",
            "device_name": "   ",
        }
        response = client.post(
            "/api/battery/logs/batch",
            json=body,
            headers=AUTH_HEADER,
        )

        assert response.status_code == 422
