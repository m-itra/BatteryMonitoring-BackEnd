from fastapi import HTTPException

import httpx

_proxy_client: httpx.AsyncClient | None = None


def get_proxy_client() -> httpx.AsyncClient:
    global _proxy_client
    if _proxy_client is None or _proxy_client.is_closed:
        _proxy_client = httpx.AsyncClient(timeout=30.0)
    return _proxy_client


async def close_proxy_client() -> None:
    global _proxy_client
    if _proxy_client is not None:
        await _proxy_client.aclose()
        _proxy_client = None


async def proxy_request(url: str, method: str, headers: dict = None, body: bytes = None, params: dict = None):
    """ Проксирование запроса к микросервису """
    client = get_proxy_client()
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
