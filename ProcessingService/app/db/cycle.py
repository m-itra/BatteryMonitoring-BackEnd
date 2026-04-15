from datetime import datetime, timedelta

import random

from app.db.connection import get_db_cursor


def create_fake_cycle(conn, device_id: str, user_id: str):
    with get_db_cursor(conn) as cur:
        cur.execute(
            "SELECT COUNT(*) as count FROM battery_cycles WHERE device_id = %s",
            (device_id,)
        )
        result = cur.fetchone()
        cycle_count = result["count"] + 1

        health_score = random.uniform(75.0, 98.0)
        capacity_degradation = random.uniform(0.5, 15.0)
        duration = random.randint(180, 480)

        started_at = datetime.now() - timedelta(minutes=duration)
        completed_at = datetime.now()

        cur.execute(
            """
            INSERT INTO battery_cycles (
                device_id,
                user_id,
                started_at,
                completed_at,
                duration_minutes,
                health_score,
                capacity_degradation,
                cycle_count,
                charge_cycles_equivalent,
                min_level,
                max_level,
                avg_discharge_rate,
                avg_charge_rate
            ) VALUES (
                %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
            )
            RETURNING cycle_id
            """,
            (
                device_id,
                user_id,
                started_at,
                completed_at,
                duration,
                round(health_score, 2),
                round(capacity_degradation, 2),
                cycle_count,
                round(random.uniform(0.8, 1.2), 2),
                random.randint(5, 20),
                random.randint(95, 100),
                round(random.uniform(10.0, 25.0), 2),
                round(random.uniform(15.0, 40.0), 2),
            )
        )
