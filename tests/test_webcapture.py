from unittest.mock import patch, MagicMock, AsyncMock
from pathlib import Path
import asyncio

from grimmealie.webcapture import WebCapture, _crop_region


def test_label_from_url_simple():
    assert WebCapture.label_from_url("https://example.com") == "example_com"


def test_label_from_url_with_www():
    assert WebCapture.label_from_url("https://www.example.com") == "www_example_com"


def test_label_from_url_with_path():
    assert WebCapture.label_from_url("https://example.com/page/1") == "example_com"


def test_label_from_url_https():
    assert WebCapture.label_from_url("http://example.com") == "example_com"


def test_label_from_url_empty():
    assert WebCapture.label_from_url("https://") == "site"


def test_label_from_url_ip():
    assert WebCapture.label_from_url("https://192.168.1.1:8080") == "192_168_1_1"


def test_webcapture_init():
    wc = WebCapture(label="mysite", viewport_width=800, viewport_height=600)
    assert wc.label == "mysite"
    assert wc.viewport == {"width": 800, "height": 600}


def test_webcapture_default_viewport():
    wc = WebCapture(label="test")
    assert wc.viewport == {"width": 1920, "height": 1080}


@patch("grimmealie.webcapture._crop_region")
def test_capture_screenshot_full(mock_crop, tmp_path):
    mock_page = MagicMock()
    mock_page.screenshot = AsyncMock()
    out = tmp_path / "shot.png"

    wc = WebCapture(label="test")
    result = asyncio.run(wc.capture_screenshot(mock_page, str(out), "full"))

    mock_page.screenshot.assert_called_once_with(
        path=str(out), full_page=False, scale="device"
    )
    mock_crop.assert_not_called()
    assert result == Path(out)


@patch("grimmealie.webcapture._crop_region")
def test_capture_screenshot_cropped(mock_crop, tmp_path):
    mock_page = MagicMock()
    mock_page.screenshot = AsyncMock()
    out = tmp_path / "shot.png"

    wc = WebCapture(label="test")
    result = asyncio.run(wc.capture_screenshot(mock_page, str(out), "top"))

    mock_page.screenshot.assert_called_once_with(
        path=str(out), full_page=False, scale="device"
    )
    mock_crop.assert_called_once_with(Path(out), "top")
    assert result == Path(out)


@patch("PIL.Image.open")
def test_crop_region_top(mock_image_open, tmp_path):
    mock_img = MagicMock()
    mock_img.size = (200, 100)
    mock_image_open.return_value = mock_img

    p = tmp_path / "test.png"
    p.write_bytes(b"fake")
    _crop_region(p, "top")

    mock_image_open.assert_called_once_with(p)
    mock_img.crop.assert_called_once_with((0, 0, 200, 50))
    mock_img.crop.return_value.save.assert_called_once_with(p)


@patch("PIL.Image.open")
def test_crop_region_bottom(mock_image_open, tmp_path):
    mock_img = MagicMock()
    mock_img.size = (200, 100)
    mock_image_open.return_value = mock_img

    p = tmp_path / "test.png"
    p.write_bytes(b"fake")
    _crop_region(p, "bottom")

    mock_img.crop.assert_called_once_with((0, 50, 200, 100))


@patch("PIL.Image.open")
def test_crop_region_left(mock_image_open, tmp_path):
    mock_img = MagicMock()
    mock_img.size = (200, 100)
    mock_image_open.return_value = mock_img

    p = tmp_path / "test.png"
    p.write_bytes(b"fake")
    _crop_region(p, "left")

    mock_img.crop.assert_called_once_with((0, 0, 100, 100))


@patch("PIL.Image.open")
def test_crop_region_right(mock_image_open, tmp_path):
    mock_img = MagicMock()
    mock_img.size = (200, 100)
    mock_image_open.return_value = mock_img

    p = tmp_path / "test.png"
    p.write_bytes(b"fake")
    _crop_region(p, "right")

    mock_img.crop.assert_called_once_with((100, 0, 200, 100))


@patch("PIL.Image.open")
def test_crop_region_full_skips_crop(mock_image_open, tmp_path):
    mock_img = MagicMock()
    mock_img.size = (200, 100)
    mock_image_open.return_value = mock_img

    p = tmp_path / "test.png"
    p.write_bytes(b"fake")
    _crop_region(p, "full")

    mock_image_open.assert_called_once_with(p)
    mock_img.crop.assert_not_called()


@patch("PIL.Image.open")
def test_crop_region_swallows_error(mock_image_open):
    mock_image_open.side_effect = Exception("bad image")
    p = Path("/nonexistent/test.png")
    _crop_region(p, "top")
