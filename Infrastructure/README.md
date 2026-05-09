# Infrastructure

Папка `Infrastructure` отвечает за:

- общий `docker-compose.yml`
- файл окружения `.env`
- Alembic-миграции для `userdb` и `batterydb`
- proto-файлы gRPC
- служебные скрипты для миграций и генерации stubs

## Файл `.env`

В [Infrastructure/.env](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/.env) используются две группы переменных:

- локальные переменные для запуска сервисов и миграций вне Docker:
  - `USER_DATABASE_URL`
  - `BATTERY_DATABASE_URL`
  - `USER_SERVICE_URL`
  - `PROCESSING_SERVICE_URL`
  - `ANALYTICS_SERVICE_URL`
  - `USER_SERVICE_GRPC_URL`
  - `PROCESSING_SERVICE_GRPC_URL`
- docker-переменные с префиксом `DOCKER_`, которые использует `docker-compose.yml`

Это позволяет держать локальную конфигурацию и Docker Compose в одном файле, не смешивая адреса и учётные данные.

## Docker Compose

Основной compose-файл:

- [Infrastructure/docker-compose.yml](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/docker-compose.yml)

Запуск полного стека:

```powershell
docker compose up -d --build
```

## Миграции базы данных

Схема базы данных управляется через Alembic.

Источником структуры служат SQLAlchemy-модели сервисов:

- для `userdb` — модели из `UserService`
- для `batterydb` — модели из `ProcessingService`

Alembic загружает `target_metadata` из этих моделей в:

- [Infrastructure/migrations/user-db/env.py](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/migrations/user-db/env.py)
- [Infrastructure/migrations/battery-db/env.py](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/migrations/battery-db/env.py)

### Порядок выбора URL для миграций

Alembic выбирает адрес базы данных в следующем порядке:

1. Сначала используется специализированная переменная окружения:
   - `USER_DATABASE_URL` для миграций `user-db`
   - `BATTERY_DATABASE_URL` для миграций `battery-db`
2. Если она не задана, используется `DATABASE_URL`.
3. Если переменные окружения отсутствуют, используется значение `sqlalchemy.url` из соответствующего `alembic.ini`.

### Как это работает в Docker

В Docker Compose используется тот же порядок, но с дополнительным этапом подстановки:

1. В [Infrastructure/.env](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/.env) хранятся значения:
   - `DOCKER_USER_DATABASE_URL`
   - `D[README.md](../README.md)OCKER_BATTERY_DATABASE_URL`
2. В [Infrastructure/docker-compose.yml](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/docker-compose.yml) они передаются в контейнеры миграций как:
   - `USER_DATABASE_URL`
   - `BATTERY_DATABASE_URL`
3. Уже внутри контейнера Alembic читает обычные `USER_DATABASE_URL` и `BATTERY_DATABASE_URL`.
[README.md](../README.md)

### Установить зависимости для миграций

```powershell
python -m pip install -r requirements.txt
```

### Применить обе миграции локально

```powershell
.\scripts\run_migrations.ps1
```

### Применить миграции вручную

```powershell
python -m alembic -c migrations/user-db/alembic.ini upgrade head
python -m alembic -c migrations/battery-db/alembic.ini upgrade head
```

### Создать новую миграцию

```powershell
python -m alembic -c migrations/user-db/alembic.ini revision --autogenerate -m "message"
python -m alembic -c migrations/battery-db/alembic.ini revision --autogenerate -m "message"
```

### Назначить пользователю роль admin в Docker
Открыть `psql` внутри контейнера `user-db`:

```powershell
docker exec -it user-db psql -U admin -d userdb
```

Посмотреть пользователей:

```sql
SELECT user_id, email, role
FROM users;
```

Назначить роль `admin` пользователю по `user_id`:

```sql
UPDATE users
SET role = 'admin'
WHERE user_id = 'PUT-USER-ID-HERE';
```

После изменения роли пользователю нужно войти в систему заново, чтобы новый `role` попал в JWT-токен.

## gRPC proto и генерация stubs

Источники истины для gRPC:

- [Infrastructure/protos/user_service.proto](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/protos/user_service.proto)
- [Infrastructure/protos/battery_data_service.proto](C:/Users/mitra/My/НГТУ/4 курс/ВКР/BatteryMonitoring/BatteryMonitoring-BackEnd/Infrastructure/protos/battery_data_service.proto)

После изменения любого `.proto` нужно пересобрать Python stubs:

```powershell
.\scripts\generate_grpc.ps1
```

Скрипт генерирует файлы в:

- `UserService`
- `ProcessingService`
