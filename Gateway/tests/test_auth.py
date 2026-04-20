"""
Unit-тесты для app/routes/auth.py
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


def _mock_response(data: dict, status: int = 200):
    m = MagicMock()
    m.json.return_value = data
    m.status_code = status
    return m


@pytest.fixture()
def client():
    with patch("app.routes.auth.USER_SERVICE_URL", "http://user-svc"):
        from app.routes.auth import router
        app = FastAPI()
        app.include_router(router)
        yield TestClient(app, raise_server_exceptions=False)


# ── POST /api/auth/register ───────────────────────────────────────────────────

class TestRegister:

    def test_successful_registration_returns_201(self, client):
        payload = {"email": "user@example.com", "name": "John Doe", "password": "password123"}
        with patch("app.routes.auth.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"message": "created"}, 201)
            response = client.post("/api/auth/register", json=payload)

        assert response.status_code == 201
        assert response.json()["message"] == "created"

    def test_proxy_called_with_json_body(self, client):
        payload = {"email": "user@example.com", "name": "John Doe", "password": "password123"}
        with patch("app.routes.auth.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({}, 201)
            client.post("/api/auth/register", json=payload)

        call_args = mock_proxy.call_args
        assert call_args[0][0] == "http://user-svc/register"
        assert call_args[0][1] == "POST"
        assert call_args[1]["headers"]["Content-Type"] == "application/json"
        body = call_args[1]["body"]
        assert b"user@example.com" in body

    def test_duplicate_email_passes_through_409(self, client):
        with patch("app.routes.auth.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "already exists"}, 409)
            response = client.post(
                "/api/auth/register",
                json={"email": "dup@example.com", "name": "John Doe", "password": "password123"},
            )

        assert response.status_code == 409

    def test_blank_name_returns_422(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "a@b.com", "name": "   ", "password": "password123"},
        )
        assert response.status_code == 422

    def test_short_password_returns_422(self, client):
        response = client.post(
            "/api/auth/register",
            json={"email": "a@b.com", "name": "John", "password": "short"},
        )
        assert response.status_code == 422

    def test_missing_email_returns_422(self, client):
        response = client.post("/api/auth/register", json={"name": "John", "password": "secret"})
        assert response.status_code == 422

    def test_missing_name_returns_422(self, client):
        response = client.post("/api/auth/register", json={"email": "a@b.com", "password": "secret"})
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        response = client.post("/api/auth/register", json={"email": "a@b.com", "name": "John"})
        assert response.status_code == 422

    def test_empty_body_returns_422(self, client):
        response = client.post("/api/auth/register", json={})
        assert response.status_code == 422


# ── POST /api/auth/login ──────────────────────────────────────────────────────

class TestLogin:

    def test_successful_login_returns_token(self, client):
        token_data = {"access_token": "jwt.token.here", "token_type": "bearer"}
        with patch("app.routes.auth.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(token_data, 200)
            response = client.post(
                "/api/auth/login",
                json={"email": "user@example.com", "password": "secret"},
            )

        assert response.status_code == 200
        assert response.json()["access_token"] == "jwt.token.here"

    def test_successful_login_sets_httponly_cookie(self, client):
        token_data = {"access_token": "jwt.token.here", "token_type": "bearer"}
        with patch("app.routes.auth.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response(token_data, 200)
            response = client.post(
                "/api/auth/login",
                json={"email": "user@example.com", "password": "secret"},
            )

        assert "access_token" in response.cookies
        set_cookie = response.headers.get("set-cookie", "")
        assert "httponly" in set_cookie.lower()

    def test_wrong_credentials_returns_401_no_cookie(self, client):
        with patch("app.routes.auth.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"error": "unauthorized"}, 401)
            response = client.post(
                "/api/auth/login",
                json={"email": "user@example.com", "password": "wrong"},
            )

        assert response.status_code == 401
        assert "access_token" not in response.cookies

    def test_proxy_called_with_correct_url(self, client):
        with patch("app.routes.auth.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"access_token": "t"}, 200)
            client.post(
                "/api/auth/login",
                json={"email": "u@example.com", "password": "p"},
            )

        call_args = mock_proxy.call_args
        assert call_args[0][0] == "http://user-svc/login"
        assert call_args[0][1] == "POST"

    def test_service_unavailable_passes_503(self, client):
        from fastapi import HTTPException
        with patch(
                "app.routes.auth.proxy_request",
                new_callable=AsyncMock,
                side_effect=HTTPException(status_code=503, detail="Service unavailable"),
        ):
            response = client.post(
                "/api/auth/login",
                json={"email": "u@example.com", "password": "p"},
            )

        assert response.status_code == 503

    def test_missing_email_returns_422(self, client):
        response = client.post("/api/auth/login", json={"password": "x"})
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        response = client.post("/api/auth/login", json={"email": "a@b.com"})
        assert response.status_code == 422

    def test_response_without_token_does_not_set_cookie(self, client):
        with patch("app.routes.auth.proxy_request", new_callable=AsyncMock) as mock_proxy:
            mock_proxy.return_value = _mock_response({"message": "ok"}, 200)
            response = client.post(
                "/api/auth/login",
                json={"email": "u@example.com", "password": "p"},
            )

        assert "access_token" not in response.cookies

    def test_blank_login_password_returns_422(self, client):
        response = client.post(
            "/api/auth/login",
            json={"email": "u@example.com", "password": "   "},
        )
        assert response.status_code == 422

    def test_logout_deletes_access_token_cookie(self, client):
        client.cookies.set("access_token", "jwt.token.here")
        response = client.post("/api/auth/logout")

        assert response.status_code == 200
        set_cookie = response.headers.get("set-cookie", "")
        assert "access_token=" in set_cookie
        assert "max-age=0" in set_cookie.lower()
