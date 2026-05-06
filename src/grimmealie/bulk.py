from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.prompt import Prompt, Confirm
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich import box

from .mealie import MealieClient
from .config import Config, is_configured

con = Console()

SCREENSHOTS_DIR = Path("screenshots")


def parse_selection(selection: str, screenshots: list[Path]) -> list[Path]:
    if selection.lower() == "all":
        return list(screenshots)

    selected = []
    indices = set()
    for part in selection.split(","):
        part = part.strip()
        if not part:
            continue
        if "-" in part:
            start, end = part.split("-", 1)
            indices.update(range(int(start), int(end) + 1))
        else:
            indices.add(int(part))

    for i in indices:
        if 1 <= i <= len(screenshots):
            selected.append(screenshots[i - 1])

    selected.sort()
    return selected


def list_screenshots(directory: Path = SCREENSHOTS_DIR) -> list[Path]:
    if not directory.exists():
        return []
    return sorted(directory.glob("*.png"))


def display_screenshots(paths: list[Path]) -> None:
    if not paths:
        con.print(
            Panel(
                "No screenshots found in [bold]screenshots/[/]", border_style="yellow"
            )
        )
        return

    table = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    table.add_column("#", style="dim", width=4)
    table.add_column("Filename")
    table.add_column("Size", justify="right")

    for i, p in enumerate(paths, 1):
        size_kb = p.stat().st_size / 1024
        table.add_row(str(i), p.name, f"{size_kb:.0f} KB")

    con.print(
        Panel(table, title=f"Screenshots ({len(paths)} total)", border_style="cyan")
    )


def bulk_upload(cfg, selected: list[Path], delete_after: bool = True) -> bool:
    if not selected:
        con.print("  [yellow]![/] No images selected")
        return False

    con.print(f"  [cyan]→[/] Uploading {len(selected)} image(s) to Mealie...")
    try:
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            transient=True,
        ) as progress:
            progress.add_task("Sending...", total=None)
            slug = MealieClient(
                cfg.mealie_url, cfg.mealie_key
            ).create_recipe_from_images([str(p) for p in selected])
        con.print("  [green]✓[/] Recipe created!")
        con.print(f"    {cfg.mealie_url}/g/home/r/{slug}")

        if delete_after:
            for p in selected:
                try:
                    p.unlink(missing_ok=True)
                except Exception:
                    pass
            con.print("  [cyan]→[/] Uploaded images deleted")

        return True
    except Exception as e:
        con.print(f"  [red]✗[/] Upload failed: {e}")
        return False


def run_bulk_upload(args) -> None:
    cfg = Config.load()

    if not is_configured(cfg):
        con.print(
            "  [yellow]![/] Mealie not configured. Run [bold]grimmealie[/] first to set up."
        )
        return

    con.print(f"    Mealie:   {cfg.mealie_url}")
    con.print()

    screenshots = list_screenshots()
    display_screenshots(screenshots)

    if not screenshots:
        return

    con.print()
    con.print("[bold]Select images to upload:[/]")
    con.print("  [dim]Examples: all, 1, 1-3, 1,3,5[/]")

    selection = Prompt.ask("Selection", default="all")
    selected = parse_selection(selection, screenshots)

    if not selected:
        con.print("  [yellow]![/] No valid selections")
        return

    con.print()
    con.print(f"  [bold]Selected {len(selected)} image(s):[/]")
    for p in selected:
        con.print(f"    [dim]• {p.name}[/]")
    con.print()

    delete_after = Confirm.ask("Delete images after upload?", default=True)
    con.print()

    success = bulk_upload(cfg, selected, delete_after=delete_after)
    if success:
        remaining = list_screenshots()
        if remaining:
            con.print()
            con.print(f"  [cyan]→[/] {len(remaining)} screenshot(s) remaining")
            display_screenshots(remaining)
