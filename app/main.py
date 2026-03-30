from flask import Flask

from .config import load_config
from .db import init_db
from .routes import bp


def create_app(config_path: str | None = None) -> Flask:
    app = Flask(__name__)
    app.config["GK"] = load_config(config_path)
    init_db()
    app.register_blueprint(bp)
    return app


if __name__ == "__main__":
    application = create_app()
    cfg = application.config["GK"]
    application.run(host="0.0.0.0", port=cfg["port"], debug=cfg["debug"])
