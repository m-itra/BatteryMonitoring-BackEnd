from app.config import USER_DATABASE_URL
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager

import psycopg2

@contextmanager
def get_db_connection():
    conn = psycopg2.connect(USER_DATABASE_URL)
    try:
        yield conn
    finally:
        conn.close()


def get_db_cursor(conn):
    return conn.cursor(cursor_factory=RealDictCursor)