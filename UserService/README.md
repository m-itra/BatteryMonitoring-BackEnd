# UserService

`UserService` отвечает за:

- регистрацию и вход пользователя
- получение данных текущего пользователя
- удаление пользователя
- административные операции по пользователям
- gRPC-валидацию существования пользователя для `ProcessingService`

## Порты

- HTTP: `8001`
- gRPC: `50051`

## Основные HTTP-эндпоинты

- `POST /register`
- `POST /login`
- `GET /users/me`
- `DELETE /users/me`
- `GET /admin/users`
- `GET /admin/stats`
- `DELETE /admin/users/{user_id}`
- `GET /health`

## gRPC

Сервис поднимает gRPC server с методом:

- `ValidateUser`

Proto-источник:

- Infrastructure/protos/user_service.proto

## Переменные окружения

Основные переменные:

- `ENVIRONMENT`
- `USER_DATABASE_URL` или `DATABASE_URL`
- `JWT_SECRET`
- `JWT_ALGORITHM`
- `JWT_EXPIRATION_HOURS`
- `USER_SERVICE_GRPC_URL`
- `PROCESSING_SERVICE_GRPC_URL`

Настройки читаются из:

- UserService/app/config.py
- Infrastructure/.env

## Локальный запуск
```powershell
python -m uvicorn app.main:app --host 0.0.0.0 --port 8001
```

## Тесты
```powershell
python -m pytest tests -q
```
