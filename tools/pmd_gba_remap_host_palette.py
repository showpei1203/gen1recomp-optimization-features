#!/usr/bin/env python3
"""Remap converted PMD frame PNGs to an existing host 16-color JASC palette.

G1 uses this to isolate rolling-cache/frame playback from palette ownership.
Index 0 is treated as transparent; opaque pixels are mapped to host entries
1..15 with nearest RGB distance and no dithering/resampling.
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import List, Sequence, Tuple

try:
    from PIL import Image
except ImportError as exc:
    raise SystemExit("Pillow is required: python -m pip install Pillow") from exc

RGB = Tuple[int, int, int]


def read_jasc(path: Path) -> List[RGB]:
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if len(lines) < 3 or lines[0] != "JASC-PAL" or lines[1] != "0100":
        raise ValueError(f"Not a JASC-PAL 0100 file: {path}")
    count = int(lines[2])
    entries: List[RGB] = []
    for line in lines[3 : 3 + count]:
        parts = [int(x) for x in line.split()]
        if len(parts) != 3 or any(x < 0 or x > 255 for x in parts):
            raise ValueError(f"Invalid palette row: {line}")
        entries.append(tuple(parts))
    if len(entries) != count:
        raise ValueError(f"Palette expected {count} entries, got {len(entries)}")
    if count != 16:
        raise ValueError(f"GBA 4bpp host palette must contain 16 entries, got {count}")
    return entries


def nearest(rgb: RGB, visible: Sequence[RGB]) -> int:
    best_i = 0
    best_d = None
    for i, p in enumerate(visible):
        d = sum((rgb[c] - p[c]) ** 2 for c in range(3))
        if best_d is None or d < best_d:
            best_i, best_d = i, d
    return best_i


def remap(path: Path, palette: Sequence[RGB]) -> None:
    src = Image.open(path).convert("RGBA")
    out = Image.new("P", src.size, 0)
    flat = []
    for color in palette:
        flat.extend(color)
    flat.extend([0] * (768 - len(flat)))
    out.putpalette(flat)
    visible = palette[1:16]
    src_px = src.load()
    dst_px = out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = src_px[x, y]
            if a == 0:
                dst_px[x, y] = 0
            else:
                dst_px[x, y] = nearest((r, g, b), visible) + 1
    out.info["transparency"] = 0
    out.save(path, optimize=False)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--frames-root", type=Path, required=True)
    ap.add_argument("--host-palette", type=Path, required=True)
    ap.add_argument("--glob", default="**/frame_*.png")
    args = ap.parse_args()

    palette = read_jasc(args.host_palette)
    files = sorted(args.frames_root.glob(args.glob))
    if not files:
        raise SystemExit(f"No frames matched {args.glob!r} under {args.frames_root}")
    for path in files:
        remap(path, palette)
    print(f"Remapped {len(files)} frame(s) to {args.host_palette}; index 0 remains transparent")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
