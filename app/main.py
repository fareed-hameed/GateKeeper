from flask import Flask

from .config import load_config
from .db import init_db, set_tz_offset as db_set_tz
from .auth import set_tz_offset as auth_set_tz
from .routes import bp


def create_app(config_path: str | None = None) -> Flask:
    app = Flask(__name__)
    cfg = load_config(config_path)
    app.config["GK"] = cfg

    # Set timezone offset for all modules
    tz_offset = cfg.get("timezone_offset_hours", 3)
    db_set_tz(tz_offset)
    auth_set_tz(tz_offset)

    init_db()
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    application = create_app()
    cfg = application.config["GK"]
    application.run(host="0.0.0.0", port=cfg["port"], debug=cfg["debug"])
