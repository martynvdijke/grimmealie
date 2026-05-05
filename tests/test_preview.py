from PIL import Image
from grimmealie.preview import preview_image, _try_pillow_art, _terminal_width


def test_preview_missing_file(capsys):
    preview_image("/tmp/nonexistent.png")
    captured = capsys.readouterr()
    assert "not found" in captured.out


def test_preview_fallback_prints_name(capsys, tmp_path):
    img = Image.new("RGB", (10, 10))
    p = tmp_path / "test.png"
    img.save(p)
    preview_image(p)
    captured = capsys.readouterr()
    assert "test.png" in captured.out or "▀" in captured.out


def test_try_pillow_art_returns_true(tmp_path):
    img = Image.new("RGB", (50, 30), color="red")
    p = tmp_path / "test_art.png"
    img.save(p)
    result = _try_pillow_art(p)
    assert result is True


def test_try_pillow_art_small(tmp_path):
    img = Image.new("RGB", (2, 2), color="blue")
    p = tmp_path / "tiny.png"
    img.save(p)
    result = _try_pillow_art(p)
    assert result is True


def test_terminal_width():
    w = _terminal_width()
    assert w is None or w > 0


def test_try_pillow_art_rgba(tmp_path):
    img = Image.new("RGBA", (20, 10), (255, 0, 0, 128))
    p = tmp_path / "rgba.png"
    img.save(p)
    result = _try_pillow_art(p)
    assert result is True
