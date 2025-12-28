from app.config import *

import httpx


async def get_user_info(user_id: str) -> dict:
    """Получение информации о пользователе по user_id без токена"""
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{USER_SERVICE_URL}/internal/user/{user_id}")
            response.raise_for_status()
            return response.json()
    except Exception as e:
        print(f"Error fetching user info for user_id {user_id}: {e}")
        return {"name": "Unknown User", "email": ""}