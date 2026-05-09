# Gateway

`Gateway` отвечает за:

- проверку JWT и cookie
- проксирование auth-запросов в `UserService`
- проксирование telemetry batch в `ProcessingService`
- сбор analytics-ответов из `AnalyticsService`

## Порт

- HTTP: `8000`

## Основные HTTP-эндпоинты

- `POST /api/auth/register`
- `POST /api/auth/login`
- `POST /api/auth/logout`
- `GET /api/auth/me`
- `DELETE /api/auth/me`
- `POST /api/battery/logs/batch`
- `GET /api/analytics`
- `GET /api/analytics/devices`
- `GET /api/analytics/devices/{device_id}`
- `PUT /api/analytics/devices/{device_id}`
- `DELETE /api/analytics/devices/{device_id}`
- `GET /api/analytics/cycles`
- `GET /api/admin/users`
- `GET /api/admin/stats`
- `DELETE /api/admin/users/{user_id}`
- `GET /health`

## Переменные окружения

Основные переменные:

- `ENVIRONMENT`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `AUTH_COOKIE_SECURE`
- `AUTH_COOKIE_SAMESITE`
- `AUTH_COOKIE_MAX_AGE_SECONDS`
- `USER_SERVICE_URL`
- `PROCESSING_SERVICE_URL`
- `ANALYTICS_SERVICE_URL`

Настройки читаются из:

- [Gateway/app/config.py](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Gateway/app/config.py)
- [Infrastructure/.env](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/.env)

## Локальный запуск
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000
```

## Тесты
```powershell
python -m pytest tests -q
```
