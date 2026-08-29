#!/usr/bin/env python3
"""Deterministic self-test for tools/showdown_sprites_ingest.py.

No network access and no copyrighted sprite assets are required. The test creates
synthetic animated GIFs, including an ani/gen5ani filename collision, then checks
that exact lane matching and both full/short host-palette conversion remain GBA-safe.
"""
from __future__ import annotations

import argparse
import json
import subprocess
import sys
import tempfile
import zipfile
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


def make_palette(path: Path, count: int = 16) -> None:
    if count < 2 or count > 16:
        raise ValueError(count)
    entries = [(0, 0, 0)] + [(i * 16, 255 - i * 12, i * 8) for i in range(1, count)]
    path.write_text(
        f"JASC-PAL\n0100\n{count}\n" + "\n".join(f"{r} {g} {b}" for r, g, b in entries) + "\n",
        encoding="utf-8",
    )


def make_zip(src: Path, dst: Path) -> None:
    # Exact ani/ and ani-back/ files are authoritative. gen5ani entries are
    # deliberately present to guard against suffix-based false matches.
    for lane in ("gen5ani", "gen5ani-back"):
        make_gif(src / lane / "cyndaquil.gif")
    with zipfile.ZipFile(dst, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for path in sorted(src.glob("**/*.gif")):
            zf.write(path, f"sprites/{path.relative_to(src).as_posix()}")


def run_ingest(tool: Path, archive: Path, out: Path, palette: Path) -> dict:
    subprocess.run(
        [
            sys.executable,
            str(tool),
            "--zip", str(archive),
            "--output", str(out),
            "--species", "cyndaquil",
            "--lanes", "front", "back",
            "--host-palette", str(palette),
        ],
        check=True,
    )
    return json.loads((out / "summary.json").read_text(encoding="utf-8"))


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--tool", type=Path, default=Path("tools/showdown_sprites_ingest.py"))
    args = p.parse_args()

    with tempfile.TemporaryDirectory(prefix="showdown_s0_") as td:
        root = Path(td)
        src = root / "src"
        out = root / "out"
        out_short = root / "out_short"
        palette = root / "host16.pal"
        palette_short = root / "host13.pal"
        archive = root / "sprites.zip"
        make_palette(palette, 16)
        make_palette(palette_short, 13)
        for lane in ("ani", "ani-back"):
            make_gif(src / lane / "cyndaquil.gif")
        make_zip(src, archive)

        summary = run_ingest(args.tool, archive, out, palette)
        assert len(summary["animations"]) == 2
        assert summary["animations"][0]["source"].endswith("sprites/ani/cyndaquil.gif")
        assert summary["animations"][1]["source"].endswith("sprites/ani-back/cyndaquil.gif")
        for lane in ("front", "back"):
            d = out / "cyndaquil" / lane
            manifest = json.loads((d / "manifest.json").read_text(encoding="utf-8"))
            assert manifest["source_canvas"] == [80, 80]
            assert manifest["gba_canvas"] == [64, 64]
            assert manifest["frame_count"] == 3
            assert manifest["scale"] == 0.8
            assert manifest["palette_policy"] == "host_jasc_entries_1_to_15"
            assert manifest["host_palette_source_entries"] == 16
            assert manifest["palette_entries_visible"] == 15
            assert (d / "palette.pal").stat().st_size == 32
            for i in range(3):
                assert (d / f"frame_{i:03d}.4bpp").stat().st_size == 2048

        short_summary = run_ingest(args.tool, archive, out_short, palette_short)
        for animation in short_summary["animations"]:
            assert animation["palette_policy"] == "host_jasc_entries_1_to_n_padded_to_16"
            assert animation["host_palette_source_entries"] == 13
            assert animation["palette_entries_visible"] == 12
            d = out_short / "cyndaquil" / animation["lane"]
            assert (d / "palette.pal").stat().st_size == 32

    print("PASS: showdown S0 ingest self-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
