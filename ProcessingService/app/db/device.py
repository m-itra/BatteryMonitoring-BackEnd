from app.db.connection import get_db_cursor


def create_device(conn, device_id: str, device_name: str, user_id: str):
    with get_db_cursor(conn) as cur:
        cur.execute(
            """
            INSERT INTO devices (device_id, user_id, device_name, last_seen)
            VALUES (%s, %s, %s, NOW())
            """,
            (device_id, user_id, device_name)
        )


def get_device_by_id(conn, device_id: str):
    """
    Проверяет, существует ли устройство с указанным device_id в базе.

    Args:
        conn: соединение с базой данных
        device_id: идентификатор устройства

    Returns:
        dict с данными устройства, если найдено, иначе None
    """
    query = "SELECT * FROM devices WHERE device_id = %s"
    cursor = conn.cursor()
    cursor.execute(query, (device_id,))
    result = cursor.fetchone()
    cursor.close()
    if result:
        return {
            "device_id": result[0],
            "user_id": result[1],
            "device_name": result[2],
        }
    return None
