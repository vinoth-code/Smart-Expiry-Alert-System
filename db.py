import sqlite3
import os
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(__file__), "data", "expiry.db")

def get_conn():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                expiry_date TEXT NOT NULL,
                quantity INTEGER DEFAULT 1,
                image_path TEXT,
                risk_score REAL DEFAULT 0.0,
                status TEXT DEFAULT 'active', -- active | consumed | expired
                added_at TEXT DEFAULT CURRENT_TIMESTAMP,
                consumed_at TEXT
            )
            """
        )
        conn.commit()

def add_item(name, expiry_date, quantity=1, image_path=None, risk_score=0.0):
    with get_conn() as conn:
        conn.execute(
            """
            INSERT INTO items (name, expiry_date, quantity, image_path, risk_score, status)
            VALUES (?, ?, ?, ?, ?, 'active')
            """,
            (name, expiry_date, quantity, image_path, risk_score),
        )
        conn.commit()

def get_items(status=None):
    with get_conn() as conn:
        if status:
            cur = conn.execute("SELECT * FROM items WHERE status = ? ORDER BY expiry_date ASC", (status,))
        else:
            cur = conn.execute("SELECT * FROM items ORDER BY expiry_date ASC")
        return [dict(r) for r in cur.fetchall()]

def update_status(item_id, status):
    with get_conn() as conn:
        conn.execute("UPDATE items SET status = ? WHERE id = ?", (status, item_id))
        conn.commit()

def mark_consumed(item_id):
    with get_conn() as conn:
        conn.execute(
            "UPDATE items SET status='consumed', consumed_at = ? WHERE id = ?",
            (datetime.utcnow().isoformat(timespec='seconds'), item_id),
        )
        conn.commit()

def delete_item(item_id):
    with get_conn() as conn:
        conn.execute("DELETE FROM items WHERE id = ?", (item_id,))
        conn.commit()
