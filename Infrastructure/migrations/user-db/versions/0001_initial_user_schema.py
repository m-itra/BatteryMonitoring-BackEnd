"""Initial user database schema.

Revision ID: 0001_user_schema
Revises:
Create Date: 2026-04-15
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0001_user_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

    op.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            user_id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
            email VARCHAR(255) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            password_hash VARCHAR(255) NOT NULL,
            created_at TIMESTAMP DEFAULT NOW(),
            updated_at TIMESTAMP DEFAULT NOW()
        )
        """
    )
    op.execute("CREATE INDEX IF NOT EXISTS idx_users_email ON users(email)")

    op.execute(
        """
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql'
        """
    )
    op.execute(
        """
        DO $$
        BEGIN
            IF NOT EXISTS (
                SELECT 1
                FROM pg_trigger
                WHERE tgname = 'update_users_updated_at'
                  AND tgrelid = 'users'::regclass
            ) THEN
                CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
                    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
            END IF;
        END;
        $$
        """
    )


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS update_users_updated_at ON users")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column()")
    op.execute("DROP INDEX IF EXISTS idx_users_email")
    op.execute("DROP TABLE IF EXISTS users")
