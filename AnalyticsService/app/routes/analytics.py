from app.db.connection import get_db_connection, get_db_cursor
from fastapi import APIRouter, Header
from app.models import CycleInfo, AnalyticsResponse, DeviceInfo
from app.utils.user_info import get_user_info

router = APIRouter()

@router.get("/analytics")
async def get_full_analytics(x_user_id: str = Header(..., alias="X-User-Id")):
    """Получить полную аналитику: пользователь + устройства + последние циклы"""

    user_info = await get_user_info(x_user_id)

    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            # Устройства
            cur.execute(
                """
                SELECT 
                    d.device_id,
                    d.device_name,
                    d.created_at,
                    d.last_seen,
                    COUNT(bc.cycle_id) as total_cycles,
                    (
                        SELECT bc2.health_score 
                        FROM battery_cycles bc2 
                        WHERE bc2.device_id = d.device_id 
                        ORDER BY bc2.completed_at DESC 
                        LIMIT 1
                    ) as last_health_score
                FROM devices d
                LEFT JOIN battery_cycles bc ON d.device_id = bc.device_id
                WHERE d.user_id = %s
                GROUP BY d.device_id
                ORDER BY d.last_seen DESC
                """,
                (x_user_id,)
            )
            devices = cur.fetchall()

            # Последние 20 циклов
            cur.execute(
                """
                SELECT * FROM battery_cycles 
                WHERE user_id = %s
                ORDER BY completed_at DESC
                LIMIT 20
                """,
                (x_user_id,)
            )
            cycles = cur.fetchall()

            # Общее количество циклов
            cur.execute(
                "SELECT COUNT(*) as total FROM battery_cycles WHERE user_id = %s",
                (x_user_id,)
            )
            total_cycles = cur.fetchone()['total']

            return AnalyticsResponse(
                user=user_info,
                devices=[
                    DeviceInfo(
                        device_id=str(d['device_id']),
                        device_name=d['device_name'],
                        created_at=d['created_at'],
                        last_seen=d['last_seen'],
                        total_cycles=d['total_cycles'],
                        last_health_score=d['last_health_score']
                    ) for d in devices
                ],
                recent_cycles=[
                    CycleInfo(
                        cycle_id=str(c['cycle_id']),
                        device_id=str(c['device_id']),
                        started_at=c['started_at'],
                        completed_at=c['completed_at'],
                        duration_minutes=c['duration_minutes'],
                        health_score=c['health_score'],
                        capacity_degradation=c['capacity_degradation'],
                        cycle_count=c['cycle_count'],
                        charge_cycles_equivalent=c.get('charge_cycles_equivalent'),
                        min_level=c.get('min_level'),
                        max_level=c.get('max_level'),
                        avg_discharge_rate=c.get('avg_discharge_rate'),
                        avg_charge_rate=c.get('avg_charge_rate')
                    ) for c in cycles
                ],
                total_cycles=total_cycles
            )