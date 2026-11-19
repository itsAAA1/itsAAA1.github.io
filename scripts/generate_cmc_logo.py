#!/usr/bin/env python3
"""Create a 200x200 transparent-background project-listing PNG from the existing source brand logo.

This performs image optimization only; ownership and on-chain identity equivalence
must still be reviewed before submitting the image to a market data provider.
"""
from collections import deque
from pathlib import Path

from PIL import Image, ImageOps

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "logo.png"
OUT = ROOT / "logo-cmc-200.png"


def near(a, b, threshold=30):
    return max(abs(int(a[i]) - int(b[i])) for i in range(3)) <= threshold


def prepare(src=SRC, dest=OUT):
    image = Image.open(src).convert("RGBA")
    w, h = image.size
    if w < 200 or h < 200:
        raise ValueError("Original project logo unexpectedly below 200 px")
    corners = [image.getpixel(pos) for pos in ((0, 0), (w-1, 0), (0, h-1), (w-1, h-1))]
    print(f"source_size={w}x{h}, original_corner_pixels={corners}")
    # Preserve native transparency where available. For a flat-colored opaque
    # background, remove the connected background from the outer edges only.
    if all(p[3] == 255 for p in corners) and all(near(p, corners[0], 15) for p in corners):
        bg = corners[0]
        px = image.load()
        queue = deque()
        visited = set()
        for x in range(w):
            queue.append((x, 0))
            queue.append((x, h-1))
        for y in range(h):
            queue.append((0, y))
            queue.append((w-1, y))
        while queue:
            x, y = queue.popleft()
            idx = y*w+x
            if idx in visited:
                continue
            visited.add(idx)
            p = px[x, y]
            if not near(p, bg, 28):
                continue
            px[x, y] = (p[0], p[1], p[2], 0)
            if x > 0: queue.append((x-1, y))
            if x+1 < w: queue.append((x+1, y))
            if y > 0: queue.append((x, y-1))
            if y+1 < h: queue.append((x, y+1))
        print("background_edge_removal=true")
    else:
        print("background_edge_removal=false; source has alpha/complex corners")

    bbox = image.getchannel("A").getbbox()
    if not bbox:
        raise ValueError("Source logo has no visible subject")
    subject = image.crop(bbox)
    subject.thumbnail((186, 186), Image.Resampling.LANCZOS)
    canvas = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
    canvas.alpha_composite(subject, ((200-subject.width)//2, (200-subject.height)//2))
    canvas.save(dest, format="PNG", optimize=True)
    check = Image.open(dest)
    if check.size != (200, 200) or check.mode != "RGBA":
        raise ValueError("Output not 200x200 RGBA")
    if check.getpixel((0,0))[3] != 0 or check.getpixel((199,199))[3] != 0:
        raise ValueError("Output background corners are not transparent")
    print(f"listing_logo_ready={dest.name}, size_bytes={dest.stat().st_size}, source_visual_equivalence_requires_review=true")


if __name__ == "__main__":
    prepare()
