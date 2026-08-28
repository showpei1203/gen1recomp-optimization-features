#!/usr/bin/env python3
"""Emit SoulGold G3R6A ambient + Hurt PMD body descriptors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ACTIONS = ("Idle", "Walk", "Nod", "Rotate", "Hurt")
AMBIENT_ACTIONS = ("Idle", "Walk", "Nod", "Rotate")
MAX_CORRECTION = 1
AUTHORITY = "G3R6A_AMBIENT_ACCEPTED_PLUS_HURT_SOURCE_BODY_CENTER"


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
    if ir.get("grounding", {}).get("battle_vertical_authority") != AUTHORITY:
        raise SystemExit(f"G3R6A emitter refuses IR without {AUTHORITY}")

    species = ir["species"]["name"]
    species_sym = sym(species)
    variant_sym = sym(args.variant.title())
    missing = [name for name in ACTIONS if name not in ir["actions"]]
    if missing:
        raise SystemExit(f"IR missing required G3R6A actions: {missing}")

    lines = [
        "/* Auto-generated SoulGold G3R6A ambient + Hurt descriptors. */",
        "/* Hurt preserves PMDCollab body-center geometry; no grounding heuristic is applied. */",
        '#include "global.h"',
        '#include "pmd_gba_runtime.h"',
        "",
    ]
    frame_symbols = {}
    for action_name in ACTIONS:
        rec = ir["actions"][action_name]
        prefix = f"Pmd{species_sym}{variant_sym}{sym(action_name)}"
        for frame in rec["frames"]:
            idx = int(frame["index"])
            symbol = f"g{prefix}Frame{idx:02d}"
            rel = f"{args.asset_root.rstrip('/')}/{action_name.lower()}/frame_{idx:02d}.4bpp.lz"
            lines.append(f'const u32 {symbol}[] = INCBIN_U32("{rel}");')
            frame_symbols[(action_name, idx)] = symbol
        lines += ["", f"static const struct PmdGbaFrame s{prefix}Frames[] =", "{"]
        for frame in rec["frames"]:
            idx = int(frame["index"])
            dx = int(frame.get("presentation_dx", 0))
            dy = int(frame.get("presentation_dy", 0))
            if dx != 0 or abs(dy) > MAX_CORRECTION:
                raise SystemExit(f"Invalid G3R6A correction: {species}/{action_name}/{idx}=({dx},{dy})")
            if action_name == "Hurt" and (dx != 0 or dy != 0):
                raise SystemExit(f"Hurt must remain source-authoritative with zero presentation correction: {species}/{idx}")
            lines.append(
                f"    {{ .gfx = {frame_symbols[(action_name, idx)]}, .duration = {int(frame['duration'])}, "
                f".presentationX = {dx}, .presentationY = {dy} }},"
            )
        lines += ["};", "", f"const struct PmdGbaAction g{prefix}Action =", "{",
                  f"    .frames = s{prefix}Frames,", f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),",
                  "    .loop = FALSE,", "};", ""]

    home_prefix = f"Pmd{species_sym}{variant_sym}Home"
    idle0 = frame_symbols[("Idle", 0)]
    lines += [
        f"static const struct PmdGbaFrame s{home_prefix}Frames[] =", "{",
        f"    {{ .gfx = {idle0}, .duration = 1, .presentationX = 0, .presentationY = 0 }},", "};", "",
        f"const struct PmdGbaAction g{home_prefix}Action =", "{",
        f"    .frames = s{home_prefix}Frames,", f"    .frameCount = ARRAY_COUNT(s{home_prefix}Frames),",
        "    .loop = TRUE,", "};", "",
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output} (G3R6A, species={species}, variant={args.variant})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
