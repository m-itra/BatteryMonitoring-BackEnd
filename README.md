# BatteryMonitoring BackEnd

BatteryMonitoring состоит из нескольких сервисов:

- `Gateway` — внешний HTTP-вход
- `UserService` — пользователи, аутентификация и администрирование
- `ProcessingService` — приём батчей телеметрии и расчёт сессий/циклов
- `AnalyticsService` — чтение аналитики и истории по устройствам
- `Infrastructure` — Docker Compose, Alembic-миграции и gRPC proto/stubs

## Сборка и запуск в Docker

### Что нужно

1. Docker Desktop или совместимый `docker compose`
2. заполненный файл [Infrastructure/.env](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/.env)
3. если нужен полный стек с фронтендом, рядом с этим репозиторием должен лежать репозиторий `BatteryMonitoring-FrontEnd`, потому что `docker-compose.yml` собирает `frontend` из пути `../../BatteryMonitoring-FrontEnd`

### Поднять всё приложение

```powershell
docker compose -f Infrastructure/docker-compose.yml up -d --build
```
После запуска приложение будет доступно по адресу `http://localhost:3000`.


### Поднять только backend

Если фронтенд-репозиторий не нужен или ещё не лежит рядом, можно поднять только backend-сервисы:

```powershell
docker compose -f Infrastructure/docker-compose.yml up -d --build user-db battery-db user-db-migrations battery-db-migrations user-service processing-service analytics-service gateway
```

## Локальный запуск без Docker

Все сервисы читают настройки из [Infrastructure/.env](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/.env).  
В нём сейчас разделены:

- локальные переменные (`USER_DATABASE_URL`, `BATTERY_DATABASE_URL`, `USER_SERVICE_URL` и так далее)
- docker-переменные с префиксом `DOCKER_`

Локальный запуск и миграции описаны в README соответствующих сервисов и в [Infrastructure/README.md](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/README.md).
