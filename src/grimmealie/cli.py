import asyncio
import argparse
import logging
from datetime import datetime
from pathlib import Path

from playwright.async_api import async_playwright
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from .grimmory import GrimmoryCapture
from .mealie import MealieClient
from .config import Config, is_configured
from .preview import preview_image
from .bulk import run_bulk_upload

log = logging.getLogger("grimmealie")
con = Console()


def setup_logging(debug: bool) -> None:
    level = logging.DEBUG if debug else logging.INFO
    log_format = (
        "%(asctime)s [%(levelname)s] %(name)s: %(message)s" if debug else "%(message)s"
    )
    logging.basicConfig(level=level, format=log_format, datefmt="%H:%M:%S")
    if debug:
        logging.getLogger("httpx").setLevel(logging.DEBUG)
        logging.getLogger("httpcore").setLevel(logging.DEBUG)
        logging.getLogger("playwright").setLevel(logging.DEBUG)


def mask(s: str) -> str:
    return "*" * max(len(s), 8)


def stamp() -> str:
    return datetime.now().strftime("%H%M%S%f")[:-3]


REGION_MAP = {"f": "full", "t": "top", "b": "bottom", "l": "left", "r": "right"}


def _configured(cfg) -> bool:
    return is_configured(cfg)


def _setup(cfg) -> None:
    con.print()
    con.print(
        Panel(
            "[bold cyan]Grimmealie[/] — import recipes from [bold]Grimmory[/] into [bold]Mealie[/]",
            box=box.HEAVY,
        )
    )
    con.print(
        Panel(
            "[bold yellow]Credentials stored in plain text[/]\n"
            "Mealie API key and Grimmory password saved in [bold]grimmealie-config.json[/] "
            "(gitignored — keep it secure).",
            box=box.SQUARE,
            border_style="yellow",
        )
    )
    con.print()

    cfg.grimmory_url = Prompt.ask("Grimmory URL", default=cfg.grimmory_url)
    cfg.mealie_url = Prompt.ask("Mealie URL", default=cfg.mealie_url)
    cfg.mealie_key = Prompt.ask(
        "Mealie API Key",
        default=mask(cfg.mealie_key) if cfg.mealie_key else "",
        password=True,
    )
    cfg.grimmory_login = Confirm.ask(
        "Grimmory login required", default=cfg.grimmory_login
    )

    if cfg.grimmory_login:
        cfg.grimmory_username = Prompt.ask(
            "Grimmory username", default=cfg.grimmory_username
        )
        cfg.grimmory_password = Prompt.ask(
            "Grimmory password",
            default=mask(cfg.grimmory_password) if cfg.grimmory_password else "",
            password=True,
        )

    cfg.save()
    con.print("  [green]✓[/] Saved to grimmealie-config.json\n")


def _show_controls() -> None:
    grid = Table.grid(padding=(0, 1))
    grid.add_column()
    grid.add_column()
    grid.add_row("[bold]Enter[/]", "capture [dim](crop: f/t/b/l/r)[/]")
    grid.add_row("[bold]u[/]", "upload all captured pages to Mealie")
    grid.add_row("[bold]r[/]", "remove last capture")
    grid.add_row("[bold]q[/]", "quit to book menu")
    grid.add_row("", "")
    grid.add_row("[bold cyan]Tip[/]", "multi-page recipe: capture each, then u once")
    con.print(Panel(grid, title="Controls", box=box.ROUNDED, border_style="cyan"))
    con.print()


def _crop_from(src: Path, dst: Path, region: str) -> None:
    from PIL import Image

    img = Image.open(src)
    w, h = img.size
    boxes = {
        "top": (0, 0, w, h // 2),
        "bottom": (0, h // 2, w, h),
        "left": (0, 0, w // 2, h),
        "right": (w // 2, 0, w, h),
    }
    img.crop(boxes[region]).save(dst)


async def _capture_loop(cfg, page, args, capture) -> None:
    shots_dir = Path("screenshots")
    shots_dir.mkdir(exist_ok=True)
    paths: list[Path] = []

    _show_controls()

    while True:
        n = len(paths)
        badge = f"{n} captured" if n else "empty"

        cmd = Prompt.ask(
            f"[{badge}]",
            choices=["", "u", "r", "q"],
            default="",
            show_choices=False,
        )

        if cmd == "q":
            con.print("  [cyan]→[/] Returning to book menu")
            break

        elif cmd == "r":
            if paths:
                removed = paths.pop()
                try:
                    removed.unlink(missing_ok=True)
                except Exception:
                    pass
                con.print(f"  [yellow]![/] Removed {removed.name}")
            else:
                con.print("  [yellow]![/] Nothing to remove")

        elif cmd == "u":
            if not paths:
                con.print("  [yellow]![/] No captures yet")
                continue

            con.print(f"  [cyan]→[/] Uploading {len(paths)} image(s) to Mealie...")
            try:
                with Progress(
                    SpinnerColumn(),
                    TextColumn("[progress.description]{task.description}"),
                    transient=True,
                ) as progress:
                    progress.add_task("Sending...", total=None)
                    slug = MealieClient(
                        cfg.mealie_url, cfg.mealie_key
                    ).create_recipe_from_images(
                        [str(p) for p in paths]  # type: ignore[arg-type]
                    )
                con.print("  [green]✓[/] Recipe created!")
                con.print(f"    {cfg.mealie_url}/g/home/r/{slug}")
                for p in paths:
                    try:
                        p.unlink(missing_ok=True)
                    except Exception:
                        pass
                paths.clear()
                con.print("  [cyan]→[/] Ready for the next recipe")
            except Exception as e:
                con.print(f"  [red]✗[/] Upload failed: {e}")

        else:
            region_key = Prompt.ask(
                "Crop",
                choices=["f", "t", "b", "l", "r"],
                default="f",
                show_choices=True,
            )
            region = REGION_MAP[region_key]
            ts = stamp()
            full_path = shots_dir / f"{cfg.book_id}_{ts}_full.png"
            await capture.capture_screenshot(page, str(full_path), "full")

            if region == "full":
                paths.append(full_path)
                if not args.no_preview:
                    preview_image(full_path)
                con.print(f"  [green]✓[/] Captured (full) → [dim]{full_path.name}[/]")
            else:
                crop_path = shots_dir / f"{cfg.book_id}_{ts}_{region}.png"
                _crop_from(full_path, crop_path, region)
                paths.append(crop_path)
                if not args.no_preview:
                    preview_image(crop_path)
                con.print(
                    f"  [green]✓[/] Captured ({region}) → [dim]{crop_path.name}[/]  [dim](full saved: {full_path.name})[/]"
                )


async def run_interactive(args: argparse.Namespace) -> None:
    cfg = Config.load()

    if _configured(cfg):
        con.print("  [cyan]→[/] Using saved credentials from grimmealie-config.json")
        con.print(f"    Grimmory: {cfg.grimmory_url}")
        con.print(f"    Mealie:   {cfg.mealie_url}")
        con.print()
    else:
        _setup(cfg)

    con.print("  [cyan]→[/] Opening browser...")
    capture = GrimmoryCapture(cfg.grimmory_url)

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--disable-blink-features=AutomationControlled"],
        )
        context = await browser.new_context(device_scale_factor=2)

        try:
            if cfg.grimmory_login and cfg.grimmory_username:
                page = await capture.login(
                    context, cfg.grimmory_username, cfg.grimmory_password
                )

            while True:
                cfg.book_id = Prompt.ask("Book ID", default=cfg.book_id)
                cfg.save()

                page = await capture.open_book(context, cfg.book_id)
                await _capture_loop(cfg, page, args, capture)

                if not Confirm.ask("Process another book?", default=True):
                    break

        except Exception as e:
            con.print(f"  [red]✗[/] {e}")
            if args.debug:
                import traceback

                traceback.print_exc()
        finally:
            await browser.close()

    con.print("  [green]✓[/] Done!")


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Import recipes from Grimmory into Mealie"
    )
    parser.add_argument(
        "--debug", "-d", action="store_true", help="Enable debug logging"
    )
    parser.add_argument(
        "--no-preview", action="store_true", help="Disable terminal image preview"
    )
    parser.add_argument(
        "--bulk-upload",
        action="store_true",
        help="Bulk upload existing screenshots to Mealie",
    )

    args, _ = parser.parse_known_args()
    setup_logging(args.debug)

    if args.bulk_upload:
        run_bulk_upload(args)
    else:
        asyncio.run(run_interactive(args))


if __name__ == "__main__":
    main()
