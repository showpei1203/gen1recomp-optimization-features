#!/usr/bin/env python3
"""Emit SoulGold G3 grounded Rich Ambient descriptors for one PMD species/side."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

ACTIONS = ("Idle", "Walk", "Nod", "Rotate")


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
    species = ir["species"]["name"]
    species_sym = sym(species)
    variant_sym = sym(args.variant.title())

    missing = [name for name in ACTIONS if name not in ir["actions"]]
    if missing:
        raise SystemExit(f"IR missing required G3R3 grounded actions: {missing}")

    lines = [
        "/* Auto-generated SoulGold G3R3 grounded Rich Ambient descriptors. */",
        "/* PMD body+shadow are atomic; grounded frames use PMD shadow-origin normalization. */",
        "#include \"global.h\"",
        "#include \"pmd_gba_runtime.h\"",
        "",
    ]
    frame_symbols: dict[tuple[str, int], str] = {}

    for action_name in ACTIONS:
        rec = ir["actions"][action_name]
        prefix = f"Pmd{species_sym}{variant_sym}{sym(action_name)}"
        for frame in rec["frames"]:
            idx = int(frame["index"])
            symbol = f"g{prefix}Frame{idx:02d}"
            rel = f"{args.asset_root.rstrip('/')}/{action_name.lower()}/frame_{idx:02d}.4bpp.lz"
            lines.append(f'const u32 {symbol}[] = INCBIN_U32("{rel}");')
            frame_symbols[(action_name, idx)] = symbol
        lines.append("")

        lines.append(f"static const struct PmdGbaFrame s{prefix}Frames[] =")
        lines.append("{")
        for frame in rec["frames"]:
            idx = int(frame["index"])
            duration = int(frame["duration"])
            dx = int(frame.get("presentation_dx", 0))
            dy = int(frame.get("presentation_dy", 0))
            if dx != 0 or dy != 0:
                raise SystemExit(
                    f"Grounded G3R3 frame must not use runtime sprite offsets: {species}/{args.variant}/{action_name}/{idx} = ({dx},{dy})"
                )
            lines.append(
                f"    {{ .gfx = {frame_symbols[(action_name, idx)]}, .duration = {duration}, "
                f".presentationX = 0, .presentationY = 0 }},"
            )
        lines.append("};")
        lines.append("")
        lines.append(f"const struct PmdGbaAction g{prefix}Action =")
        lines.append("{")
        lines.append(f"    .frames = s{prefix}Frames,")
        lines.append(f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),")
        lines.append("    .loop = FALSE,")
        lines.append("};")
        lines.append("")

    home_prefix = f"Pmd{species_sym}{variant_sym}Home"
    idle0 = frame_symbols[("Idle", 0)]
    lines.extend([
        f"static const struct PmdGbaFrame s{home_prefix}Frames[] =",
        "{",
        f"    {{ .gfx = {idle0}, .duration = 1, .presentationX = 0, .presentationY = 0 }},",
        "};",
        "",
        f"const struct PmdGbaAction g{home_prefix}Action =",
        "{",
        f"    .frames = s{home_prefix}Frames,",
        f"    .frameCount = ARRAY_COUNT(s{home_prefix}Frames),",
        "    .loop = TRUE,",
        "};",
        "",
    ])

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output} (G3R3 grounded, species={species}, variant={args.variant})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
