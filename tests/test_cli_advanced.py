from PIL import Image
from grimmealie.cli import _configured, _crop_from
from grimmealie.config import Config


def test_configured_false_when_empty():
    cfg = Config()
    cfg.grimmory_url = ""
    cfg.mealie_url = ""
    cfg.mealie_key = ""
    assert _configured(cfg) is False


def test_configured_false_partial():
    cfg = Config()
    cfg.grimmory_url = "https://example.com"
    cfg.mealie_url = ""
    cfg.mealie_key = ""
    assert _configured(cfg) is False


def test_configured_true():
    cfg = Config()
    cfg.grimmory_url = "https://g.example.com"
    cfg.mealie_url = "https://m.example.com"
    cfg.mealie_key = "key-123"
    assert _configured(cfg) is True


def test_crop_from_top(tmp_path):
    src = tmp_path / "full.png"
    dst = tmp_path / "crop.png"
    img = Image.new("RGB", (200, 100))
    img.save(src)
    _crop_from(src, dst, "top")
    assert dst.exists()
    assert Image.open(dst).size == (200, 50)


def test_crop_from_bottom(tmp_path):
    src = tmp_path / "full.png"
    dst = tmp_path / "crop.png"
    img = Image.new("RGB", (200, 100))
    img.save(src)
    _crop_from(src, dst, "bottom")
    assert dst.exists()
    assert Image.open(dst).size == (200, 50)


def test_crop_from_left(tmp_path):
    src = tmp_path / "full.png"
    dst = tmp_path / "crop.png"
    img = Image.new("RGB", (200, 100))
    img.save(src)
    _crop_from(src, dst, "left")
    assert dst.exists()
    assert Image.open(dst).size == (100, 100)


def test_crop_from_right(tmp_path):
    src = tmp_path / "full.png"
    dst = tmp_path / "crop.png"
    img = Image.new("RGB", (200, 100))
    img.save(src)
    _crop_from(src, dst, "right")
    assert dst.exists()
    assert Image.open(dst).size == (100, 100)
