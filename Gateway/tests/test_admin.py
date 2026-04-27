from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient

ADMIN_PAYLOAD = {"user_id": "admin-123", "role": "admin"}
USER_PAYLOAD = {"user_id": "user-123", "role": "user"}
AUTH_HEADER = {"Authorization": "Bearer sometoken"}


def _mock_response(data: dict, status: int = 200):
    mock_response = MagicMock()
    mock_response.json.return_value = data
    mock_response.status_code = status
    return mock_response


@pytest.fixture()
def admin_client():
    with (
        patch("app.utils.auth_dependencies.verify_jwt_token", return_value=ADMIN_PAYLOAD),
        patch("app.routes.admin.USER_SERVICE_URL", "http://user-svc"),
        patch("app.routes.admin.ANALYTICS_SERVICE_URL", "http://analytics-svc"),
    ):
        from app.routes.admin import router

        app = FastAPI()
        app.include_router(router)
        yield TestClient(app, raise_server_exceptions=False)


class TestAdminRoutes:
    def test_get_admin_users_returns_200(self, admin_client):
        payload = {
            "users": [
                {
                    "user_id": "uuid-1",
                    "email": "user@example.com",
                    "name": "John",
                    "role": "user",
                    "created_at": "2026-04-28T00:00:00",
                }
            ]
        }
        with patch("app.routes.admin.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(payload)
            response = admin_client.get("/api/admin/users", headers=AUTH_HEADER)

        assert response.status_code == 200
        assert response.json()["users"][0]["role"] == "user"

    def test_get_admin_users_proxies_to_user_service(self, admin_client):
        with patch("app.routes.admin.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"users": []})
            admin_client.get("/api/admin/users", headers=AUTH_HEADER)

        mock_proxy.assert_called_once_with("http://user-svc/admin/users", "GET")

    def test_get_admin_stats_aggregates_two_services(self, admin_client):
        responses = [
            _mock_response({"users_count": 2}),
            _mock_response(
                {
                    "devices_count": 5,
                    "active_sessions_count": 1,
                    "completed_sessions_count": 10,
                    "interrupted_sessions_count": 2,
                    "equivalent_cycles_count": 4,
                    "excluded_cycles_count": 1,
                }
            ),
        ]
        with patch("app.routes.admin.proxy_request", new_callable=AsyncMock, side_effect=responses):
            response = admin_client.get("/api/admin/stats", headers=AUTH_HEADER)

        assert response.status_code == 200
        assert response.json()["users_count"] == 2
        assert response.json()["devices_count"] == 5

    def test_delete_admin_user_proxies_to_user_service(self, admin_client):
        payload = {"user_id": "uuid-1", "deleted_devices": 2, "message": "User and battery data deleted"}
        with patch("app.routes.admin.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(payload)
            response = admin_client.delete("/api/admin/users/uuid-1", headers=AUTH_HEADER)

        assert response.status_code == 200
        mock_proxy.assert_called_once_with("http://user-svc/admin/users/uuid-1", "DELETE")

    def test_non_admin_gets_403(self):
        with (
            patch("app.utils.auth_dependencies.verify_jwt_token", return_value=USER_PAYLOAD),
            patch("app.routes.admin.USER_SERVICE_URL", "http://user-svc"),
            patch("app.routes.admin.ANALYTICS_SERVICE_URL", "http://analytics-svc"),
        ):
            from app.routes.admin import router

            app = FastAPI()
            app.include_router(router)
            client = TestClient(app, raise_server_exceptions=False)
            response = client.get("/api/admin/users", headers=AUTH_HEADER)

        assert response.status_code == 403

    def test_missing_auth_returns_401(self, admin_client):
        response = admin_client.get("/api/admin/users")
        assert response.status_code == 401

    def test_service_unavailable_passes_503(self, admin_client):
        with patch(
            "app.routes.admin.proxy_request",
            new_callable=AsyncMock,
            side_effect=HTTPException(status_code=503, detail="Service unavailable"),
        ):
            response = admin_client.get("/api/admin/users", headers=AUTH_HEADER)

        assert response.status_code == 503
