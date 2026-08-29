#!/usr/bin/env python3
"""Emit Pokémon Showdown idle descriptors for SoulGold candidates."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

LANES = {
    "front": "Front",
    "back": "Back",
}
MAX_ACTION_FRAMES = 65535


def emit_lane(lines: list[str], species: str, lane: str, manifest: dict, asset_root: str) -> None:
    lane_sym = LANES[lane]
    species_sym = "".join(ch for ch in species.title() if ch.isalnum())
    prefix = f"Showdown{species_sym}{lane_sym}Idle"
    frames = manifest.get("frames", [])
    if not frames:
        raise ValueError(f"{lane} manifest has no frames")
    if len(frames) > MAX_ACTION_FRAMES:
        raise ValueError(f"{lane} has {len(frames)} frames; u16 frameCount would overflow")

    for frame in frames:
        idx = int(frame["index"])
        rel = f"{asset_root.rstrip('/')}/{lane}/frame_{idx:03d}.4bpp.lz"
        lines.append(f'const u32 g{prefix}Frame{idx:03d}[] = INCBIN_U32("{rel}");')
    lines.append("")
    lines.append(f"static const struct ShowdownGbaFrame s{prefix}Frames[] =")
    lines.append("{")
    for frame in frames:
        idx = int(frame["index"])
        duration = int(frame["duration_ticks_60hz"])
        if duration <= 0:
            raise ValueError(f"{lane} frame {idx} has non-positive duration")
        lines.append(f"    {{ .gfx = g{prefix}Frame{idx:03d}, .duration = {duration} }},")
    lines.append("};")
    lines.append("")
    lines.append(f"const struct ShowdownGbaAction g{prefix}Action =")
    lines.append("{")
    lines.append(f"    .frames = s{prefix}Frames,")
    lines.append(f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),")
    lines.append("    .loop = TRUE,")
    lines.append("};")
    lines.append("")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ingest-root", type=Path, required=True)
    ap.add_argument("--species", default="cyndaquil")
    ap.add_argument("--lanes", nargs="+", choices=tuple(LANES), default=("front", "back"))
    ap.add_argument("--asset-root", default="graphics/showdown/cyndaquil")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    lines = [
        "/* Auto-generated from Pokémon Showdown GIF manifests. */",
        '#include "global.h"',
        '#include "showdown_gba_runtime.h"',
        "",
    ]
    for lane in args.lanes:
        path = args.ingest_root / args.species / lane / "manifest.json"
        manifest = json.loads(path.read_text(encoding="utf-8"))
        emit_lane(lines, args.species, lane, manifest, args.asset_root)

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
