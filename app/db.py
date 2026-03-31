import sqlite3
import os
import secrets
from datetime import datetime, timedelta, timezone


DB_PATH = os.environ.get("GATEKEEPER_DB", "gatekeeper.db")

# Configurable timezone offset — set via set_tz_offset() at app startup
_TZ_OFFSET_HOURS = 3  # default GMT+3


def set_tz_offset(hours: int) -> None:
    global _TZ_OFFSET_HOURS
    _TZ_OFFSET_HOURS = hours


def now_local() -> datetime:
    """Current time in the configured timezone."""
    tz = timezone(timedelta(hours=_TZ_OFFSET_HOURS))
    return datetime.now(tz).replace(tzinfo=None)


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
            role TEXT NOT NULL DEFAULT 'admin',
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

        CREATE TABLE IF NOT EXISTS invite_tokens (
            id INTEGER PRIMARY KEY,
            token TEXT UNIQUE NOT NULL,
            label TEXT NOT NULL,
            created_by TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            expires_at TIMESTAMP,
            max_uses INTEGER DEFAULT 1,
            used_count INTEGER DEFAULT 0,
            active BOOLEAN DEFAULT 1
        );

        CREATE INDEX IF NOT EXISTS idx_access_log_fp_date
            ON access_log(fingerprint, attempted_at);
    """)
    # Migrate: add role column if missing (existing installs)
    try:
        conn.execute("SELECT role FROM admin_devices LIMIT 1")
    except sqlite3.OperationalError:
        conn.execute("ALTER TABLE admin_devices ADD COLUMN role TEXT NOT NULL DEFAULT 'admin'")
        conn.commit()
    conn.close()


# --- Admin Devices ---

def is_admin_device(fingerprint: str) -> bool:
    conn = get_db()
    row = conn.execute(
        "SELECT 1 FROM admin_devices WHERE fingerprint = ?", (fingerprint,)
    ).fetchone()
    conn.close()
    return row is not None


def get_device_role(fingerprint: str) -> str | None:
    conn = get_db()
    row = conn.execute(
        "SELECT role FROM admin_devices WHERE fingerprint = ?", (fingerprint,)
    ).fetchone()
    conn.close()
    return row["role"] if row else None


def enroll_admin_device(fingerprint: str, name: str, role: str = "super_admin") -> None:
    conn = get_db()
    conn.execute(
        """INSERT INTO admin_devices (fingerprint, name, role)
           VALUES (?, ?, ?)
           ON CONFLICT(fingerprint) DO UPDATE SET name=excluded.name, role=excluded.role""",
        (fingerprint, name, role),
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
        "SELECT fingerprint, name, role, enrolled_at FROM admin_devices ORDER BY enrolled_at"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def admin_device_count() -> int:
    conn = get_db()
    row = conn.execute("SELECT COUNT(*) FROM admin_devices").fetchone()
    conn.close()
    return row[0]


# --- Invite Tokens ---

def create_invite_token(
    label: str, created_by: str, max_uses: int = 1, expires_hours: int = 72
) -> str:
    token = secrets.token_urlsafe(16)
    expires_at = (now_local() + timedelta(hours=expires_hours)).isoformat()
    conn = get_db()
    conn.execute(
        """INSERT INTO invite_tokens (token, label, created_by, expires_at, max_uses)
           VALUES (?, ?, ?, ?, ?)""",
        (token, label, created_by, expires_at, max_uses),
    )
    conn.commit()
    conn.close()
    return token


def claim_invite_token(token: str) -> bool:
    """Atomically validate and claim an invite token. Returns True if claimed."""
    conn = get_db()
    try:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute(
            "SELECT * FROM invite_tokens WHERE token = ? AND active = 1", (token,)
        ).fetchone()
        if not row:
            conn.rollback()
            return False
        row = dict(row)
        now = now_local()
        if row["expires_at"] and now > datetime.fromisoformat(row["expires_at"]):
            conn.rollback()
            return False
        if row["used_count"] >= row["max_uses"]:
            conn.rollback()
            return False
        conn.execute(
            "UPDATE invite_tokens SET used_count = used_count + 1 WHERE token = ?",
            (token,),
        )
        conn.commit()
        return True
    except Exception:
        conn.rollback()
        return False
    finally:
        conn.close()


def validate_invite_token(token: str) -> dict | None:
    """Read-only check — use claim_invite_token for actual redemption."""
    conn = get_db()
    row = conn.execute(
        "SELECT * FROM invite_tokens WHERE token = ? AND active = 1", (token,)
    ).fetchone()
    if not row:
        conn.close()
        return None
    row = dict(row)
    now = now_local()
    if row["expires_at"] and now > datetime.fromisoformat(row["expires_at"]):
        conn.close()
        return None
    if row["used_count"] >= row["max_uses"]:
        conn.close()
        return None
    conn.close()
    return row


def list_invite_tokens() -> list[dict]:
    conn = get_db()
    rows = conn.execute(
        "SELECT token, label, created_at, expires_at, max_uses, used_count, active "
        "FROM invite_tokens ORDER BY created_at DESC"
    ).fetchall()
    conn.close()
    return [dict(r) for r in rows]


def revoke_invite_token(token: str) -> None:
    conn = get_db()
    conn.execute("UPDATE invite_tokens SET active = 0 WHERE token = ?", (token,))
    conn.commit()
    conn.close()


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
           (fingerprint, attempted_at, code_valid, action_triggered, blocked_reason)
           VALUES (?, ?, ?, ?, ?)""",
        (fingerprint, now_local().isoformat(), code_valid, action_triggered, blocked_reason),
    )
    conn.commit()
    conn.close()


def get_device_stats(
    fingerprint: str, reset_hour: int = 0
) -> dict:
    """Return today's stats for a device since the last reset hour (local time)."""
    now = now_local()
    reset_today = now.replace(hour=reset_hour, minute=0, second=0, microsecond=0)
    if now < reset_today:
        reset_today -= timedelta(days=1)

    conn = get_db()

    row = conn.execute(
        """SELECT COUNT(*) FROM access_log
           WHERE fingerprint = ?
             AND action_triggered = 1
             AND attempted_at >= ?""",
        (fingerprint, reset_today.isoformat()),
    ).fetchone()
    successful_count = row[0]

    row = conn.execute(
        """SELECT MIN(attempted_at) FROM access_log
           WHERE fingerprint = ?
             AND action_triggered = 1
             AND attempted_at >= ?""",
        (fingerprint, reset_today.isoformat()),
    ).fetchone()
    first_success = row[0]

    conn.close()
    return {
        "successful_count": successful_count,
        "first_success_at": first_success,
    }


def get_recent_logs(hours: int = 24, limit: int = 100) -> list[dict]:
    since = (now_local() - timedelta(hours=hours)).isoformat()
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


def purge_old_logs(retention_days: int = 30) -> int:
    cutoff = (now_local() - timedelta(days=retention_days)).isoformat()
    conn = get_db()
    cursor = conn.execute(
        "DELETE FROM access_log WHERE attempted_at < ?", (cutoff,)
    )
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return count
