"""
Unit-тесты для app/routes/analytics.py
Покрывает все 5 эндпоинтов:
  GET    /api/analytics/devices
  GET    /api/analytics/cycles
  GET    /api/analytics
  PUT    /api/analytics/devices/{device_id}
  DELETE /api/analytics/devices/{device_id}
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, HTTPException

USER_ID = "user-123"
DEVICE_ID = "device-456"
VALID_PAYLOAD = {"user_id": USER_ID}
AUTH_HEADER = {"Authorization": "Bearer sometoken"}


def _mock_response(data: dict, status: int = 200):
    m = MagicMock()
    m.json.return_value = data
    m.status_code = status
    return m


@pytest.fixture()
def client():
    with (
        patch("app.utils.auth_dependencies.verify_jwt_token", return_value=VALID_PAYLOAD),
        patch("app.routes.analytics.ANALYTICS_SERVICE_URL", "http://analytics-svc"),
    ):
        from app.routes.analytics import router
        app = FastAPI()
        app.include_router(router)
        yield TestClient(app, raise_server_exceptions=False)


# ── GET /api/analytics/devices ────────────────────────────────────────────────

class TestGetDevices:

    def test_returns_200_with_device_list(self, client):
        devices = [{"id": DEVICE_ID, "name": "Phone"}]
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(devices)
            response = client.get("/api/analytics/devices", headers=AUTH_HEADER)

        assert response.status_code == 200
        assert response.json() == devices

    def test_proxy_called_with_correct_url_and_user_id(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response([])
            client.get("/api/analytics/devices", headers=AUTH_HEADER)

        mock_proxy.assert_called_once_with(
            "http://analytics-svc/devices",
            "GET",
            headers={"X-User-Id": USER_ID},
        )

    def test_cookie_auth_works_without_authorization_header(self, client):
        devices = [{"id": DEVICE_ID, "name": "Phone"}]
        client.cookies.set("access_token", "cookie-token")
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(devices)
            response = client.get("/api/analytics/devices")

        assert response.status_code == 200
        assert mock_proxy.call_args[1]["headers"]["X-User-Id"] == USER_ID

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/analytics/devices")
        assert response.status_code == 401

    def test_upstream_404_passes_through(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "not found"}, 404)
            response = client.get("/api/analytics/devices", headers=AUTH_HEADER)

        assert response.status_code == 404

    def test_returns_empty_list(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response([])
            response = client.get("/api/analytics/devices", headers=AUTH_HEADER)

        assert response.json() == []


class TestGetDeviceAnalytics:

    def test_returns_200_with_device_analytics(self, client):
        payload = {"device": {"device_id": DEVICE_ID}, "recent_sessions": [], "cycles": [], "capacity_history": []}
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(payload)
            response = client.get(f"/api/analytics/devices/{DEVICE_ID}", headers=AUTH_HEADER)

        assert response.status_code == 200
        assert response.json()["device"]["device_id"] == DEVICE_ID

    def test_proxy_called_with_limits(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.get(
                f"/api/analytics/devices/{DEVICE_ID}",
                params={"session_limit": 10, "cycle_limit": 15},
                headers=AUTH_HEADER,
            )

        mock_proxy.assert_called_once_with(
            f"http://analytics-svc/devices/{DEVICE_ID}",
            "GET",
            headers={"X-User-Id": USER_ID},
            params={"session_limit": 10, "cycle_limit": 15},
        )

    @pytest.mark.parametrize("field,value", [("session_limit", 0), ("cycle_limit", 201)])
    def test_invalid_limits_return_422(self, client, field, value):
        response = client.get(
            f"/api/analytics/devices/{DEVICE_ID}",
            params={field: value},
            headers=AUTH_HEADER,
        )

        assert response.status_code == 422


# ── GET /api/analytics/cycles ─────────────────────────────────────────────────

class TestGetCycles:

    def test_returns_200_with_cycles(self, client):
        cycles = [{"cycle_id": "c1", "duration": 120}]
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(cycles)
            response = client.get(
                "/api/analytics/cycles",
                params={"device_id": DEVICE_ID},
                headers=AUTH_HEADER,
            )

        assert response.status_code == 200
        assert response.json() == cycles

    def test_proxy_called_with_device_id_and_limit(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response([])
            client.get(
                "/api/analytics/cycles",
                params={"device_id": DEVICE_ID, "limit": 10},
                headers=AUTH_HEADER,
            )

        mock_proxy.assert_called_once_with(
            "http://analytics-svc/cycles",
            "GET",
            headers={"X-User-Id": USER_ID},
            params={"device_id": DEVICE_ID, "limit": 10, "include_excluded": True},
        )

    def test_default_limit_is_50(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response([])
            client.get(
                "/api/analytics/cycles",
                params={"device_id": DEVICE_ID},
                headers=AUTH_HEADER,
            )

        assert mock_proxy.call_args[1]["params"]["limit"] == 50
        assert mock_proxy.call_args[1]["params"]["include_excluded"] is True

    def test_include_excluded_passed_through(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response([])
            client.get(
                "/api/analytics/cycles",
                params={"device_id": DEVICE_ID, "include_excluded": True},
                headers=AUTH_HEADER,
            )

        assert mock_proxy.call_args[1]["params"]["include_excluded"] is True

    def test_missing_device_id_returns_422(self, client):
        response = client.get("/api/analytics/cycles", headers=AUTH_HEADER)
        assert response.status_code == 422

    @pytest.mark.parametrize("limit", [0, 201])
    def test_invalid_limit_returns_422(self, client, limit):
        response = client.get(
            "/api/analytics/cycles",
            params={"device_id": DEVICE_ID, "limit": limit},
            headers=AUTH_HEADER,
        )
        assert response.status_code == 422

    def test_no_auth_returns_401(self, client):
        response = client.get(
            "/api/analytics/cycles",
            params={"device_id": DEVICE_ID},
        )
        assert response.status_code == 401

    def test_upstream_500_passes_through(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "server error"}, 500)
            response = client.get(
                "/api/analytics/cycles",
                params={"device_id": DEVICE_ID},
                headers=AUTH_HEADER,
            )

        assert response.status_code == 500


# ── GET /api/analytics ────────────────────────────────────────────────────────

class TestGetFullAnalytics:

    def test_returns_200_with_analytics(self, client):
        analytics = {"total_cycles": 42, "avg_duration": 95}
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(analytics)
            response = client.get("/api/analytics", headers=AUTH_HEADER)

        assert response.status_code == 200
        assert response.json() == analytics

    def test_proxy_called_with_correct_url(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.get("/api/analytics", headers=AUTH_HEADER)

        mock_proxy.assert_called_once_with(
            "http://analytics-svc/analytics",
            "GET",
            headers={"X-User-Id": USER_ID},
        )

    def test_no_auth_returns_401(self, client):
        response = client.get("/api/analytics")
        assert response.status_code == 401

    def test_upstream_404_passes_through(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "not found"}, 404)
            response = client.get("/api/analytics", headers=AUTH_HEADER)

        assert response.status_code == 404


# ── PUT /api/analytics/devices/{device_id} ────────────────────────────────────

class TestUpdateDevice:

    def test_returns_200_on_successful_update(self, client):
        updated = {"id": DEVICE_ID, "name": "Laptop"}
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(updated)
            response = client.put(
                f"/api/analytics/devices/{DEVICE_ID}",
                # json={"name": "Laptop"},
                json={"device_name": "Laptop"},
                headers=AUTH_HEADER,
            )

        assert response.status_code == 200
        assert response.json() == updated

    def test_proxy_called_with_correct_url_and_method(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.put(
                f"/api/analytics/devices/{DEVICE_ID}",
                json={"device_name": "New Name"},
                headers=AUTH_HEADER,
            )

        call_args = mock_proxy.call_args
        assert call_args[0][0] == f"http://analytics-svc/devices/{DEVICE_ID}"
        assert call_args[0][1] == "PUT"

    def test_user_id_in_headers(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.put(
                f"/api/analytics/devices/{DEVICE_ID}",
                json={"device_name": "New Name"},
                headers=AUTH_HEADER,
            )

        assert mock_proxy.call_args[1]["headers"]["X-User-Id"] == USER_ID

    def test_content_type_json_in_headers(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.put(
                f"/api/analytics/devices/{DEVICE_ID}",
                json={"device_name": "New Name"},
                headers=AUTH_HEADER,
            )

        assert mock_proxy.call_args[1]["headers"]["Content-Type"] == "application/json"

    def test_body_contains_device_name(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.put(
                f"/api/analytics/devices/{DEVICE_ID}",
                json={"device_name": "Renamed"},
                headers=AUTH_HEADER,
            )

        body_bytes = mock_proxy.call_args[1]["body"]
        assert b"Renamed" in body_bytes

    def test_missing_body_returns_422(self, client):
        response = client.put(
            f"/api/analytics/devices/{DEVICE_ID}",
            headers=AUTH_HEADER,
        )
        assert response.status_code == 422

    def test_blank_device_name_returns_422(self, client):
        response = client.put(
            f"/api/analytics/devices/{DEVICE_ID}",
            json={"device_name": "   "},
            headers=AUTH_HEADER,
        )
        assert response.status_code == 422

    def test_no_auth_returns_401(self, client):
        response = client.put(
            f"/api/analytics/devices/{DEVICE_ID}",
            json={"device_name": "X"},
        )
        assert response.status_code == 401

    def test_upstream_404_passes_through(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "not found"}, 404)
            response = client.put(
                f"/api/analytics/devices/{DEVICE_ID}",
                json={"device_name": "X"},
                headers=AUTH_HEADER,
            )

        assert response.status_code == 404


# ── DELETE /api/analytics/devices/{device_id} ─────────────────────────────────

class TestDeleteDevice:

    def test_returns_200_on_successful_delete(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"deleted": True})
            response = client.delete(
                f"/api/analytics/devices/{DEVICE_ID}",
                headers=AUTH_HEADER,
            )

        assert response.status_code == 200
        assert response.json()["deleted"] is True

    def test_proxy_called_with_correct_url_and_method(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({})
            client.delete(
                f"/api/analytics/devices/{DEVICE_ID}",
                headers=AUTH_HEADER,
            )

        mock_proxy.assert_called_once_with(
            f"http://analytics-svc/devices/{DEVICE_ID}",
            "DELETE",
            headers={"X-User-Id": USER_ID},
        )

    def test_upstream_404_passes_through(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "not found"}, 404)
            response = client.delete(
                f"/api/analytics/devices/{DEVICE_ID}",
                headers=AUTH_HEADER,
            )

        assert response.status_code == 404

    def test_no_auth_returns_401(self, client):
        response = client.delete(f"/api/analytics/devices/{DEVICE_ID}")
        assert response.status_code == 401

    def test_upstream_500_passes_through(self, client):
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "server error"}, 500)
            response = client.delete(
                f"/api/analytics/devices/{DEVICE_ID}",
                headers=AUTH_HEADER,
            )

        assert response.status_code == 500


class TestToggleCycleExclusion:
    CYCLE_ID = "cycle-789"

    def test_exclude_cycle_returns_200(self, client):
        payload = {
            "status": "success",
            "message": "Cycle excluded from analytics",
            "device_id": DEVICE_ID,
            "cycle_id": self.CYCLE_ID,
            "is_excluded": True,
            "excluded_at": "2026-04-27T14:00:00",
        }
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(payload)
            response = client.post(
                f"/api/analytics/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}/exclude",
                headers=AUTH_HEADER,
            )

        assert response.status_code == 200
        assert response.json()["is_excluded"] is True

    def test_include_cycle_returns_200(self, client):
        payload = {
            "status": "success",
            "message": "Cycle included in analytics",
            "device_id": DEVICE_ID,
            "cycle_id": self.CYCLE_ID,
            "is_excluded": False,
            "excluded_at": None,
        }
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(payload)
            response = client.post(
                f"/api/analytics/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}/include",
                headers=AUTH_HEADER,
            )

        assert response.status_code == 200
        assert response.json()["is_excluded"] is False

    def test_exclude_cycle_proxies_to_processing_service(self, client):
        with (
            patch("app.routes.analytics.ANALYTICS_SERVICE_URL", "http://analytics-svc"),
            patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy,
        ):
            mock_proxy.return_value = _mock_response({})
            client.post(
                f"/api/analytics/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}/exclude",
                headers=AUTH_HEADER,
            )

        mock_proxy.assert_called_once_with(
            f"http://analytics-svc/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}/exclude",
            "POST",
            headers={"X-User-Id": USER_ID},
        )

    def test_include_cycle_proxies_to_analytics_service(self, client):
        with (
            patch("app.routes.analytics.ANALYTICS_SERVICE_URL", "http://analytics-svc"),
            patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy,
        ):
            mock_proxy.return_value = _mock_response({})
            client.post(
                f"/api/analytics/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}/include",
                headers=AUTH_HEADER,
            )

        mock_proxy.assert_called_once_with(
            f"http://analytics-svc/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}/include",
            "POST",
            headers={"X-User-Id": USER_ID},
        )

    def test_exclude_cycle_requires_auth(self, client):
        response = client.post(
            f"/api/analytics/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}/exclude",
        )
        assert response.status_code == 401


class TestDeleteCycle:
    CYCLE_ID = "cycle-789"

    def test_delete_cycle_returns_200(self, client):
        payload = {
            "status": "success",
            "message": "Cycle deleted from analytics",
            "device_id": DEVICE_ID,
            "cycle_id": self.CYCLE_ID,
            "deleted_sessions": 3,
        }
        with patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(payload)
            response = client.delete(
                f"/api/analytics/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}",
                headers=AUTH_HEADER,
            )

        assert response.status_code == 200
        assert response.json()["deleted_sessions"] == 3

    def test_delete_cycle_proxies_to_analytics_service(self, client):
        with (
            patch("app.routes.analytics.ANALYTICS_SERVICE_URL", "http://analytics-svc"),
            patch("app.routes.analytics.proxy_request", new_callable=AsyncMock) as mock_proxy,
        ):
            mock_proxy.return_value = _mock_response({})
            client.delete(
                f"/api/analytics/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}",
                headers=AUTH_HEADER,
            )

        mock_proxy.assert_called_once_with(
            f"http://analytics-svc/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}",
            "DELETE",
            headers={"X-User-Id": USER_ID},
        )

    def test_delete_cycle_requires_auth(self, client):
        response = client.delete(
            f"/api/analytics/devices/{DEVICE_ID}/cycles/{self.CYCLE_ID}",
        )
        assert response.status_code == 401


# ── Невалидный JWT — общий сценарий для всех защищённых эндпоинтов ────────────

class TestInvalidJwtAcrossEndpoints:

    @pytest.mark.parametrize("method,url", [
        ("GET",    "/api/analytics/devices"),
        ("GET",    "/api/analytics"),
        ("DELETE", f"/api/analytics/devices/{DEVICE_ID}"),
        ("DELETE", f"/api/analytics/devices/{DEVICE_ID}/cycles/cycle-789"),
        ("POST",   f"/api/analytics/devices/{DEVICE_ID}/cycles/cycle-789/exclude"),
    ])
    def test_invalid_jwt_returns_401(self, method, url):
        with (
            patch(
                "app.utils.auth_dependencies.verify_jwt_token",
                side_effect=HTTPException(status_code=401, detail="Invalid token"),
            ),
            patch("app.routes.analytics.ANALYTICS_SERVICE_URL", "http://analytics-svc"),
        ):
            from app.routes.analytics import router
            app = FastAPI()
            app.include_router(router)
            c = TestClient(app, raise_server_exceptions=False)
            response = getattr(c, method.lower())(url, headers=AUTH_HEADER)

        assert response.status_code == 401
