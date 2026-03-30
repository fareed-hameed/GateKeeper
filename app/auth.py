import hashlib
import hmac
from datetime import date, datetime, timedelta, timezone

# Configurable timezone offset — mirrors db module
_TZ_OFFSET_HOURS = 3


def set_tz_offset(hours: int) -> None:
    global _TZ_OFFSET_HOURS
    _TZ_OFFSET_HOURS = hours


def _today_local() -> date:
    tz = timezone(timedelta(hours=_TZ_OFFSET_HOURS))
    return datetime.now(tz).date()


def get_daily_code(secret: str, length: int = 6, for_date: date | None = None) -> str:
    """Generate a deterministic daily code from a secret and a date."""
    target = (for_date or _today_local()).isoformat()
    h = hmac.new(secret.encode(), target.encode(), hashlib.sha256).hexdigest()
    return str(int(h[:8], 16) % (10**length)).zfill(length)


def get_upcoming_codes(secret: str, length: int = 6, days: int = 7) -> list[dict]:
    """Generate codes for today and the next N-1 days."""
    today = _today_local()
    return [
        {
            "date": (today + timedelta(days=i)).isoformat(),
            "day": (today + timedelta(days=i)).strftime("%a"),
            "code": get_daily_code(secret, length, today + timedelta(days=i)),
        }
        for i in range(days)
    ]


def check_rate_limit(
    device_stats: dict,
    max_opens: int,
    window_minutes: int,
) -> tuple[bool, str | None, dict]:
    """Check whether a device is allowed to trigger the action.

    Returns (allowed, blocked_reason, info_dict).
    """
    count = device_stats["successful_count"]
    first_success = device_stats["first_success_at"]

    remaining = max_opens - count
    window_remaining = None

    if first_success:
        if isinstance(first_success, str):
            first_success = datetime.fromisoformat(first_success)
        window_end = first_success + timedelta(minutes=window_minutes)
        tz = timezone(timedelta(hours=_TZ_OFFSET_HOURS))
        now = datetime.now(tz).replace(tzinfo=None)
        window_remaining = max(0, int((window_end - now).total_seconds()))

        if now > window_end:
            return False, "window_expired", {
                "remaining_attempts": 0,
                "window_seconds_left": 0,
            }

    if count >= max_opens:
        return False, "limit_exceeded", {
            "remaining_attempts": 0,
            "window_seconds_left": window_remaining or 0,
        }

    return True, None, {
        "remaining_attempts": remaining,
        "window_seconds_left": window_remaining,
    }
