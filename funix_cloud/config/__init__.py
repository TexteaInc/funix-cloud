import json
import os
from dataclasses import dataclass
from typing import Any


@dataclass
class ConfigDict:
    token: str | None
    api_server: str
    config_path: str

    def __init__(self, config_path: str):
        self.config_path = config_path
        self.read_config()

    def default(self):
        self.token = None
        self.api_server = "https://cloud-dev.funix.io"

    def to_dict(self):
        return {"token": self.token, "api_server": self.api_server}

    def from_dict(self, data):
        self.token = data["token"]
        self.api_server = data["api_server"]

    def read_config(self):
        if not os.path.exists(self.config_path):
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            self.default()
            with open(self.config_path, "w") as f:
                json.dump(self.to_dict(), f)
        else:
            with open(self.config_path, "r") as f:
                data = json.load(f)
                self.from_dict(data)

    def get(self, key: str, default: Any | None) -> Any | None:
        if hasattr(self, key):
            return getattr(self, key)
        else:
            return default

    def set(self, key: str, value: Any | None):
        if hasattr(self, key):
            setattr(self, key, value)
        else:
            raise KeyError(f"Key {key} does not exist in config.")
        with open(self.config_path, "w") as f:
            json.dump(self.to_dict(), f)
