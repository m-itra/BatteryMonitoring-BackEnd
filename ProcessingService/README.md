# ProcessingService

`ProcessingService` отвечает за:

- приём батчей телеметрии батареи
- дедупликацию сэмплов
- расчёт активной, завершённой/прерванной сессии
- построение эквивалентных циклов
- удаление данных пользователя по gRPC-запросу из `UserService`

## Порты

- HTTP: `8002`
- gRPC: `50052`

## Основные HTTP-эндпоинты

- `POST /logs/batch`
- `GET /health`

## gRPC

Сервис:

- как клиент вызывает `UserService.ValidateUser`
- как сервер обслуживает `BatteryDataService.DeleteUserBatteryData`

Proto-источники:

- [Infrastructure/protos/user_service.proto](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/protos/user_service.proto)
- [Infrastructure/protos/battery_data_service.proto](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/protos/battery_data_service.proto)

## Переменные окружения

Основные переменные:

- `ENVIRONMENT`
- `BATTERY_DATABASE_URL` или `DATABASE_URL`
- `USER_SERVICE_GRPC_URL`
- `PROCESSING_SERVICE_GRPC_URL`
- `MIN_SESSION_DISCHARGE_PERCENT`

Настройки читаются из:

- [ProcessingService/app/config.py](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/ProcessingService/app/config.py)
- [Infrastructure/.env](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/.env)

## Локальный запуск
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8002
```

## Тесты
```powershell
python -m pytest tests -q
```
