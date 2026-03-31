import logging

from flask import Flask

from .config import load_config
from .db import init_db, set_tz_offset as db_set_tz, purge_old_logs
from .auth import set_tz_offset as auth_set_tz, set_reset_hour as auth_set_reset
from .routes import bp

logger = logging.getLogger(__name__)


def create_app(config_path: str | None = None) -> Flask:
    app = Flask(__name__)
    cfg = load_config(config_path)

    # Reject unsafe defaults
    if cfg["code_secret"] == "change-me":
        raise RuntimeError("FATAL: code_secret is still 'change-me' — update config.yaml")
    if cfg["master_pin"] == "change-me":
        raise RuntimeError("FATAL: master_pin is still 'change-me' — update config.yaml")

    app.config["GK"] = cfg

    # Set timezone offset for all modules
    tz_offset = cfg.get("timezone_offset_hours", 3)
    db_set_tz(tz_offset)
    auth_set_tz(tz_offset)
    auth_set_reset(cfg.get("daily_reset_hour", 3))

    init_db()

    # Purge old logs on startup
    purged = purge_old_logs(retention_days=30)
    if purged:
        logger.info("Purged %d access log entries older than 30 days", purged)

    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    application = create_app()
    cfg = application.config["GK"]
    application.run(host="0.0.0.0", port=cfg["port"], debug=cfg["debug"])
