import hashlib
import hmac
from datetime import date, datetime, timedelta, timezone

# Configurable — set via set_tz_offset() and set_reset_hour() at app startup
_TZ_OFFSET_HOURS = 3
_RESET_HOUR = 3


def set_tz_offset(hours: int) -> None:
    global _TZ_OFFSET_HOURS
    _TZ_OFFSET_HOURS = hours


def set_reset_hour(hour: int) -> None:
    global _RESET_HOUR
    _RESET_HOUR = hour


def _now_local() -> datetime:
    tz = timezone(timedelta(hours=_TZ_OFFSET_HOURS))
    return datetime.now(tz).replace(tzinfo=None)


def _effective_date() -> date:
    """The 'code day' — shifts at reset hour, not midnight.
    Between midnight and reset hour, we're still on yesterday's code."""
    now = _now_local()
    if now.hour < _RESET_HOUR:
        return (now - timedelta(days=1)).date()
    return now.date()


def get_daily_code(secret: str, length: int = 6, for_date: date | None = None) -> str:
    """Generate a deterministic daily code from a secret and a date."""
    target = (for_date or _effective_date()).isoformat()
    h = hmac.new(secret.encode(), target.encode(), hashlib.sha256).hexdigest()
    return str(int(h[:8], 16) % (10**length)).zfill(length)


def get_upcoming_codes(
    secret: str, length: int = 6, days: int = 6, reset_hour: int | None = None
) -> list[dict]:
    """Generate codes for the next N days (excluding today's active code)."""
    rh = reset_hour if reset_hour is not None else _RESET_HOUR
    today = _effective_date()
    result = []
    for i in range(1, days + 1):
        d = today + timedelta(days=i)
        result.append({
            "date": d.isoformat(),
            "day": d.strftime("%a"),
            "time": f"{str(rh).zfill(2)}:00",
            "code": get_daily_code(secret, length, d),
        })
    return result


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
        now = _now_local()
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
