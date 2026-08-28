#!/usr/bin/env python3
"""Emit SoulGold G3R10 PMDCollab special-state body descriptors."""
from __future__ import annotations

import argparse
import json
from pathlib import Path

FORMAT = "PMD_GBA_SOULGOLD_G3R10_SPECIAL_STATE_IR"
SUPPORTED_ACTIONS = ("Sleep", "EventSleep", "Wake")


def sym(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--variant", choices=["player", "opponent"], required=True)
    ap.add_argument("--action", choices=SUPPORTED_ACTIONS, required=True)
    ap.add_argument("--asset-root", required=True)
    args = ap.parse_args()

    ir = json.loads(args.ir.read_text(encoding="utf-8"))
    if ir.get("format") != FORMAT:
        raise SystemExit(f"G3R10 emitter refuses IR without {FORMAT}")
    action = ir.get("actions", {}).get(args.action)
    if not action:
        raise SystemExit(f"G3R10 IR missing {args.action}")

    species = ir["species"]["name"]
    prefix = f"Pmd{sym(species)}{sym(args.variant.title())}{sym(args.action)}"
    frames = action["frames"]
    folder = action["folder"]
    loop = bool(action.get("loop", False))

    lines = [
        f"/* Auto-generated SoulGold G3R10 PMDCollab {args.action} body descriptors. */",
        "/* Source-view layout is resolved per action from PMDCollab geometry. */",
        '#include "global.h"',
        '#include "pmd_gba_runtime.h"',
        "",
    ]
    for f in frames:
        i = int(f["index"])
        if int(f["opaque_source_pixels"]) != int(f["opaque_copied_pixels"]):
            raise SystemExit(f"{args.action} visible pixel mismatch {species}/{i}")
        lines.append(
            f'const u32 g{prefix}Frame{i:02d}[] = INCBIN_U32("{args.asset_root.rstrip("/")}/{folder}/frame_{i:02d}.4bpp.lz");'
        )

    lines += ["", f"static const struct PmdGbaFrame s{prefix}Frames[] =", "{"]
    for f in frames:
        i = int(f["index"])
        lines.append(
            f"    {{ .gfx = g{prefix}Frame{i:02d}, .duration = {int(f['duration'])}, .presentationX = 0, .presentationY = 0 }},"
        )
    lines += [
        "};",
        "",
        f"const struct PmdGbaAction g{prefix}Action =",
        "{",
        f"    .frames = s{prefix}Frames,",
        f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),",
        f"    .loop = {'TRUE' if loop else 'FALSE'},",
        "};",
        "",
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output}: {species} {args.action} frames={len(frames)} loop={loop}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
