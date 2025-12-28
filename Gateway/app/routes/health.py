from fastapi import APIRouter
from app.config import *

import httpx

router = APIRouter()


@router.get("/", tags=["Health"])
def root():
    return {
        "service": "API Gateway",
        "version": "1.0.0",
        "status": "running"
    }


@router.get("/health", tags=["Health"])
async def health_check():
    return {"status": "healthy", "service": "gateway"}


@router.get("/health/services", tags=["Health"])
async def services_health():
    """ Проверка всех сервисов """
    results = {}

    services = {
        "user-service": f"{USER_SERVICE_URL}/health",
        "processing-service": f"{PROCESSING_SERVICE_URL}/health",
        "analytics-service": f"{ANALYTICS_SERVICE_URL}/health"
    }

    async with httpx.AsyncClient() as client:
        for name, url in services.items():
            try:
                response = await client.get(url, timeout=5.0)
                results[name] = {
                    "status": "healthy" if response.status_code == 200 else "unhealthy",
                    "code": response.status_code
                }
            except Exception as e:
                results[name] = {
                    "status": "unreachable",
                    "error": str(e)
                }

    all_healthy = all(s["status"] == "healthy" for s in results.values())

    return {
        "gateway": "healthy",
        "services": results,
        "overall": "healthy" if all_healthy else "degraded"
    }
