#!/usr/bin/env python3
"""Emit SoulGold G3R7 PMDCollab Shoot body descriptors and source markers."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FORMAT = "PMD_GBA_SOULGOLD_G3R7_SHOOT_IR"


def sym(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--variant", choices=["player", "opponent"], required=True)
    ap.add_argument("--asset-root", required=True)
    args = ap.parse_args()

    ir = json.loads(args.ir.read_text(encoding="utf-8"))
    if ir.get("format") != FORMAT:
        raise SystemExit(f"G3R7 Shoot emitter refuses IR without {FORMAT}")
    action = ir.get("actions", {}).get("Shoot")
    if not action:
        raise SystemExit("G3R7 Shoot IR missing Shoot action")

    species = ir["species"]["name"]
    prefix = f"Pmd{sym(species)}{sym(args.variant.title())}Shoot"
    frames = action["frames"]
    if not frames:
        raise SystemExit("G3R7 Shoot action has no frames")

    lines = [
        "/* Auto-generated SoulGold G3R7 PMDCollab Shoot body descriptors. */",
        "/* Source Hit/Return markers are preserved as metadata, not combat timing authority. */",
        '#include "global.h"',
        '#include "pmd_gba_runtime.h"',
        "",
    ]
    for frame in frames:
        idx = int(frame["index"])
        if int(frame.get("presentation_dx", 0)) != 0 or int(frame.get("presentation_dy", 0)) != 0:
            raise SystemExit(f"G3R7 Shoot must not inject runtime x2/y2: {species}/{idx}")
        if int(frame["opaque_source_pixels"]) != int(frame["opaque_copied_pixels"]):
            raise SystemExit(f"G3R7 Shoot visible pixel mismatch: {species}/{idx}")
        lines.append(
            f'const u32 g{prefix}Frame{idx:02d}[] = INCBIN_U32("{args.asset_root.rstrip("/")}/shoot/frame_{idx:02d}.4bpp.lz");'
        )

    lines += ["", f"static const struct PmdGbaFrame s{prefix}Frames[] =", "{"]
    for frame in frames:
        idx = int(frame["index"])
        lines.append(
            f"    {{ .gfx = g{prefix}Frame{idx:02d}, .duration = {int(frame['duration'])}, .presentationX = 0, .presentationY = 0 }},"
        )
    lines += [
        "};", "",
        f"const struct PmdGbaAction g{prefix}Action =", "{",
        f"    .frames = s{prefix}Frames,",
        f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),",
        "    .loop = FALSE,",
        "};", "",
        f"const u8 g{prefix}RushFrame = {255 if action.get('rush_frame') is None else int(action['rush_frame'])};",
        f"const u8 g{prefix}HitFrame = {255 if action.get('hit_frame') is None else int(action['hit_frame'])};",
        f"const u8 g{prefix}ReturnFrame = {255 if action.get('return_frame') is None else int(action['return_frame'])};",
        "",
    ]
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}: {species} Shoot frames={len(frames)}, hit={action.get('hit_frame')}, return={action.get('return_frame')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
