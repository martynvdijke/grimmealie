import json
from pathlib import Path

CONFIG_FILE = Path("grimmealie-config.json")


class Config:
    def __init__(self):
        self.grimmory_url: str = "https://booklore.vandijke.xyz"
        self.mealie_url: str = "https://mealie.vandijke.xyz"
        self.mealie_key: str = ""
        self.book_id: str = ""
        self.grimmory_login: bool = False
        self.grimmory_username: str = ""
        self.grimmory_password: str = ""

    @classmethod
    def load(cls) -> "Config":
        cfg = cls()
        if CONFIG_FILE.exists():
            try:
                data = json.loads(CONFIG_FILE.read_text())
                cfg.grimmory_url = data.get("grimmory_url", cfg.grimmory_url)
                cfg.mealie_url = data.get("mealie_url", cfg.mealie_url)
                cfg.mealie_key = data.get("mealie_key", cfg.mealie_key)
                cfg.book_id = data.get("book_id", cfg.book_id)
                cfg.grimmory_login = data.get("grimmory_login", cfg.grimmory_login)
                cfg.grimmory_username = data.get(
                    "grimmory_username", cfg.grimmory_username
                )
                cfg.grimmory_password = data.get(
                    "grimmory_password", cfg.grimmory_password
                )
            except (json.JSONDecodeError, OSError):
                pass
        return cfg

    def save(self) -> None:
        data = {
            "grimmory_url": self.grimmory_url,
            "mealie_url": self.mealie_url,
            "mealie_key": self.mealie_key,
            "book_id": self.book_id,
            "grimmory_login": self.grimmory_login,
            "grimmory_username": self.grimmory_username,
            "grimmory_password": self.grimmory_password,
        }
        CONFIG_FILE.write_text(json.dumps(data, indent=2))
