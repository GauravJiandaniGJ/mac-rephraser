"""Generate assets/Rephrase.icns from scratch.

Draws a 1024px master (rounded square, indigo→violet gradient, white "R"
with a sparkle accent), then uses sips + iconutil to produce the .icns.
Only needed when changing the icon design — the generated .icns is
committed so normal builds don't require Pillow.

Usage:
    python3 -m venv /tmp/icon-venv && /tmp/icon-venv/bin/pip install Pillow
    /tmp/icon-venv/bin/python scripts/make_icon.py
"""

import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parent.parent
ICNS_PATH = ROOT / "assets" / "Rephrase.icns"

SIZE = 1024
# macOS icons leave a margin around the rounded square (Big Sur grid: ~100px)
MARGIN = 100
RADIUS = 185
GRADIENT_TOP = (79, 70, 229)  # indigo
GRADIENT_BOTTOM = (124, 58, 237)  # violet


def find_font(size: int) -> ImageFont.FreeTypeFont:
    candidates = [
        ("/System/Library/Fonts/SFNSRounded.ttf", 0),
        ("/System/Library/Fonts/SFNS.ttf", 0),
        ("/System/Library/Fonts/Helvetica.ttc", 1),  # index 1 = Helvetica Bold
        ("/System/Library/Fonts/Supplemental/Arial Bold.ttf", 0),
    ]
    for path, index in candidates:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size, index=index)
            except OSError:
                continue
    raise SystemExit("No usable system font found for the icon glyph")


def draw_master() -> Image.Image:
    img = Image.new("RGBA", (SIZE, SIZE), (0, 0, 0, 0))

    # Vertical gradient clipped to a rounded square
    gradient = Image.new("RGBA", (SIZE, SIZE))
    for y in range(SIZE):
        t = y / (SIZE - 1)
        color = tuple(
            round(GRADIENT_TOP[i] + (GRADIENT_BOTTOM[i] - GRADIENT_TOP[i]) * t)
            for i in range(3)
        )
        ImageDraw.Draw(gradient).line([(0, y), (SIZE, y)], fill=color + (255,))
    mask = Image.new("L", (SIZE, SIZE), 0)
    ImageDraw.Draw(mask).rounded_rectangle(
        [MARGIN, MARGIN, SIZE - MARGIN, SIZE - MARGIN], radius=RADIUS, fill=255
    )
    img.paste(gradient, (0, 0), mask)

    draw = ImageDraw.Draw(img)

    # Centered "R"
    font = find_font(560)
    bbox = draw.textbbox((0, 0), "R", font=font)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    x = (SIZE - w) / 2 - bbox[0] - 20
    y = (SIZE - h) / 2 - bbox[1]
    draw.text((x, y), "R", font=font, fill=(255, 255, 255, 255))

    # Four-point sparkle at the top-right of the glyph
    cx, cy, r = 700, 330, 78
    pinch = 0.22
    points = [
        (cx, cy - r),
        (cx + r * pinch, cy - r * pinch),
        (cx + r, cy),
        (cx + r * pinch, cy + r * pinch),
        (cx, cy + r),
        (cx - r * pinch, cy + r * pinch),
        (cx - r, cy),
        (cx - r * pinch, cy - r * pinch),
    ]
    draw.polygon(points, fill=(255, 255, 255, 235))

    return img


def build_icns(master: Image.Image) -> None:
    with tempfile.TemporaryDirectory() as tmp:
        master_png = Path(tmp) / "master.png"
        master.save(master_png)

        iconset = Path(tmp) / "Rephrase.iconset"
        iconset.mkdir()
        for points in (16, 32, 128, 256, 512):
            for scale in (1, 2):
                px = points * scale
                suffix = "" if scale == 1 else "@2x"
                out = iconset / f"icon_{points}x{points}{suffix}.png"
                subprocess.run(
                    ["sips", "-z", str(px), str(px), str(master_png), "--out", str(out)],
                    check=True,
                    capture_output=True,
                )

        ICNS_PATH.parent.mkdir(exist_ok=True)
        subprocess.run(
            ["iconutil", "-c", "icns", str(iconset), "-o", str(ICNS_PATH)],
            check=True,
        )
    print(f"Wrote {ICNS_PATH}")


if __name__ == "__main__":
    build_icns(draw_master())
