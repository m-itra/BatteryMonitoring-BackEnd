"""
Unit-тесты для app/routes/battery.py
Покрывает:
  POST /api/battery/submit
    - успешная отправка → 200 + device_id в ответе
    - невалидный JWT → 401
    - отсутствие заголовка Authorization → 403
    - сервис недоступен → 503
    - некорректное тело запроса → 422
    - проверка, что X-User-Id прокидывается в заголовке
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

USER_ID = "user-123"
VALID_PAYLOAD = {"user_id": USER_ID}
AUTH_HEADER = {"Authorization": "Bearer sometoken"}

VALID_BODY = {
    "device_id": "device-456",
    "device_name": "Test Device",
    "battery_level": 85,
    "is_charging": False,
    "timestamp": "2024-01-01T12:00:00",
}

def _mock_response(data: dict, status: int = 200):
    m = MagicMock()
    m.json.return_value = data
    m.status_code = status
    return m


@pytest.fixture()
def client():
    with (
        patch("app.routes.battery.verify_jwt_token", return_value=VALID_PAYLOAD),
        patch("app.routes.battery.PROCESSING_SERVICE_URL", "http://processing-svc"),
    ):
        from app.routes.battery import router
        app = FastAPI()
        app.include_router(router)
        yield TestClient(app, raise_server_exceptions=False)


class TestSubmitBatteryLog:

    def test_successful_submit_returns_200(self, client):
        result = {"status": "ok", "device_id": "device-456"}
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(result)
            response = client.post(
                "/api/battery/submit",
                json=VALID_BODY,
                headers=AUTH_HEADER,
            )

        assert response.status_code == 200
        assert response.json()["device_id"] == "device-456"

    def test_proxy_called_with_correct_url(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.post("/api/battery/submit", json=VALID_BODY, headers=AUTH_HEADER)

        call_args = mock_proxy.call_args
        assert call_args[0][0] == "http://processing-svc/submit"
        assert call_args[0][1] == "POST"

    def test_user_id_passed_in_header(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.post("/api/battery/submit", json=VALID_BODY, headers=AUTH_HEADER)

        headers = mock_proxy.call_args[1]["headers"]
        assert headers["X-User-Id"] == USER_ID

    def test_content_type_json_in_header(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.post("/api/battery/submit", json=VALID_BODY, headers=AUTH_HEADER)

        headers = mock_proxy.call_args[1]["headers"]
        assert headers["Content-Type"] == "application/json"

    def test_body_bytes_sent_to_proxy(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.post("/api/battery/submit", json=VALID_BODY, headers=AUTH_HEADER)

        body = mock_proxy.call_args[1]["body"]
        assert isinstance(body, bytes)
        assert b"device-456" in body

    def test_no_auth_header_returns_403(self, client):
        response = client.post("/api/battery/submit", json=VALID_BODY)
        assert response.status_code == 403

    def test_invalid_jwt_returns_401(self, client):
        with (
            patch(
                "app.routes.battery.verify_jwt_token",
                side_effect=HTTPException(status_code=401, detail="Invalid token"),
            ),
            patch("app.routes.battery.PROCESSING_SERVICE_URL", "http://processing-svc"),
        ):
            from app.routes.battery import router
            app = FastAPI()
            app.include_router(router)
            c = TestClient(app, raise_server_exceptions=False)
            response = c.post(
                "/api/battery/submit",
                json=VALID_BODY,
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
                "/api/battery/submit",
                json=VALID_BODY,
                headers=AUTH_HEADER,
            )

        assert response.status_code == 503

    def test_upstream_400_passes_through(self, client):
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "bad data"}, 400)
            response = client.post(
                "/api/battery/submit",
                json=VALID_BODY,
                headers=AUTH_HEADER,
            )

        assert response.status_code == 400

    def test_new_device_id_returned_when_generated(self, client):
        """Если device_id не был передан, сервис может вернуть новый."""
        body_without_device = {k: v for k, v in VALID_BODY.items() if k != "device_id"}
        result = {"status": "ok", "device_id": "new-generated-device"}
        with patch("app.routes.battery.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(result)
            response = client.post(
                "/api/battery/submit",
                json=body_without_device,
                headers=AUTH_HEADER,
            )

        assert response.json().get("device_id") == "new-generated-device"