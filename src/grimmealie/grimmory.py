from pathlib import Path
from typing import Literal
from playwright.async_api import Page, BrowserContext

Region = Literal["full", "top", "bottom", "left", "right"]


class GrimmoryCapture:
    def __init__(
        self,
        base_url: str,
        viewport_width: int = 1920,
        viewport_height: int = 1080,
    ):
        self.base_url = base_url.rstrip("/")
        self.viewport = {"width": viewport_width, "height": viewport_height}

    async def create_page(self, context: BrowserContext) -> Page:
        page = await context.new_page()
        await page.set_viewport_size(self.viewport)  # type: ignore
        return page

    async def login(
        self, context: BrowserContext, username: str, password: str
    ) -> Page:
        page = await self.create_page(context)
        await page.goto(f"{self.base_url}/login", wait_until="networkidle")
        await page.wait_for_timeout(1000)
        await page.fill(
            'input[type="text"], input[name="username"], input[placeholder*="user"]',
            username,
        )
        await page.fill('input[type="password"]', password)
        await page.click('button[type="submit"]')
        await page.wait_for_url("**/dashboard**", timeout=10000)
        return page

    async def open_book(self, context: BrowserContext, book_id: str | int) -> Page:
        page = await self.create_page(context)
        await page.goto(
            f"{self.base_url}/ebook-reader/book/{book_id}",
            wait_until="domcontentloaded",
        )
        await page.wait_for_timeout(3000)
        return page

    async def capture_screenshot(
        self, page: Page, output_path: str | Path, region: Region = "full"
    ) -> Path:
        path = Path(output_path)
        await page.screenshot(path=str(path), full_page=False)
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
