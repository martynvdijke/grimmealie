from pathlib import Path
from PIL import Image

from grimmealie.grimmory import _crop_region


def _check_crop(region: str, expected_w: int, expected_h: int, expected_color):
    src = Path("/tmp/test_crop_src.png")
    img = Image.new("RGB", (200, 100), color="white")
    for x in range(100):
        for y in range(100):
            img.putpixel((x, y), (0, 0, 255))
    for x in range(100, 200):
        for y in range(100):
            img.putpixel((x, y), (255, 0, 0))
    img.save(src)

    out = Path("/tmp/test_crop_out.png")
    if out.exists():
        out.unlink()

    if region == "full":
        img.save(out)
    else:
        img.save(src)
        _crop_region(src, region)  # type: ignore
        src.rename(out)

    assert out.exists()
    cropped = Image.open(out)
    assert cropped.size == (expected_w, expected_h), (
        f"{region}: got {cropped.size}, expected ({expected_w}, {expected_h})"
    )
    assert cropped.getpixel((0, 0)) == expected_color, f"{region}: color mismatch"
    out.unlink()
    src.unlink(missing_ok=True)


def test_crop_top():
    _check_crop("top", 200, 50, (0, 0, 255))


def test_crop_bottom():
    _check_crop("bottom", 200, 50, (0, 0, 255))


def test_crop_left():
    _check_crop("left", 100, 100, (0, 0, 255))


def test_crop_right():
    _check_crop("right", 100, 100, (255, 0, 0))


def test_crop_full():
    _check_crop("full", 200, 100, (0, 0, 255))
