from typing import TypedDict, Any
import os
import json


class ConfigType(TypedDict):
    token: str | None
    server: str


DEFAULT_CONFIG: ConfigType = {
    "token": None,
    "server": "http://cloud-dev.funix.io",
}

CONFIG = {}
LOADED = False
CONFIG_PATH = os.path.expanduser("~/.config/tengoku/config.json")


def read_config_from_file():
    global CONFIG, LOADED
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, "w") as f:
            f.write(json.dumps(DEFAULT_CONFIG))
        CONFIG = DEFAULT_CONFIG
        LOADED = True
    else:
        with open(CONFIG_PATH, "r") as f:
            CONFIG = json.loads(f.read())
        LOADED = True


def read_key_from_config(key: str):
    global LOADED
    if not LOADED:
        read_config_from_file()
    return CONFIG.get(key, None)


def write_key_to_config(key: str, value: Any):
    global CONFIG, LOADED
    if not LOADED:
        read_config_from_file()
    CONFIG[key] = value
    with open(CONFIG_PATH, "w") as f:
        f.write(json.dumps(CONFIG))
