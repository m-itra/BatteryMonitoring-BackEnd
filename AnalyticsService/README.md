# AnalyticsService

`AnalyticsService` отвечает за чтение аналитики:

- список устройств пользователя
- детали по одному устройству
- активные сессии, эквивалентные циклы, 
- история устройств

## Порт

- HTTP: `8003`

## Основные HTTP-эндпоинты

- `GET /analytics`
- `GET /devices`
- `GET /devices/{device_id}`
- `PUT /devices/{device_id}`
- `DELETE /devices/{device_id}`
- `GET /cycles`
- `POST /devices/{device_id}/cycles/{cycle_id}/exclude`
- `POST /devices/{device_id}/cycles/{cycle_id}/include`
- `DELETE /devices/{device_id}/cycles/{cycle_id}`
- `GET /admin/stats`
- `GET /health`

## Переменные окружения

Основные переменные:

- `ENVIRONMENT`
- `BATTERY_DATABASE_URL` или `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`

Настройки читаются из:

- AnalyticsService/app/config.py
- Infrastructure/.env

## Локальный запуск
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8003
```

## Тесты
```powershell
python -m pytest tests -q
```
