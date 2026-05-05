import json
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
