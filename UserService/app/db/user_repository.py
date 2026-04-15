from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import User


def parse_user_id(user_id: str) -> UUID | None:
    try:
        return UUID(str(user_id))
    except (TypeError, ValueError):
        return None


async def get_user_by_email(session: AsyncSession, email: str) -> User | None:
    result = await session.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(session: AsyncSession, user_id: str) -> User | None:
    parsed_user_id = parse_user_id(user_id)
    if parsed_user_id is None:
        return None

    result = await session.execute(select(User).where(User.user_id == parsed_user_id))
    return result.scalar_one_or_none()


async def create_user(session: AsyncSession, email: str, name: str, password_hash: str) -> User:
    user = User(email=email, name=name, password_hash=password_hash)
    session.add(user)
    await session.flush()
    return user
