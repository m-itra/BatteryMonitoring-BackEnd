from fastapi import HTTPException

import httpx


async def proxy_request(url: str, method: str, headers: dict = None, body: bytes = None, params: dict = None):
    """ Проксирование запроса к микросервису """
    async with httpx.AsyncClient() as client:
        try:
            response = await client.request(
                method=method,
                url=url,
                headers=headers,
                content=body,
                params=params,
                timeout=30.0
            )
            return response
        except httpx.RequestError as e:
            raise HTTPException(status_code=503, detail=f"Service unavailable: {str(e)}")
