import os
import yaml


_DEFAULT = {
    "action_url": "",
    "action_timeout_seconds": 10,
    "action_method": "GET",
    "action_label": "Trigger",
    "code_secret": "change-me",
    "code_length": 6,
    "max_opens_per_device": 3,
    "access_window_minutes": 15,
    "daily_reset_hour": 3,
    "timezone_offset_hours": 3,
    "trusted_max_opens": 50,
    "trusted_cooldown_seconds": 30,
    "master_pin": "change-me",
    "port": 5000,
    "debug": False,
}


def load_config(path: str | None = None) -> dict:
    path = path or os.environ.get("GATEKEEPER_CONFIG", "config.yaml")
    cfg = dict(_DEFAULT)
    if os.path.exists(path):
        with open(path, "r") as f:
            cfg.update(yaml.safe_load(f) or {})
    return cfg
