"""
Общие фикстуры и конфигурация pytest.
Мокаем переменные окружения ДО импорта любого модуля приложения,
чтобы config.py не падал при отсутствии .env файла.
"""
import os
import sys

# ── Принудительно подменяем env-переменные до импорта app ────────────────────
os.environ["JWT_SECRET"] = "test-secret-key"
os.environ["JWT_ALGORITHM"] = "HS256"
os.environ["USER_SERVICE_URL"] = "http://user-svc"
os.environ["PROCESSING_SERVICE_URL"] = "http://processing-svc"
os.environ["ANALYTICS_SERVICE_URL"] = "http://analytics-svc"

# ── Добавляем корень проекта в sys.path ───────────────────────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# ── Общие константы ───────────────────────────────────────────────────────────
TEST_USER_ID = "user-123"
TEST_DEVICE_ID = "device-456"
VALID_TOKEN = "Bearer valid.jwt.token"