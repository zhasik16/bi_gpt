import sqlite3
from typing import List, Dict, Any

DB_PATH = "../data/app.db"  # путь относительно backend/

def query_db(sql: str, params: tuple = ()) -> List[Dict[str, Any]]:
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    cols = rows[0].keys() if rows else []
    result = [dict(row) for row in rows]
    cur.close()
    conn.close()
    return result

def execute_db(sql: str, params: tuple = ()):
    conn = sqlite3.connect(DB_PATH, timeout=30)
    cur = conn.cursor()
    cur.execute(sql, params)
    conn.commit()
    cur.close()
    conn.close()
