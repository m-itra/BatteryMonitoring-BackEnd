"""Add roles to users.

Revision ID: 0002_add_user_roles
Revises: 0001_user_schema
Create Date: 2026-04-28
"""

from typing import Sequence, Union

from alembic import op

revision: str = "0002_add_user_roles"
down_revision: Union[str, None] = "0001_user_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE users ADD COLUMN IF NOT EXISTS role VARCHAR(20) NOT NULL DEFAULT 'user'")
    op.execute("UPDATE users SET role = 'user' WHERE role IS NULL OR role = ''")


def downgrade() -> None:
    op.execute("ALTER TABLE users DROP COLUMN IF EXISTS role")
