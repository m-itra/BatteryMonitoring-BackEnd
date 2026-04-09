"""
Unit-тесты для UserService/app/utils/auth_utils.py
Покрывает:
  hash_password     - хеширование пароля
  verify_password   - проверка пароля
  create_jwt_token  - генерация JWT токена
"""

import pytest
import jwt
from unittest.mock import patch


# hash_password
class TestHashPassword:

    def test_returns_string(self):
        """Результат хеширования является строкой"""
        from app.utils.auth_utils import hash_password
        result = hash_password("mypassword")
        assert isinstance(result, str)

    def test_hash_is_not_equal_to_original(self):
        """Хеш не совпадает с исходным паролем"""
        from app.utils.auth_utils import hash_password
        result = hash_password("mypassword")
        assert result != "mypassword"

    def test_same_password_produces_different_hashes(self):
        """Два хеша одного пароля различаются (bcrypt использует соль)"""
        from app.utils.auth_utils import hash_password
        hash1 = hash_password("mypassword")
        hash2 = hash_password("mypassword")
        assert hash1 != hash2

    def test_hash_starts_with_bcrypt_prefix(self):
        """Хеш начинается с префикса bcrypt '$2b$'"""
        from app.utils.auth_utils import hash_password
        result = hash_password("mypassword")
        assert result.startswith("$2b$")

    def test_empty_password_can_be_hashed(self):
        """Пустой пароль хешируется без ошибок"""
        from app.utils.auth_utils import hash_password
        result = hash_password("")
        assert isinstance(result, str)
        assert result.startswith("$2b$")


# verify_password
class TestVerifyPassword:

    @pytest.mark.parametrize("password,expected", [
        ("secret123", True),        # верный пароль
        ("wrongpass", False),       # неверный пароль
        ("", False),                # пустой пароль против хеша "secret123"
        ("SECRET123", False),       # другой регистр
        ("secret1234", False),      # похожий, но не точный
    ])
    def test_verify_password_parametrized(self, password, expected):
        """Параметризованная проверка различных паролей"""
        from app.utils.auth_utils import hash_password, verify_password

        hashed = hash_password("secret123")
        assert verify_password(password, hashed) is expected

    def test_empty_password_correct_returns_true(self):
        """Пустой пароль против хеша пустого пароля возвращает True"""
        from app.utils.auth_utils import hash_password, verify_password

        hashed = hash_password("")
        assert verify_password("", hashed) is True


# create_jwt_token
class TestCreateJwtToken:
    SECRET = "test-secret-key"
    ALGORITHM = "HS256"
    EXPIRATION_HOURS = 24

    @pytest.fixture(autouse=True)
    def patch_config(self):
        with (
            patch("app.utils.auth_utils.JWT_SECRET", self.SECRET),
            patch("app.utils.auth_utils.JWT_ALGORITHM", self.ALGORITHM),
            patch("app.utils.auth_utils.JWT_EXPIRATION_HOURS", self.EXPIRATION_HOURS),
        ):
            yield

    def test_returns_string(self):
        """Токен является строкой"""
        from app.utils.auth_utils import create_jwt_token
        token = create_jwt_token("user-1", "user@example.com", "John")
        assert isinstance(token, str)

    def test_token_contains_three_parts(self):
        """JWT состоит из трёх частей разделённых точкой"""
        from app.utils.auth_utils import create_jwt_token
        token = create_jwt_token("user-1", "user@example.com", "John")
        assert len(token.split(".")) == 3

    def test_payload_structure_and_fields(self):
        """Payload содержит все ожидаемые поля и корректные значения"""
        from app.utils.auth_utils import create_jwt_token

        token = create_jwt_token("user-123", "test@example.com", "Alice")
        payload = jwt.decode(token, self.SECRET, algorithms=[self.ALGORITHM])

        assert payload["user_id"] == "user-123"
        assert payload["email"] == "test@example.com"
        assert payload["name"] == "Alice"
        assert "exp" in payload
        assert "iat" in payload

    def test_expiration_is_24_hours(self):
        """Токен истекает через 24 часа"""
        from app.utils.auth_utils import create_jwt_token

        token = create_jwt_token("user-1", "user@example.com", "John")
        payload = jwt.decode(token, self.SECRET, algorithms=[self.ALGORITHM])

        assert payload["exp"] - payload["iat"] == pytest.approx(
            self.EXPIRATION_HOURS * 3600, abs=1
        )

    def test_different_users_produce_different_tokens(self):
        """Разные пользователи имеют разные токены"""
        from app.utils.auth_utils import create_jwt_token

        token1 = create_jwt_token("user-1", "a@example.com", "Alice")
        token2 = create_jwt_token("user-2", "b@example.com", "Bob")

        assert token1 != token2

    def test_token_invalid_with_wrong_secret(self):
        """Токен не декодируется с неверным секретом"""
        from app.utils.auth_utils import create_jwt_token

        token = create_jwt_token("user-1", "user@example.com", "John")

        with pytest.raises(jwt.InvalidTokenError):
            jwt.decode(token, "wrong-secret", algorithms=[self.ALGORITHM])
