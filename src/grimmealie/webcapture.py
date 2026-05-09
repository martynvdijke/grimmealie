from pathlib import Path
from typing import Literal
from urllib.parse import urlparse

from playwright.async_api import Page

Region = Literal["full", "top", "bottom", "left", "right"]


class WebCapture:
    def __init__(
        self,
        label: str = "site",
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ):
        self.label = label
        self.viewport = {"width": viewport_width, "height": viewport_height}

    @staticmethod
    def label_from_url(url: str) -> str:
        hostname = urlparse(url).hostname or "site"
        return hostname.replace(".", "_")

    async def capture_screenshot(
        self, page: Page, output_path: str | Path, region: Region = "full"
    ) -> Path:
        path = Path(output_path)
        await page.screenshot(path=str(path), full_page=False, scale="device")
        if region != "full":
            _crop_region(path, region)
        return path


def _crop_region(path: Path, region: Region) -> None:
    try:
        from PIL import Image

        img = Image.open(path)
        w, h = img.size
        boxes = {
            "top": (0, 0, w, h // 2),
            "bottom": (0, h // 2, w, h),
            "left": (0, 0, w // 2, h),
            "right": (w // 2, 0, w, h),
        }
        img.crop(boxes[region]).save(path)
    except Exception:
        pass
