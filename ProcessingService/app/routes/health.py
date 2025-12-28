from app.db.connection import get_db_connection
from app.db.connection import get_db_cursor
from fastapi import HTTPException, APIRouter

router = APIRouter()


@router.get("/")
def root():
    return {
        "service": "ProcessingService",
        "version": "1.0.0",
        "status": "running",
        "mode": "stub"  # Показывает что это заглушка
    }


@router.get("/health")
def health_check():
    """Health check endpoint"""
    try:
        with get_db_connection() as conn:
            with get_db_cursor(conn) as cur:
                cur.execute("SELECT 1")
                cur.fetchone()
        return {"status": "healthy", "database": "connected"}
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"Database connection failed: {str(e)}")
