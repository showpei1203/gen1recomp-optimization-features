#!/usr/bin/env python3
"""Deterministic self-test for tools/showdown_sprites_ingest.py.

No network access and no copyrighted sprite assets are required. The test creates a
small synthetic animated GIF, runs front/back ingestion, and checks GBA output sizes.
It also exercises the S1 host-palette remap path.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
from pathlib import Path

from PIL import Image


def make_gif(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    frames = []
    for top in (10, 12, 10):
        im = Image.new("RGBA", (80, 80), (0, 0, 0, 0))
        for y in range(top, top + 30):
            for x in range(20, 60):
                color = (220, 80, 40, 255) if (x + y) % 2 else (250, 180, 60, 255)
                im.putpixel((x, y), color)
        frames.append(im)
    frames[0].save(
        path,
        save_all=True,
        append_images=frames[1:],
        duration=[100, 150, 100],
        loop=0,
        disposal=2,
    )


def make_palette(path: Path) -> None:
    entries = [(0, 0, 0)] + [(i * 16, 255 - i * 12, i * 8) for i in range(1, 16)]
    path.write_text(
        "JASC-PAL\n0100\n16\n" + "\n".join(f"{r} {g} {b}" for r, g, b in entries) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tool", type=Path, default=Path("tools/showdown_sprites_ingest.py"))
    args = p.parse_args()

    with tempfile.TemporaryDirectory(prefix="showdown_s0_") as td:
        root = Path(td)
        src = root / "src"
        out = root / "out"
        palette = root / "host.pal"
        make_palette(palette)
        for lane in ("ani", "ani-back"):
            make_gif(src / lane / "cyndaquil.gif")

        subprocess.run(
            [
                sys.executable,
                str(args.tool),
                "--source-dir", str(src),
                "--output", str(out),
                "--species", "cyndaquil",
                "--lanes", "front", "back",
                "--host-palette", str(palette),
            ],
            check=True,
        )

        summary = json.loads((out / "summary.json").read_text(encoding="utf-8"))
        assert len(summary["animations"]) == 2
        for lane in ("front", "back"):
            d = out / "cyndaquil" / lane
            manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
            assert manifest["source_canvas"] == [80, 80]
            assert manifest["gba_canvas"] == [64, 64]
            assert manifest["frame_count"] == 3
            assert manifest["scale"] == 0.8
            assert manifest["palette_policy"] == "host_jasc_entries_1_to_15"
            assert manifest["palette_entries_visible"] == 15
            assert (d / "palette.pal").stat().st_size == 32
            for i in range(3):
                assert (d / f"frame_{i:03d}.4bpp").stat().st_size == 2048

    print("PASS: showdown S0 ingest self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
