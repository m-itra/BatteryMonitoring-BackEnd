from app.db.connection import get_db_connection, get_db_cursor
from fastapi import APIRouter, Header
from typing import Optional
from app.models import CycleInfo


router = APIRouter()

@router.get("/cycles")
async def get_cycles(
        x_user_id: str = Header(...),
        device_id: Optional[str] = None,
        limit: int = 50
):
    """Получить циклы пользователя (все или для конкретного устройства)"""

    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            if device_id:
                query = """
                    SELECT * FROM battery_cycles 
                    WHERE user_id = %s AND device_id = %s
                    ORDER BY completed_at DESC
                    LIMIT %s
                """
                cur.execute(query, (x_user_id, device_id, limit))
            else:
                query = """
                    SELECT * FROM battery_cycles 
                    WHERE user_id = %s
                    ORDER BY completed_at DESC
                    LIMIT %s
                """
                cur.execute(query, (x_user_id, limit))

            cycles = cur.fetchall()

            result = []
            for cycle in cycles:
                result.append(CycleInfo(
                    cycle_id=str(cycle['cycle_id']),
                    device_id=str(cycle['device_id']),
                    started_at=cycle['started_at'],
                    completed_at=cycle['completed_at'],
                    duration_minutes=cycle['duration_minutes'],
                    health_score=cycle['health_score'],
                    capacity_degradation=cycle['capacity_degradation'],
                    cycle_count=cycle['cycle_count'],
                    charge_cycles_equivalent=cycle.get('charge_cycles_equivalent'),
                    min_level=cycle.get('min_level'),
                    max_level=cycle.get('max_level'),
                    avg_discharge_rate=cycle.get('avg_discharge_rate'),
                    avg_charge_rate=cycle.get('avg_charge_rate')
                ))

            return {"cycles": result}