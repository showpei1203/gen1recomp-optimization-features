#!/usr/bin/env python3
"""Emit SoulGold G3R5B body-ground-stabilized ambient descriptors."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ACTIONS = ("Idle", "Walk", "Nod", "Rotate")
MAX_CORRECTION = 4


def sym(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--variant", choices=["player", "opponent"], required=True)
    ap.add_argument("--asset-root", required=True)
    args = ap.parse_args()

    ir = json.loads(args.ir.read_text(encoding="utf-8"))
    if ir.get("grounding", {}).get("battle_vertical_authority") != "ROBUST_BODY_SUPPORT_BASELINE":
        raise SystemExit("G3R5B emitter refuses IR without ROBUST_BODY_SUPPORT_BASELINE authority")
    if ir.get("shadow", {}).get("policy") != "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK_CENTERED_ON_BATTLE_X":
        raise SystemExit("G3R5B emitter refuses IR without centered authentic PMD shadow contract")

    species = ir["species"]["name"]
    species_sym = sym(species)
    variant_sym = sym(args.variant.title())
    missing = [name for name in ACTIONS if name not in ir["actions"]]
    if missing:
        raise SystemExit(f"IR missing required G3R5B ambient actions: {missing}")

    lines = [
        "/* Auto-generated SoulGold G3R5B body-ground-stabilized ambient descriptors. */",
        "/* presentationY comes from body support, never PMDCollab Shadow.png positions. */",
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
            dy = int(frame.get("presentation_dy", 0))
            if int(frame.get("presentation_dx", 0)) != 0 or abs(dy) > MAX_CORRECTION:
                raise SystemExit(f"Invalid G3R5B correction: {species}/{action_name}/{idx} dy={dy}")
            lines.append(
                f"    {{ .gfx = {frame_symbols[(action_name, idx)]}, .duration = {int(frame['duration'])}, "
                f".presentationX = 0, .presentationY = {dy} }},"
            )
        lines += ["};", "", f"const struct PmdGbaAction g{prefix}Action =", "{",
                  f"    .frames = s{prefix}Frames,", f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),",
                  "    .loop = FALSE,", "};", ""]

    home_prefix = f"Pmd{species_sym}{variant_sym}Home"
    idle0 = frame_symbols[("Idle", 0)]
    if int(ir["actions"]["Idle"]["frames"][0].get("presentation_dy", 0)) != 0:
        raise SystemExit("G3R5B Idle0 must remain zero-offset")
    lines += [
        f"static const struct PmdGbaFrame s{home_prefix}Frames[] =", "{",
        f"    {{ .gfx = {idle0}, .duration = 1, .presentationX = 0, .presentationY = 0 }},", "};", "",
        f"const struct PmdGbaAction g{home_prefix}Action =", "{",
        f"    .frames = s{home_prefix}Frames,", f"    .frameCount = ARRAY_COUNT(s{home_prefix}Frames),",
        "    .loop = TRUE,", "};", "",
    ]

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output} (G3R5B body-ground, species={species}, variant={args.variant})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
