import sqlite3
import os
from datetime import datetime, timedelta


DB_PATH = os.environ.get("GATEKEEPER_DB", "gatekeeper.db")


def get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def init_db() -> None:
    conn = get_db()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS admin_devices (
            id INTEGER PRIMARY KEY,
            fingerprint TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            enrolled_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS access_log (
            id INTEGER PRIMARY KEY,
            fingerprint TEXT NOT NULL,
            attempted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            code_valid BOOLEAN NOT NULL,
            action_triggered BOOLEAN DEFAULT 0,
            blocked_reason TEXT
        );

        CREATE INDEX IF NOT EXISTS idx_access_log_fp_date
            ON access_log(fingerprint, attempted_at);
    """)
    conn.close()


# --- Admin Devices ---

def is_admin_device(fingerprint: str) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM admin_devices WHERE fingerprint = ?", (fingerprint,)
    ).fetchone()
    conn.close()
    return row is not None


def enroll_admin_device(fingerprint: str, name: str) -> None:
    conn = get_db()
    conn.execute(
        "INSERT OR IGNORE INTO admin_devices (fingerprint, name) VALUES (?, ?)",
        (fingerprint, name),
    )
    conn.commit()
    conn.close()


def remove_admin_device(fingerprint: str) -> None:
    conn = get_db()
    conn.execute("DELETE FROM admin_devices WHERE fingerprint = ?", (fingerprint,))
    conn.commit()
    conn.close()


def list_admin_devices() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT fingerprint, name, enrolled_at FROM admin_devices ORDER BY enrolled_at"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def admin_device_count() -> int:
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) FROM admin_devices").fetchone()
    conn.close()
    return row[0]


# --- Access Log & Rate Limiting ---

def log_access(
    fingerprint: str,
    code_valid: bool,
    action_triggered: bool = False,
    blocked_reason: str | None = None,
) -> None:
    conn = get_db()
    conn.execute(
        """INSERT INTO access_log
           (fingerprint, code_valid, action_triggered, blocked_reason)
           VALUES (?, ?, ?, ?)""",
        (fingerprint, code_valid, action_triggered, blocked_reason),
    )
    conn.commit()
    conn.close()


def get_device_stats(
    fingerprint: str, reset_hour: int = 0
) -> dict:
    """Return today's stats for a device since the last reset hour."""
    now = datetime.utcnow()
    reset_today = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    if now < reset_today:
        reset_today -= timedelta(days=1)

    conn = get_db()

    # Count successful triggers today
    row = conn.execute(
        """SELECT COUNT(*) FROM access_log
           WHERE fingerprint = ?
             AND action_triggered = 1
             AND attempted_at >= ?""",
        (fingerprint, reset_today.isoformat()),
    ).fetchone()
    successful_count = row[0]

    # First successful trigger timestamp today
    row = conn.execute(
        """SELECT MIN(attempted_at) FROM access_log
           WHERE fingerprint = ?
             AND action_triggered = 1
             AND attempted_at >= ?""",
        (fingerprint, reset_today.isoformat()),
    ).fetchone()
    first_success = row[0] if row else None

    conn.close()
    return {
        "successful_count": successful_count,
        "first_success_at": first_success,
    }


def get_recent_logs(hours: int = 24, limit: int = 100) -> list[dict]:
    since = (datetime.utcnow() - timedelta(hours=hours)).isoformat()
    conn = get_db()
    rows = conn.execute(
        """SELECT fingerprint, attempted_at, code_valid,
                  action_triggered, blocked_reason
           FROM access_log
           WHERE attempted_at >= ?
           ORDER BY attempted_at DESC
           LIMIT ?""",
        (since, limit),
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]
