"""
MySQL database connection module.
Provides a context-managed connection with dict cursors.
"""
import os
import pymysql
from pymysql.cursors import DictCursor
from contextlib import contextmanager
from dotenv import load_dotenv

load_dotenv()


def _config():
    return {
        "host": os.getenv("MYSQL_HOST"),
        "port": int(os.getenv("MYSQL_PORT")),
        "user": os.getenv("MYSQL_USER"),
        "password": os.getenv("MYSQL_PASSWORD"),
        "database": os.getenv("MYSQL_NAME"),
        "charset": "utf8mb4",
        "cursorclass": DictCursor,
        "autocommit": False,
    }


def get_connection():
    """Return a new MySQL connection."""
    config = _config()
    # Mask password for safety when printing
    safe_config = config.copy()
    safe_config['password'] = '***'
    print(f"--- DB CONNECTION ATTEMPT ---")
    print(f"Config: {safe_config}")
    try:
        conn = pymysql.connect(**config)
        print("--- DB CONNECTION SUCCESS ---")
        return conn
    except Exception as e:
        print(f"--- DB CONNECTION FAILED: {e} ---")
        raise


@contextmanager
def db_cursor(commit: bool = False):
    """Yield (conn, cursor); commits on exit when commit=True, rolls back on error."""
    conn = get_connection()
    try:
        cur = conn.cursor()
        yield conn, cur
        if commit:
            conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def fetch_all(sql: str, params=None):
    with db_cursor() as (_, cur):
        cur.execute(sql, params or ())
        return cur.fetchall()


def fetch_one(sql: str, params=None):
    with db_cursor() as (_, cur):
        cur.execute(sql, params or ())
        return cur.fetchone()


def execute(sql: str, params=None):
    with db_cursor(commit=True) as (_, cur):
        cur.execute(sql, params or ())
        return cur.lastrowid


def execute_many(sql: str, seq_params):
    with db_cursor(commit=True) as (_, cur):
        cur.executemany(sql, seq_params)
        return cur.rowcount
