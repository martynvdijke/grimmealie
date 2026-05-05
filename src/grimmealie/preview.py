import os
import shutil
import subprocess
from pathlib import Path


def preview_image(path: str | Path) -> None:
    path = Path(path)
    if not path.exists():
        print(f"  (file not found: {path})")
        return

    if _try_kitty(path):
        return
    if _try_viu(path):
        return
    if _try_chafa(path):
        return
    if _try_catimg(path):
        return
    if _try_pillow_art(path):
        return

    print(f"  → {path.name}")


def _try_pillow_art(path: Path) -> bool:
    try:
        from PIL import Image

        img = Image.open(path)
        term_cols = _terminal_width()
        width = min(term_cols - 6, 200) if term_cols else 120

        aspect = img.height / img.width
        height = max(1, int(width * aspect * 0.5))

        thumb = img.resize((width, height * 2), Image.LANCZOS)  # type: ignore

        if thumb.mode != "RGB":
            thumb = thumb.convert("RGB")

        reset = "\033[0m"
        lines = []
        for y in range(height):
            line = ""
            for x in range(width):
                px1 = thumb.getpixel((x, y * 2))
                px2 = thumb.getpixel((x, y * 2 + 1))
                r1, g1, b1 = px1[0], px1[1], px1[2]  # type: ignore
                r2, g2, b2 = px2[0], px2[1], px2[2]  # type: ignore
                line += f"\033[38;2;{r1};{g1};{b1}m\033[48;2;{r2};{g2};{b2}m\u2580"
            lines.append(line + reset)

        print()
        for line in lines:
            print(line)
        print()
        return True
    except Exception:
        return False


def _terminal_width() -> int | None:
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return None


def _try_kitty(path: Path) -> bool:
    if "KITTY_WINDOW_ID" not in os.environ:
        return False
    try:
        with open(path, "rb") as f:
            data = f.read()
        import base64

        encoded = base64.b64encode(data).decode()
        chunk_size = 4096
        payloads = [
            encoded[i : i + chunk_size] for i in range(0, len(encoded), chunk_size)
        ]
        total = len(payloads)
        for i, chunk in enumerate(payloads):
            if i == 0:
                cmd = f"\033_Ga=T,f=100,m=1;{chunk}\033\\"
            elif i == total - 1:
                cmd = f"\033_Gm=0;{chunk}\033\\"
            else:
                cmd = f"\033_Gm=1;{chunk}\033\\"
            print(cmd, end="", flush=True)
        return True
    except Exception:
        return False


def _try_viu(path: Path) -> bool:
    viu = shutil.which("viu")
    if not viu:
        return False
    try:
        subprocess.run([viu, str(path)], check=True)
        return True
    except Exception:
        return False


def _try_chafa(path: Path) -> bool:
    chafa = shutil.which("chafa")
    if not chafa:
        return False
    try:
        subprocess.run([chafa, str(path)], check=True)
        return True
    except Exception:
        return False


def _try_catimg(path: Path) -> bool:
    catimg = shutil.which("catimg")
    if not catimg:
        return False
    try:
        subprocess.run([catimg, str(path)], check=True)
        return True
    except Exception:
        return False
