#!/usr/bin/env python3
"""Emit SoulGold G3R6A ambient + Hurt PMD body descriptors.

Ambient presentation values are preserved from G3R5C. Hurt is allowed one
constant action-level presentation compensation when its source frame cannot be
placed on the 64x64 GBA canvas at the ambient anchor without clipping. The
converter moves the source body inside the canvas to a clip-safe anchor, then
this emitter restores the exact intended battle-space body center through x2/y2.
No source pixels are cropped or scaled.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ACTIONS = ("Idle", "Walk", "Nod", "Rotate", "Hurt")
AMBIENT_ACTIONS = ("Idle", "Walk", "Nod", "Rotate")
MAX_AMBIENT_CORRECTION = 1
MAX_HURT_CLIP_COMPENSATION = 16
AUTHORITY = "G3R6A_AMBIENT_ACCEPTED_PLUS_HURT_CLIP_SAFE_COMPENSATION"


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
    grounding = ir.get("grounding", {})
    if grounding.get("battle_vertical_authority") != AUTHORITY:
        raise SystemExit(f"G3R6A emitter refuses IR without {AUTHORITY}")

    species = ir["species"]["name"]
    species_sym = sym(species)
    variant_sym = sym(args.variant.title())
    missing = [name for name in ACTIONS if name not in ir["actions"]]
    if missing:
        raise SystemExit(f"IR missing required G3R6A actions: {missing}")

    hurt_comp = grounding.get("hurt_clip_compensation")
    if not isinstance(hurt_comp, list) or len(hurt_comp) != 2:
        raise SystemExit("G3R6A IR lacks two-axis Hurt clip compensation")
    hurt_dx, hurt_dy = int(hurt_comp[0]), int(hurt_comp[1])
    if abs(hurt_dx) > MAX_HURT_CLIP_COMPENSATION or abs(hurt_dy) > MAX_HURT_CLIP_COMPENSATION:
        raise SystemExit(f"Suspicious Hurt clip compensation: ({hurt_dx},{hurt_dy})")

    lines = [
        "/* Auto-generated SoulGold G3R6A ambient + Hurt descriptors. */",
        "/* Hurt uses a clip-safe canvas anchor plus exact battle-space compensation; no crop/scale. */",
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
            if action_name in AMBIENT_ACTIONS:
                if dx != 0 or abs(dy) > MAX_AMBIENT_CORRECTION:
                    raise SystemExit(f"Invalid ambient correction: {species}/{action_name}/{idx}=({dx},{dy})")
            else:
                if (dx, dy) != (hurt_dx, hurt_dy):
                    raise SystemExit(
                        f"Hurt frame {species}/{idx} compensation ({dx},{dy}) != action contract ({hurt_dx},{hurt_dy})"
                    )
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
    print(
        f"Wrote {args.output} (G3R6A, species={species}, variant={args.variant}, "
        f"hurtComp=({hurt_dx},{hurt_dy}))"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
