#!/usr/bin/env python3
"""Photo -> ASCII portrait.

Run this by hand only when the source photo changes; it writes portrait.txt,
which is committed and read by generate_all.py. Keeping it out of CI means the
daily Action needs no image libraries.

    pip install pillow numpy
    python tools/make_portrait.py                 # uses assets/photo.jpg (gitignored)
    python tools/make_portrait.py other.png       # uses another file
    python tools/make_portrait.py --grid          # coordinate overlay, for re-tuning CROP

assets/ is gitignored, so a photo left there is used but never published. Only
portrait.txt is committed, and it is all generate_all.py needs.

The source photo must have its background removed (flat black or transparent).
The matte is recovered by flood-filling inward from the border, which keeps dark
jacket interiors as subject instead of punching holes through them.
"""

import os
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageOps

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_SRC = os.path.join(ROOT, "assets", "photo.jpg")
OUT = os.path.join(ROOT, "portrait.txt")

# ── tuning ────────────────────────────────────────────────────────────────────
CROP = (140, 0, 720, 620)   # head + shoulders; face carries the frame
COLS = 58
CELL_ASPECT = 2.05          # monospace cell height / width

BG_THRESHOLD = 10           # luminance at or below this is candidate background
FEATHER = 1.5               # matte edge softness, px
GAMMA = 0.78
MIN_INK = 0.16              # hair and jacket are near-black; keep them inked
LOCAL_CONTRAST = (14, 200)  # UnsharpMask(radius, percent) — broad, for form
DETAIL = (2, 150)           # UnsharpMask(radius, percent) — tight, for features

RAMP = " .':;+*ocbdkhaoOQ0ZmMW8%B@"


def matte(im):
    """Recover the subject mask by flood-filling the removed background inward."""
    g = np.asarray(ImageOps.grayscale(im)).astype(np.float32)
    w, h = im.size

    # .copy() detaches from the numpy buffer; floodfill silently no-ops on an
    # Image that is still backed by the array it was created from.
    b = Image.fromarray(((g <= BG_THRESHOLD) * 255).astype(np.uint8)).copy()

    for seed in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1),
                 (w // 2, 0), (0, h // 2), (w - 1, h // 2), (w // 2, h - 1)]:
        if b.getpixel(seed) == 255:
            ImageDraw.floodfill(b, seed, 128, thresh=0)

    m = ((np.asarray(b) != 128).astype(np.uint8) * 255)
    return np.asarray(
        Image.fromarray(m).filter(ImageFilter.GaussianBlur(FEATHER))
    ).astype(np.float32) / 255.0


def to_ascii(src):
    im = src.crop(CROP)
    mask = matte(im)

    sharp = (im.filter(ImageFilter.UnsharpMask(*LOCAL_CONTRAST, 1))
               .filter(ImageFilter.UnsharpMask(*DETAIL, 1)))
    g = np.asarray(ImageOps.grayscale(sharp)).astype(np.float32)

    sel = g[mask > 0.6]
    lo, hi = np.percentile(sel, 2), np.percentile(sel, 99)
    g = np.clip((g - lo) / max(1.0, hi - lo), 0.0, 1.0)
    g = np.power(g, GAMMA)
    g = (MIN_INK + (1.0 - MIN_INK) * g) * mask

    w, h = im.size
    rows = max(1, int(round(COLS * (h / w) / CELL_ASPECT)))
    a = np.clip(np.asarray(
        Image.fromarray((g * 255).astype(np.uint8)).resize((COLS, rows), Image.LANCZOS)
    ).astype(np.float32) / 255.0, 0.0, 1.0)

    n = len(RAMP) - 1
    return ["".join(RAMP[int(round(v * n))] for v in a[r]).rstrip()
            for r in range(rows)]


def grid_overlay(src, path, step=100, scale=1):
    c = src.copy()
    d = ImageDraw.Draw(c)
    for gx in range(0, c.width, step):
        d.line([(gx, 0), (gx, c.height)], fill=(255, 0, 0), width=2)
        d.text((gx + 3, 6), str(gx), fill=(0, 255, 255))
    for gy in range(0, c.height, step):
        d.line([(0, gy), (c.width, gy)], fill=(255, 0, 0), width=2)
        d.text((6, gy + 3), str(gy), fill=(255, 255, 0))
    c.save(path)


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    path = args[0] if args else DEFAULT_SRC
    if not os.path.exists(path):
        sys.exit(f"no photo at {path} — pass one as an argument, or drop it "
                 f"at assets/photo.jpg (gitignored, so it stays private)")
    src = Image.open(path).convert("RGB")

    if "--grid" in sys.argv:
        grid_overlay(src, "grid.png")
        sys.exit("wrote grid.png — read CROP off it, then rerun without --grid")

    lines = to_ascii(src)
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")
    print(f"wrote {OUT} — {len(lines)} rows x {max(len(l) for l in lines)} cols")
    print("\n".join(lines))
