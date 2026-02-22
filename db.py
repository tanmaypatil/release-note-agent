import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'defects.db')


def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db():
    conn = get_conn()
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS defects (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                title             TEXT    NOT NULL,
                date              TEXT    NOT NULL,
                developer_comment TEXT    DEFAULT '',
                label             TEXT    NOT NULL,
                status            TEXT    NOT NULL CHECK(status IN ('OPEN','RESOLVED'))
            );
            CREATE TABLE IF NOT EXISTS release_info (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                label      TEXT    NOT NULL UNIQUE,
                build_no   TEXT    NOT NULL,
                created_at TEXT    NOT NULL
            );
        """)
        conn.commit()
    finally:
        conn.close()


def get_all_defects():
    conn = get_conn()
    try:
        rows = conn.execute("SELECT * FROM defects ORDER BY id").fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_resolved_defects(label):
    conn = get_conn()
    try:
        rows = conn.execute(
            "SELECT * FROM defects WHERE label = ? AND status = 'RESOLVED' ORDER BY id",
            (label,)
        ).fetchall()
        return [dict(row) for row in rows]
    finally:
        conn.close()


def get_release_info(label):
    conn = get_conn()
    try:
        row = conn.execute(
            "SELECT * FROM release_info WHERE label = ?", (label,)
        ).fetchone()
        return dict(row) if row else None
    finally:
        conn.close()


def create_defect(title, date, developer_comment, label, status):
    conn = get_conn()
    try:
        cursor = conn.execute(
            "INSERT INTO defects (title, date, developer_comment, label, status) "
            "VALUES (?, ?, ?, ?, ?)",
            (title, date, developer_comment or '', label, status)
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def update_defect_status(defect_id, status):
    conn = get_conn()
    try:
        conn.execute(
            "UPDATE defects SET status = ? WHERE id = ?",
            (status, defect_id)
        )
        conn.commit()
    finally:
        conn.close()
