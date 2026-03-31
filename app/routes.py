import threading
from collections import defaultdict
from datetime import datetime

from flask import Blueprint, request, jsonify, render_template, current_app

from .auth import get_daily_code, get_upcoming_codes, check_rate_limit
from .action import trigger_action
from . import db

bp = Blueprint("gatekeeper", __name__)

# Simple in-memory rate limiter for PIN attempts (per IP)
_pin_attempts = defaultdict(list)  # ip -> [timestamp, ...]
PIN_MAX_ATTEMPTS = 5
PIN_WINDOW_SECONDS = 900  # 15 minutes

# Action lock — only one action call can be in-flight at a time
_action_lock = threading.Lock()


def _check_pin_rate(ip: str) -> bool:
    """Returns True if allowed, False if rate limited."""
    now = datetime.utcnow()
    window = [t for t in _pin_attempts[ip] if (now - t).total_seconds() < PIN_WINDOW_SECONDS]
    _pin_attempts[ip] = window
    return len(window) < PIN_MAX_ATTEMPTS


def _record_pin_attempt(ip: str) -> None:
    _pin_attempts[ip].append(datetime.utcnow())


# ---------- Pages ----------

@bp.route("/")
def index():
    cfg = current_app.config["GK"]
    return render_template("gate.html", action_label=cfg["action_label"])


@bp.route("/admin")
def admin_page():
    return render_template("admin.html")


@bp.route("/enroll/<token>")
def enroll_page(token):
    return render_template("enroll.html", token=token)


# ---------- API: Trigger ----------

@bp.route("/api/trigger", methods=["POST"])
def api_trigger():
    cfg = current_app.config["GK"]
    data = request.get_json(silent=True) or {}
    code = (data.get("code") or "").strip()
    fingerprint = (data.get("fingerprint") or "").strip()

    if not fingerprint:
        return jsonify({"ok": False, "error": "Device identification required"}), 400

    expected = get_daily_code(cfg["code_secret"], cfg["code_length"])
    if code != expected:
        db.log_access(fingerprint, code_valid=False, blocked_reason="invalid_code")
        return jsonify({"ok": False, "error": "Invalid code"}), 403

    cooldown = cfg.get("cooldown_seconds", 15)
    stats = db.get_device_stats(fingerprint, cfg["daily_reset_hour"])

    # Cooldown between triggers
    if stats["last_success_at"]:
        last_dt = stats["last_success_at"]
        if isinstance(last_dt, str):
            last_dt = datetime.fromisoformat(last_dt)
        elapsed = (db.now_local() - last_dt).total_seconds()
        wait = cooldown - int(elapsed)
        if wait > 0:
            db.log_access(fingerprint, code_valid=True, blocked_reason="cooldown")
            return jsonify({
                "ok": False,
                "error": f"Please wait {wait} seconds",
                "cooldown_seconds": wait,
            }), 429

    allowed, reason, info = check_rate_limit(
        stats, cfg["max_opens_per_device"], cfg["access_window_minutes"]
    )

    if not allowed:
        db.log_access(fingerprint, code_valid=True, blocked_reason=reason)
        messages = {
            "limit_exceeded": "Daily limit reached",
            "window_expired": "Access window has expired",
        }
        return jsonify({
            "ok": False,
            "error": messages.get(reason, "Access denied"),
            **info,
        }), 429

    # Action lock — drop concurrent requests
    if not _action_lock.acquire(blocking=False):
        return jsonify({"ok": False, "error": "System busy. Try again shortly."}), 503

    try:
        result = trigger_action(
            cfg["action_url"], cfg["action_method"], cfg["action_timeout_seconds"]
        )
    finally:
        _action_lock.release()

    db.log_access(
        fingerprint, code_valid=True, action_triggered=result["success"],
    )

    updated_stats = db.get_device_stats(fingerprint, cfg["daily_reset_hour"])
    _, _, updated_info = check_rate_limit(
        updated_stats, cfg["max_opens_per_device"], cfg["access_window_minutes"]
    )

    return jsonify({
        "ok": result["success"],
        "error": result["error"],
        "cooldown_seconds": cooldown,
        **updated_info,
    })


# ---------- API: Bypass (trusted registered devices) ----------

@bp.route("/api/bypass", methods=["POST"])
def api_bypass():
    cfg = current_app.config["GK"]
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()

    if not fingerprint:
        return jsonify({"ok": False, "error": "Device identification required"}), 400

    if not db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Device not registered"}), 403

    trusted_max = cfg.get("trusted_max_opens", 50)
    cooldown = cfg.get("trusted_cooldown_seconds", 30)

    stats = db.get_device_stats(fingerprint, cfg["daily_reset_hour"])
    count = stats["successful_count"]
    last_success = stats["last_success_at"]

    # Daily limit for trusted devices
    if count >= trusted_max:
        remaining = 0
        db.log_access(fingerprint, code_valid=True, blocked_reason="limit_exceeded")
        return jsonify({
            "ok": False,
            "error": "Daily limit reached",
            "remaining_attempts": remaining,
        }), 429

    # Cooldown between requests
    if last_success:
        if isinstance(last_success, str):
            last_success_dt = datetime.fromisoformat(last_success)
        else:
            last_success_dt = last_success
        from .db import now_local
        elapsed = (now_local() - last_success_dt).total_seconds()
        wait = cooldown - int(elapsed)
        if wait > 0:
            db.log_access(fingerprint, code_valid=True, blocked_reason="cooldown")
            return jsonify({
                "ok": False,
                "error": f"Please wait {wait} seconds",
                "cooldown_seconds": wait,
                "remaining_attempts": trusted_max - count,
            }), 429

    # Action lock — drop concurrent requests (DDoS protection)
    if not _action_lock.acquire(blocking=False):
        return jsonify({
            "ok": False,
            "error": "System busy. Try again shortly.",
        }), 503

    try:
        result = trigger_action(
            cfg["action_url"], cfg["action_method"], cfg["action_timeout_seconds"]
        )
    finally:
        _action_lock.release()

    db.log_access(
        fingerprint, code_valid=True, action_triggered=result["success"],
    )

    return jsonify({
        "ok": result["success"],
        "error": result["error"],
        "remaining_attempts": trusted_max - count - (1 if result["success"] else 0),
        "cooldown_seconds": cooldown,
    })


# ---------- API: Admin ----------

@bp.route("/api/admin/check", methods=["POST"])
def api_admin_check():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    if not fingerprint:
        return jsonify({"ok": False, "enrolled": False}), 400
    role = db.get_device_role(fingerprint)
    return jsonify({"ok": True, "enrolled": role is not None, "role": role})


@bp.route("/api/admin/enroll", methods=["POST"])
def api_admin_enroll():
    cfg = current_app.config["GK"]
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    pin = (data.get("pin") or "").strip()
    name = (data.get("name") or "").strip() or "Admin Device"

    if not fingerprint:
        return jsonify({"ok": False, "error": "Device identification required"}), 400

    ip = request.remote_addr or "unknown"
    if not _check_pin_rate(ip):
        return jsonify({"ok": False, "error": "Too many attempts. Try again later."}), 429

    if pin != cfg["master_pin"]:
        _record_pin_attempt(ip)
        return jsonify({"ok": False, "error": "Invalid PIN"}), 403

    db.enroll_admin_device(fingerprint, name, role="super_admin")
    return jsonify({"ok": True})


@bp.route("/api/admin/peek", methods=["POST"])
def api_admin_peek():
    """View codes with master PIN only — no enrollment required."""
    cfg = current_app.config["GK"]
    data = request.get_json(silent=True) or {}
    pin = (data.get("pin") or "").strip()

    ip = request.remote_addr or "unknown"
    if not _check_pin_rate(ip):
        return jsonify({"ok": False, "error": "Too many attempts. Try again later."}), 429

    if pin != cfg["master_pin"]:
        _record_pin_attempt(ip)
        return jsonify({"ok": False, "error": "Invalid PIN"}), 403

    code = get_daily_code(cfg["code_secret"], cfg["code_length"])
    upcoming = get_upcoming_codes(cfg["code_secret"], cfg["code_length"], days=7)
    return jsonify({"ok": True, "code": code, "upcoming": upcoming})


@bp.route("/api/admin/devices", methods=["POST"])
def api_admin_devices():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    if not db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Not authorized"}), 403
    role = db.get_device_role(fingerprint)
    return jsonify({"ok": True, "devices": db.list_admin_devices(), "caller_role": role})


@bp.route("/api/admin/devices/remove", methods=["POST"])
def api_admin_remove_device():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    target = (data.get("target") or "").strip()

    if db.get_device_role(fingerprint) != "super_admin":
        return jsonify({"ok": False, "error": "Only super admins can remove devices"}), 403
    if fingerprint == target:
        return jsonify({"ok": False, "error": "Cannot remove yourself"}), 400

    db.remove_admin_device(target)
    return jsonify({"ok": True})


@bp.route("/api/admin/code", methods=["POST"])
def api_admin_code():
    cfg = current_app.config["GK"]
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    if not db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Not authorized"}), 403
    code = get_daily_code(cfg["code_secret"], cfg["code_length"])
    upcoming = get_upcoming_codes(cfg["code_secret"], cfg["code_length"], days=7)
    return jsonify({"ok": True, "code": code, "upcoming": upcoming})


@bp.route("/api/admin/logs", methods=["POST"])
def api_admin_logs():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    if not db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Not authorized"}), 403
    return jsonify({"ok": True, "logs": db.get_recent_logs()})


@bp.route("/api/admin/config", methods=["POST"])
def api_admin_config():
    cfg = current_app.config["GK"]
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    if not db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Not authorized"}), 403
    return jsonify({
        "ok": True,
        "config": {
            "max_opens_per_device": cfg["max_opens_per_device"],
            "access_window_minutes": cfg["access_window_minutes"],
            "daily_reset_hour": cfg["daily_reset_hour"],
            "code_length": cfg["code_length"],
            "action_label": cfg["action_label"],
            "action_method": cfg["action_method"],
        },
    })


# ---------- API: Invite Tokens ----------

@bp.route("/api/admin/invites", methods=["POST"])
def api_admin_invites():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    if db.get_device_role(fingerprint) != "super_admin":
        return jsonify({"ok": False, "error": "Only super admins can manage invites"}), 403
    return jsonify({"ok": True, "invites": db.list_invite_tokens()})


@bp.route("/api/admin/invites/create", methods=["POST"])
def api_admin_create_invite():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    label = (data.get("label") or "").strip() or "Invite"
    max_uses = min(max(int(data.get("max_uses", 1)), 1), 50)
    expires_hours = min(max(int(data.get("expires_hours", 72)), 1), 720)

    if db.get_device_role(fingerprint) != "super_admin":
        return jsonify({"ok": False, "error": "Only super admins can create invites"}), 403

    token = db.create_invite_token(label, fingerprint, max_uses, expires_hours)
    return jsonify({"ok": True, "token": token})


@bp.route("/api/admin/invites/revoke", methods=["POST"])
def api_admin_revoke_invite():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    token = (data.get("token") or "").strip()

    if db.get_device_role(fingerprint) != "super_admin":
        return jsonify({"ok": False, "error": "Only super admins can revoke invites"}), 403

    db.revoke_invite_token(token)
    return jsonify({"ok": True})


# ---------- API: Self-Enroll via Invite ----------

@bp.route("/api/enroll/check", methods=["POST"])
def api_enroll_check():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    fingerprint = (data.get("fingerprint") or "").strip()

    if db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Device already enrolled"})

    invite = db.validate_invite_token(token)
    if not invite:
        return jsonify({"ok": False, "error": "Invalid or expired invite link"})

    return jsonify({"ok": True, "label": invite["label"]})


@bp.route("/api/enroll/submit", methods=["POST"])
def api_enroll_submit():
    data = request.get_json(silent=True) or {}
    token = (data.get("token") or "").strip()
    fingerprint = (data.get("fingerprint") or "").strip()
    name = (data.get("name") or "").strip() or "Invited Device"

    if not fingerprint:
        return jsonify({"ok": False, "error": "Device identification required"}), 400

    if db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Device already enrolled"}), 400

    # Atomic claim — prevents TOCTOU race with concurrent requests
    if not db.claim_invite_token(token):
        return jsonify({"ok": False, "error": "Invalid or expired invite link"}), 403

    db.enroll_admin_device(fingerprint, name, role="admin")
    return jsonify({"ok": True})


# ---------- Health ----------

@bp.route("/health")
def health():
    return jsonify({"status": "ok"})
