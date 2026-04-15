## Database migrations

The database schema is managed by Alembic.

Install migration dependencies:

```powershell
python -m pip install -r requirements.txt
```

Run both database migrations from the `Infrastructure` directory:

```powershell
.\scripts\run_migrations.ps1
```

The script loads `Infrastructure/.env`, creates `userdb` and `batterydb` if they do not exist. For local PostgreSQL, make sure `USER_DATABASE_URL` and `BATTERY_DATABASE_URL` point to the actual local port and credentials.

Or run one database explicitly:

```powershell
python -m alembic -c migrations/user-db/alembic.ini upgrade head
python -m alembic -c migrations/battery-db/alembic.ini upgrade head
```