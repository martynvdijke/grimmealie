import json
import os
from pathlib import Path

CONFIG_FILE = Path("grimmealie-config.json")

# Secrets can be supplied out-of-band so they are never written to disk.
# Environment variables take precedence over the keyring, which takes
# precedence over values stored in the config file.
SECRET_ENV_VARS = {
    "mealie_key": "GRIMMEALIE_MEALIE_KEY",
    "grimmory_password": "GRIMMEALIE_GRIMMORY_PASSWORD",
}
KEYRING_SERVICE = "grimmealie"

CONFIG_MODE = 0o600


def _keyring_get(name: str) -> str | None:
    """Return a secret from the OS keyring, if keyring is installed."""
    try:
        import keyring

        return keyring.get_password(KEYRING_SERVICE, name)
    except Exception:
        # keyring is optional and may be unavailable on headless systems.
        return None


def _env_secret(name: str) -> str | None:
    env_name = SECRET_ENV_VARS.get(name)
    if not env_name:
        return None
    return os.environ.get(env_name)


class Config:
    def __init__(self):
        self.grimmory_url: str = "https://booklore.vandijke.xyz"
        self.mealie_url: str = "https://mealie.vandijke.xyz"
        self.mealie_key: str = ""
        self.book_id: str = ""
        self.grimmory_login: bool = False
        self.grimmory_username: str = ""
        self.grimmory_password: str = ""
        # Secrets that came from env/keyring and must not be persisted again.
        self._external_secrets: set[str] = set()

    def __repr__(self) -> str:
        return (
            f"Config(grimmory_url={self.grimmory_url!r}, "
            f"mealie_url={self.mealie_url!r}, "
            f"mealie_key={mask(self.mealie_key)!r}, "
            f"book_id={self.book_id!r}, "
            f"grimmory_login={self.grimmory_login!r}, "
            f"grimmory_username={self.grimmory_username!r}, "
            f"grimmory_password={mask(self.grimmory_password)!r})"
        )

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

        # Out-of-band secrets win over anything persisted in the config file.
        for name in SECRET_ENV_VARS:
            value = _env_secret(name)
            if value:
                setattr(cfg, name, value)
                cfg._external_secrets.add(name)
                continue
            value = _keyring_get(name)
            if value:
                setattr(cfg, name, value)
                cfg._external_secrets.add(name)

        return cfg

    def save(self) -> None:
        data = {
            "grimmory_url": self.grimmory_url,
            "mealie_url": self.mealie_url,
            # Never re-persist secrets supplied via env/keyring.
            "mealie_key": (
                "" if "mealie_key" in self._external_secrets else self.mealie_key
            ),
            "book_id": self.book_id,
            "grimmory_login": self.grimmory_login,
            "grimmory_username": self.grimmory_username,
            "grimmory_password": (
                ""
                if "grimmory_password" in self._external_secrets
                else self.grimmory_password
            ),
        }
        # Create with 0600 from the start so there is no window where the
        # file is readable by other users. chmod also fixes pre-existing files.
        fd = os.open(CONFIG_FILE, os.O_WRONLY | os.O_CREAT | os.O_TRUNC, CONFIG_MODE)
        try:
            os.fchmod(fd, CONFIG_MODE)
            with os.fdopen(fd, "w") as fh:
                fh.write(json.dumps(data, indent=2))
        except Exception:
            os.close(fd)
            raise


def mask(value: str) -> str:
    """Mask a secret for display. Never leak length or characters."""
    if not value:
        return ""
    return "••••"


def is_configured(cfg: "Config") -> bool:
    return bool(cfg.grimmory_url and cfg.mealie_url and cfg.mealie_key)
