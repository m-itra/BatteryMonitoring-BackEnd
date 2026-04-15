import os

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url


def make_sync_database_url(database_url: str) -> str:
    if database_url.startswith("postgresql+asyncpg://"):
        return database_url.replace("postgresql+asyncpg://", "postgresql+pg8000://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+pg8000://", 1)
    return database_url


def quote_identifier(value: str) -> str:
    return '"' + value.replace('"', '""') + '"'


def ensure_database(database_url: str) -> None:
    target_url = make_url(make_sync_database_url(database_url))
    database_name = target_url.database
    if not database_name:
        raise ValueError(f"Database name is missing in URL: {database_url}")

    maintenance_url = target_url.set(database="postgres")
    engine = create_engine(maintenance_url, isolation_level="AUTOCOMMIT")

    with engine.connect() as connection:
        exists = connection.execute(
            text("SELECT 1 FROM pg_database WHERE datname = :database_name"),
            {"database_name": database_name},
        ).scalar()

        if exists:
            print(f"Database '{database_name}' already exists")
            return

        connection.execute(text(f"CREATE DATABASE {quote_identifier(database_name)}"))
        print(f"Database '{database_name}' created")


def main() -> None:
    for env_name in ("USER_DATABASE_URL", "BATTERY_DATABASE_URL"):
        database_url = os.getenv(env_name)
        if not database_url:
            raise RuntimeError(f"{env_name} is not set")

        ensure_database(database_url)


if __name__ == "__main__":
    main()
