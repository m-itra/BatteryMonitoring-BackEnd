"""
Unit-тесты для UserService/app/routes/auth.py
Покрывает:
  POST /register — успех, дубликат email
  POST /login    — успех, неверный email, неверный пароль, генерация JWT
"""

import pytest
from unittest.mock import MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI


def _make_db_mocks(fetchone_values: list):
    """
    Создаёт цепочку моков: connection → cursor → fetchone.
    fetchone_values — список значений которые вернёт fetchone() при каждом вызове.
    """
    mock_cursor = MagicMock()
    mock_cursor.fetchone.side_effect = fetchone_values

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    # get_db_connection это contextmanager, __enter__ возвращает conn
    mock_conn_ctx = MagicMock()
    mock_conn_ctx.__enter__ = MagicMock(return_value=mock_conn)
    mock_conn_ctx.__exit__ = MagicMock(return_value=False)

    # get_db_cursor тоже contextmanager
    mock_cursor_ctx = MagicMock()
    mock_cursor_ctx.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor_ctx.__exit__ = MagicMock(return_value=False)

    return mock_conn_ctx, mock_cursor_ctx, mock_conn


@pytest.fixture()
def client():
    """Создает изолированный экземпляр приложения с роутером auth и возвращает TestClient для имитации HTTP-запросов."""
    from app.routes.auth import router
    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


# POST /register
class TestRegister:
    def test_successful_registration_returns_user(self, client):
        """Успешная регистрация возвращает данные пользователя"""
        mock_conn_ctx, mock_cursor_ctx, _ = _make_db_mocks([
            None,  # Пользователя с таким email не существует в БД
            {"user_id": "uuid-1", "email": "user@example.com", "name": "John"},  # INSERT RETURNING
        ])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
            patch("app.routes.auth.hash_password", return_value="hashed_secret"),
        ):
            response = client.post(
                "/register",
                json={"email": "user@example.com", "name": "John", "password": "secret"},
            )

        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "user@example.com"
        assert data["name"] == "John"

    def test_duplicate_email_returns_400(self, client):
        """Повторная регистрация с тем же email возвращает 400 'already registered'"""
        mock_conn_ctx, mock_cursor_ctx, _ = _make_db_mocks([
            {"email": "user@example.com"},  # email уже есть в БД
        ])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
        ):
            response = client.post(
                "/register",
                json={"email": "user@example.com", "name": "John", "password": "secret"},
            )

        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_password_is_hashed_not_stored_raw(self, client):
        """Вызывается ли hash_password перед сохранением в БД"""
        mock_conn_ctx, mock_cursor_ctx, _ = _make_db_mocks([
            None,
            {"user_id": "uuid-1", "email": "u@example.com", "name": "John"},
        ])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
            patch("app.routes.auth.hash_password", return_value="hashed") as mock_hash,
        ):
            client.post(
                "/register",
                json={"email": "u@example.com", "name": "John", "password": "secret"},
            )

        mock_hash.assert_called_once_with("secret")

    def test_missing_email_returns_422(self, client):
        """Отсутствие email возвращает 422"""
        response = client.post("/register", json={"name": "John", "password": "secret"})
        assert response.status_code == 422

    def test_missing_name_returns_422(self, client):
        """Отсутствие name возвращает 422"""
        response = client.post("/register", json={"email": "u@example.com", "password": "secret"})
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        """Отсутствие password возвращает 422"""
        response = client.post("/register", json={"email": "u@example.com", "name": "John"})
        assert response.status_code == 422

    def test_commit_called_after_insert(self, client):
        """Вызывается ли conn.commit() после успешной вставки"""
        mock_conn_ctx, mock_cursor_ctx, mock_conn = _make_db_mocks([
            None,
            {"user_id": "uuid-1", "email": "u@example.com", "name": "John"},
        ])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
            patch("app.routes.auth.hash_password", return_value="hashed"),
        ):
            client.post(
                "/register",
                json={"email": "u@example.com", "name": "John", "password": "secret"},
            )

        mock_conn.commit.assert_called_once()


# POST /login
class TestLogin:
    def test_successful_login(self, client):
        """Успешный вход возвращает access_token и данные пользователя"""
        mock_conn_ctx, mock_cursor_ctx, _ = _make_db_mocks([
            {
                "user_id": "uuid-1",
                "email": "user@example.com",
                "name": "John",
                "password_hash": "hashed",
            }
        ])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
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
        """Пользователь не найден возвращает 401"""
        mock_conn_ctx, mock_cursor_ctx, _ = _make_db_mocks([None])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
        ):
            response = client.post(
                "/login",
                json={"email": "noone@example.com", "password": "secret"},
            )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_wrong_password_returns_401(self, client):
        """Неверный пароль возвращает 401"""
        mock_conn_ctx, mock_cursor_ctx, _ = _make_db_mocks([
            {
                "user_id": "uuid-1",
                "email": "user@example.com",
                "name": "John",
                "password_hash": "hashed",
            }
        ])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
            patch("app.routes.auth.verify_password", return_value=False),
        ):
            response = client.post(
                "/login",
                json={"email": "user@example.com", "password": "wrongpass"},
            )

        assert response.status_code == 401
        assert "Invalid credentials" in response.json()["detail"]

    def test_create_jwt_called_with_correct_args(self, client):
        """create_jwt_token вызывается с правильными аргументами"""
        mock_conn_ctx, mock_cursor_ctx, _ = _make_db_mocks([
            {
                "user_id": "uuid-1",
                "email": "user@example.com",
                "name": "John",
                "password_hash": "hashed",
            }
        ])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
            patch("app.routes.auth.verify_password", return_value=True),
            patch("app.routes.auth.create_jwt_token", return_value="t") as mock_jwt,
        ):
            client.post(
                "/login",
                json={"email": "user@example.com", "password": "secret"},
            )

        mock_jwt.assert_called_once_with("uuid-1", "user@example.com", "John")

    def test_verify_password_called_with_correct_args(self, client):
        """verify_password вызывается с паролем из запроса и хешем из БД"""
        mock_conn_ctx, mock_cursor_ctx, _ = _make_db_mocks([
            {
                "user_id": "uuid-1",
                "email": "user@example.com",
                "name": "John",
                "password_hash": "stored_hash",
            }
        ])

        with (
            patch("app.routes.auth.get_db_connection", return_value=mock_conn_ctx),
            patch("app.routes.auth.get_db_cursor", return_value=mock_cursor_ctx),
            patch("app.routes.auth.verify_password", return_value=True) as mock_verify,
            patch("app.routes.auth.create_jwt_token", return_value="t"),
        ):
            client.post(
                "/login",
                json={"email": "user@example.com", "password": "secret"},
            )

        mock_verify.assert_called_once_with("secret", "stored_hash")

    def test_missing_email_returns_422(self, client):
        """Отсутствие email возвращает 422"""
        response = client.post("/login", json={"password": "secret"})
        assert response.status_code == 422

    def test_missing_password_returns_422(self, client):
        """Отсутствие password возвращает 422"""
        response = client.post("/login", json={"email": "u@example.com"})
        assert response.status_code == 422
