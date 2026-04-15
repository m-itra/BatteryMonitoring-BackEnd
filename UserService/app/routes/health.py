from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from app.db.connection import get_db_session

router = APIRouter()


@router.get("/")
def root():
    return {
        "service": "UserService",
        "version": "1.0.0",
        "status": "running",
    }


@router.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        async with get_db_session() as session:
            await session.execute(text("SELECT 1"))
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
