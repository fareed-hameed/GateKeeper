import hashlib
import hmac
from datetime import date, datetime, timedelta


def get_daily_code(secret: str, length: int = 6) -> str:
    """Generate a deterministic daily code from a secret and today's date."""
    today = date.today().isoformat()
    h = hmac.new(secret.encode(), today.encode(), hashlib.sha256).hexdigest()
    return str(int(h[:8], 16) % (10**length)).zfill(length)


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
        now = datetime.utcnow()
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
