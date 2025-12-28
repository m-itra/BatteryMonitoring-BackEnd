from app.db.connection import get_db_connection, get_db_cursor
from fastapi import APIRouter, Header, HTTPException
from app.models import DeviceInfo, UpdateDeviceRequest


router = APIRouter()

@router.get("/devices")
async def get_devices(x_user_id: str = Header(...)):
    """Получить список устройств пользователя"""

    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            # Получаем устройства
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
                GROUP BY d.device_id, d.device_name, d.created_at, d.last_seen
                ORDER BY d.last_seen DESC
                """,
                (x_user_id,)
            )

            devices = cur.fetchall()

            result = []
            for device in devices:
                result.append(DeviceInfo(
                    device_id=str(device['device_id']),
                    device_name=device['device_name'],
                    created_at=device['created_at'],
                    last_seen=device['last_seen'],
                    total_cycles=device['total_cycles'],
                    last_health_score=device['last_health_score']
                ))

            return {"devices": result}


@router.put("/devices/{device_id}")
def update_device(
        device_id: str,
        data: UpdateDeviceRequest,
        x_user_id: str = Header(...)
):
    """Обновить название устройства"""

    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            # Проверяем владение устройством
            cur.execute(
                "SELECT device_id FROM devices WHERE device_id = %s AND user_id = %s",
                (device_id, x_user_id)
            )

            if not cur.fetchone():
                raise HTTPException(status_code=403, detail="Device not found or access denied")

            # Обновляем название
            cur.execute(
                "UPDATE devices SET device_name = %s WHERE device_id = %s",
                (data.device_name, device_id)
            )
            conn.commit()

            return {"status": "updated", "device_id": device_id, "device_name": data.device_name}


@router.delete("/devices/{device_id}")
def delete_device(device_id: str, x_user_id: str = Header(...)):
    """Удалить устройство и все его данные"""

    with get_db_connection() as conn:
        with get_db_cursor(conn) as cur:
            # Удаляем устройство (циклы удалятся автоматически через CASCADE)
            cur.execute(
                "DELETE FROM devices WHERE device_id = %s AND user_id = %s RETURNING device_id",
                (device_id, x_user_id)
            )

            deleted = cur.fetchone()

            if not deleted:
                raise HTTPException(status_code=403, detail="Device not found or access denied")

            conn.commit()

            return {"status": "deleted", "device_id": device_id}