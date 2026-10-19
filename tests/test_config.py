import os
import tempfile
from pathlib import Path

from grimmealie.config import Config


def test_config_defaults():
    cfg = Config()
    assert cfg.grimmory_url == "https://booklore.vandijke.xyz"
    assert cfg.mealie_url == "https://mealie.vandijke.xyz"
    assert cfg.mealie_key == ""
    assert cfg.book_id == ""
    assert cfg.grimmory_login is False
    assert cfg.grimmory_username == ""
    assert cfg.grimmory_password == ""


def test_config_roundtrip():
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        cfg = Config.load()
        cfg.grimmory_url = "https://example.com"
        cfg.mealie_url = "https://m.example.com"
        cfg.mealie_key = "secret-123"
        cfg.book_id = "42"
        cfg.grimmory_login = True
        cfg.grimmory_username = "user"
        cfg.grimmory_password = "pass"
        cfg.save()

        cfg2 = Config.load()
        assert cfg2.grimmory_url == "https://example.com"
        assert cfg2.mealie_url == "https://m.example.com"
        assert cfg2.mealie_key == "secret-123"
        assert cfg2.book_id == "42"
        assert cfg2.grimmory_login is True
        assert cfg2.grimmory_username == "user"
        assert cfg2.grimmory_password == "pass"


def test_config_bad_json():
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        Path("grimmealie-config.json").write_text("{bad json")
        cfg = Config.load()
        assert cfg.mealie_key == ""
        assert cfg.grimmory_url == "https://booklore.vandijke.xyz"


def test_config_saved_with_0600_permissions():
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        cfg = Config.load()
        cfg.mealie_key = "secret-123"
        cfg.save()
        mode = Path("grimmealie-config.json").stat().st_mode & 0o777
        assert mode == 0o600


def test_env_secret_overrides_config(monkeypatch):
    with tempfile.TemporaryDirectory() as tmp:
        os.chdir(tmp)
        cfg = Config.load()
        cfg.mealie_key = "file-key"
        cfg.grimmory_password = "file-pass"
        cfg.save()

        monkeypatch.setenv("GRIMMEALIE_MEALIE_KEY", "env-key")
        monkeypatch.setenv("GRIMMEALIE_GRIMMORY_PASSWORD", "env-pass")
        cfg2 = Config.load()
        assert cfg2.mealie_key == "env-key"
        assert cfg2.grimmory_password == "env-pass"

        # Re-saving must not leak env-only secrets back to disk.
        cfg2.save()
        import json

        data = json.loads(Path("grimmealie-config.json").read_text())
        assert data["mealie_key"] == ""
        assert data["grimmory_password"] == ""


def test_repr_redacts_secrets():
    cfg = Config()
    cfg.mealie_key = "super-secret-key"
    cfg.grimmory_password = "hunter2"
    rendered = repr(cfg)
    assert "super-secret-key" not in rendered
    assert "hunter2" not in rendered
    assert "••••" in rendered
