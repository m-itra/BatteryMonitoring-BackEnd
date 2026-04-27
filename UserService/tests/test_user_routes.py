from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


class FakeSessionContext:
    def __init__(self, session):
        self.session = session

    async def __aenter__(self):
        return self.session

    async def __aexit__(self, exc_type, exc, tb):
        return False


def make_fake_session():
    return SimpleNamespace(
        commit=AsyncMock(),
        rollback=AsyncMock(),
    )


def make_user(
    user_id="uuid-1",
    email="user@example.com",
    name="John",
    password_hash="hashed",
    role="user",
):
    return SimpleNamespace(
        user_id=user_id,
        email=email,
        name=name,
        password_hash=password_hash,
        role=role,
        created_at="2026-04-28T00:00:00",
    )


@pytest.fixture()
def client():
    from app.routes import admin, auth

    app = FastAPI()
    app.include_router(auth.router)
    app.include_router(admin.router)
    return TestClient(app)


class TestRegister:
    def test_successful_registration_returns_user(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_email", new_callable=AsyncMock, return_value=None),
            patch(
                "app.routes.auth.create_user",
                new_callable=AsyncMock,
                return_value=make_user(),
            ),
            patch("app.routes.auth.hash_password", return_value="hashed_secret"),
        ):
            response = client.post(
                "/register",
                json={"email": "user@example.com", "name": "John", "password": "password123"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@example.com"
        assert data["name"] == "John"
        assert data["role"] == "user"

    def test_duplicate_email_returns_400(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_email", new_callable=AsyncMock, return_value=make_user()),
        ):
            response = client.post(
                "/register",
                json={"email": "user@example.com", "name": "John", "password": "password123"},
            )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_password_is_hashed_not_stored_raw(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_email", new_callable=AsyncMock, return_value=None),
            patch("app.routes.auth.create_user", new_callable=AsyncMock, return_value=make_user()),
            patch("app.routes.auth.hash_password", return_value="hashed") as mock_hash,
        ):
            client.post(
                "/register",
                json={"email": "u@example.com", "name": "John", "password": "password123"},
            )

        mock_hash.assert_called_once_with("password123")

    def test_missing_email_returns_422(self, client):
        response = client.post("/register", json={"name": "John", "password": "password123"})
        assert response.status_code == 422

    def test_missing_name_returns_422(self, client):
        response = client.post("/register", json={"email": "u@example.com", "password": "password123"})
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        response = client.post("/register", json={"email": "u@example.com", "name": "John"})
        assert response.status_code == 422

    def test_blank_name_returns_422(self, client):
        response = client.post(
            "/register",
            json={"email": "u@example.com", "name": "   ", "password": "password123"},
        )
        assert response.status_code == 422

    def test_short_password_returns_422(self, client):
        response = client.post(
            "/register",
            json={"email": "u@example.com", "name": "John", "password": "short"},
        )
        assert response.status_code == 422

    def test_commit_called_after_insert(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_email", new_callable=AsyncMock, return_value=None),
            patch("app.routes.auth.create_user", new_callable=AsyncMock, return_value=make_user()),
            patch("app.routes.auth.hash_password", return_value="hashed"),
        ):
            client.post(
                "/register",
                json={"email": "u@example.com", "name": "John", "password": "password123"},
            )

        session.commit.assert_awaited_once()


class TestLogin:
    def test_successful_login(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_email", new_callable=AsyncMock, return_value=make_user()),
            patch("app.routes.auth.verify_password", return_value=True),
            patch("app.routes.auth.create_jwt_token", return_value="jwt.token.here"),
        ):
            response = client.post(
                "/login",
                json={"email": "user@example.com", "password": "secret"},
            )

        data = response.json()
        assert response.status_code == 200
        assert data["access_token"] == "jwt.token.here"
        assert data["user"]["email"] == "user@example.com"
        assert data["user"]["name"] == "John"

    def test_user_not_found_returns_401(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_email", new_callable=AsyncMock, return_value=None),
        ):
            response = client.post(
                "/login",
                json={"email": "noone@example.com", "password": "secret"},
            )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_wrong_password_returns_401(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_email", new_callable=AsyncMock, return_value=make_user()),
            patch("app.routes.auth.verify_password", return_value=False),
        ):
            response = client.post(
                "/login",
                json={"email": "user@example.com", "password": "wrongpass"},
            )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_create_jwt_called_with_correct_args(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_email", new_callable=AsyncMock, return_value=make_user()),
            patch("app.routes.auth.verify_password", return_value=True),
            patch("app.routes.auth.create_jwt_token", return_value="t") as mock_jwt,
        ):
            client.post(
                "/login",
                json={"email": "user@example.com", "password": "secret"},
            )

        mock_jwt.assert_called_once_with("uuid-1", "user@example.com", "John", "user")

    def test_login_returns_user_role(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch(
                "app.routes.auth.get_user_by_email",
                new_callable=AsyncMock,
                return_value=make_user(role="admin"),
            ),
            patch("app.routes.auth.verify_password", return_value=True),
            patch("app.routes.auth.create_jwt_token", return_value="jwt.token.here"),
        ):
            response = client.post(
                "/login",
                json={"email": "user@example.com", "password": "secret"},
            )

        assert response.status_code == 200
        assert response.json()["user"]["role"] == "admin"

    def test_verify_password_called_with_correct_args(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch(
                "app.routes.auth.get_user_by_email",
                new_callable=AsyncMock,
                return_value=make_user(password_hash="stored_hash"),
            ),
            patch("app.routes.auth.verify_password", return_value=True) as mock_verify,
            patch("app.routes.auth.create_jwt_token", return_value="t"),
        ):
            client.post(
                "/login",
                json={"email": "user@example.com", "password": "secret"},
            )

        mock_verify.assert_called_once_with("secret", "stored_hash")

    def test_missing_email_returns_422(self, client):
        response = client.post("/login", json={"password": "secret"})
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        response = client.post("/login", json={"email": "u@example.com"})
        assert response.status_code == 422

    def test_blank_password_returns_422(self, client):
        response = client.post("/login", json={"email": "u@example.com", "password": "   "})
        assert response.status_code == 422


class TestDeleteCurrentUser:
    def test_successful_delete_removes_user_after_battery_cleanup(self, client):
        session = make_fake_session()
        cleanup_result = SimpleNamespace(success=True, deleted_devices=2, message="Deleted 2 device(s)")

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_id", new_callable=AsyncMock, return_value=make_user()),
            patch(
                "app.routes.auth.delete_user_battery_data_via_grpc",
                new_callable=AsyncMock,
                return_value=cleanup_result,
            ),
            patch("app.routes.auth.delete_user", new_callable=AsyncMock) as mock_delete_user,
        ):
            response = client.delete("/users/me", headers={"X-User-Id": "uuid-1"})

        assert response.status_code == 200
        assert response.json()["deleted_devices"] == 2
        mock_delete_user.assert_awaited_once()
        session.commit.assert_awaited_once()

    def test_delete_user_not_found_returns_404(self, client):
        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_id", new_callable=AsyncMock, return_value=None),
            patch("app.routes.auth.delete_user_battery_data_via_grpc", new_callable=AsyncMock) as mock_cleanup,
        ):
            response = client.delete("/users/me", headers={"X-User-Id": "missing-user"})

        assert response.status_code == 404
        mock_cleanup.assert_not_called()
        session.commit.assert_not_awaited()

    def test_delete_rolls_back_when_battery_cleanup_fails(self, client):
        from app.routes.auth import BatteryDataCleanupError

        session = make_fake_session()

        with (
            patch("app.routes.auth.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.auth.get_user_by_id", new_callable=AsyncMock, return_value=make_user()),
            patch(
                "app.routes.auth.delete_user_battery_data_via_grpc",
                new_callable=AsyncMock,
                side_effect=BatteryDataCleanupError("grpc down"),
            ),
            patch("app.routes.auth.delete_user", new_callable=AsyncMock) as mock_delete_user,
        ):
            response = client.delete("/users/me", headers={"X-User-Id": "uuid-1"})

        assert response.status_code == 502
        mock_delete_user.assert_not_called()
        session.rollback.assert_awaited()

    def test_missing_x_user_id_returns_422(self, client):
        response = client.delete("/users/me")
        assert response.status_code == 422


class TestAdminRoutes:
    def test_get_admin_users_returns_users(self, client):
        session = make_fake_session()
        users = [make_user(user_id="uuid-1"), make_user(user_id="uuid-2", email="other@example.com", role="admin")]

        with (
            patch("app.routes.admin.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.admin.list_users", new_callable=AsyncMock, return_value=users),
        ):
            response = client.get("/admin/users")

        assert response.status_code == 200
        assert len(response.json()["users"]) == 2
        assert response.json()["users"][1]["role"] == "admin"

    def test_get_admin_stats_returns_user_count(self, client):
        session = make_fake_session()
        session.execute = AsyncMock(return_value=SimpleNamespace(scalar_one=lambda: 3))

        with patch("app.routes.admin.get_db_session", return_value=FakeSessionContext(session)):
            response = client.get("/admin/stats")

        assert response.status_code == 200
        assert response.json()["users_count"] == 3

    def test_delete_admin_user_runs_cleanup_and_delete(self, client):
        session = make_fake_session()
        cleanup_payload = SimpleNamespace(
            user_id="uuid-1",
            deleted_devices=4,
            message="User and battery data deleted",
        )

        with (
            patch("app.routes.admin.get_db_session", return_value=FakeSessionContext(session)),
            patch("app.routes.admin.get_user_by_id", new_callable=AsyncMock, return_value=make_user()),
            patch(
                "app.routes.admin.delete_user_with_battery_cleanup",
                new_callable=AsyncMock,
                return_value=cleanup_payload,
            ),
            patch("app.routes.admin.delete_user", new_callable=AsyncMock) as mock_delete_user,
        ):
            response = client.delete("/admin/users/uuid-1")

        assert response.status_code == 200
        assert response.json()["deleted_devices"] == 4
        mock_delete_user.assert_awaited_once()
        session.commit.assert_awaited_once()
