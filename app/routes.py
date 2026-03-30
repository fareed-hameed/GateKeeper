from flask import Blueprint, request, jsonify, render_template, current_app

from .auth import get_daily_code, check_rate_limit
from .action import trigger_action
from . import db

bp = Blueprint("gatekeeper", __name__)


# ---------- Pages ----------

@bp.route("/")
def index():
    cfg = current_app.config["GK"]
    return render_template("gate.html", action_label=cfg["action_label"])


@bp.route("/admin")
def admin_page():
    return render_template("admin.html")


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

    stats = db.get_device_stats(fingerprint, cfg["daily_reset_hour"])
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

    result = trigger_action(
        cfg["action_url"], cfg["action_method"], cfg["action_timeout_seconds"]
    )

    db.log_access(
        fingerprint,
        code_valid=True,
        action_triggered=result["success"],
    )

    # Re-fetch stats after logging this trigger
    updated_stats = db.get_device_stats(fingerprint, cfg["daily_reset_hour"])
    _, _, updated_info = check_rate_limit(
        updated_stats, cfg["max_opens_per_device"], cfg["access_window_minutes"]
    )

    return jsonify({
        "ok": result["success"],
        "action_response": result["response"],
        "error": result["error"],
        **updated_info,
    })


# ---------- API: Admin ----------

@bp.route("/api/admin/check", methods=["POST"])
def api_admin_check():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    if not fingerprint:
        return jsonify({"enrolled": False}), 400
    return jsonify({"enrolled": db.is_admin_device(fingerprint)})


@bp.route("/api/admin/enroll", methods=["POST"])
def api_admin_enroll():
    cfg = current_app.config["GK"]
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    pin = (data.get("pin") or "").strip()
    name = (data.get("name") or "").strip() or "Admin Device"

    if not fingerprint:
        return jsonify({"ok": False, "error": "Device identification required"}), 400
    if pin != cfg["master_pin"]:
        return jsonify({"ok": False, "error": "Invalid PIN"}), 403

    db.enroll_admin_device(fingerprint, name)
    return jsonify({"ok": True})


@bp.route("/api/admin/devices", methods=["POST"])
def api_admin_devices():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    if not db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Not authorized"}), 403
    return jsonify({"ok": True, "devices": db.list_admin_devices()})


@bp.route("/api/admin/devices/remove", methods=["POST"])
def api_admin_remove_device():
    data = request.get_json(silent=True) or {}
    fingerprint = (data.get("fingerprint") or "").strip()
    target = (data.get("target") or "").strip()

    if not db.is_admin_device(fingerprint):
        return jsonify({"ok": False, "error": "Not authorized"}), 403
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
    return jsonify({"ok": True, "code": code})


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


# ---------- Health ----------

@bp.route("/health")
def health():
    return jsonify({"status": "ok"})
