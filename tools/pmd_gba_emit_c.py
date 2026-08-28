#!/usr/bin/env python3
"""Emit GBA C frame/action descriptors from portable PMD Animation IR.

This is intentionally separate from image conversion. A host can consume the
same IR while choosing its own build paths and naming conventions.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path


def sym(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ir", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--variant", choices=["player", "opponent"], required=True)
    ap.add_argument("--asset-root", required=True, help="host path prefix, e.g. graphics/pmd/cyndaquil/player")
    ap.add_argument("--actions", default="", help="comma-separated subset; empty emits every IR action")
    args = ap.parse_args()

    ir = json.loads(args.ir.read_text(encoding="utf-8"))
    species = ir["species"]["name"]
    species_sym = sym(species)
    variant_sym = sym(args.variant.title())
    wanted = {x.strip() for x in args.actions.split(",") if x.strip()}

    action_items = []
    for name, rec in ir["actions"].items():
        if wanted and name not in wanted:
            continue
        if not rec.get("frames"):
            continue
        action_items.append((name, rec))
    if not action_items:
        raise SystemExit("No actions selected from IR")

    lines = [
        "/* Auto-generated from portable PMD Animation IR. */",
        "#include \"global.h\"",
        "#include \"pmd_gba_runtime.h\"",
        "",
    ]

    for action_name, rec in action_items:
        action_sym = sym(action_name)
        prefix = f"Pmd{species_sym}{variant_sym}{action_sym}"
        for frame in rec["frames"]:
            idx = int(frame["index"])
            rel = f"{args.asset_root.rstrip('/')}/{action_name.lower()}/frame_{idx:02d}.4bpp.lz"
            lines.append(f'const u32 g{prefix}Frame{idx:02d}[] = INCBIN_U32("{rel}");')
        lines.append("")
        lines.append(f"static const struct PmdGbaFrame s{prefix}Frames[] =")
        lines.append("{")
        for frame in rec["frames"]:
            idx = int(frame["index"])
            duration = int(frame["duration"])
            dx = int(frame.get("presentation_dx", 0))
            dy = int(frame.get("presentation_dy", 0))
            lines.append(
                f"    {{ .gfx = g{prefix}Frame{idx:02d}, .duration = {duration}, "
                f".presentationX = {dx}, .presentationY = {dy} }},"
            )
        lines.append("};")
        lines.append("")
        lines.append(f"const struct PmdGbaAction g{prefix}Action =")
        lines.append("{")
        lines.append(f"    .frames = s{prefix}Frames,")
        lines.append(f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),")
        lines.append("    .loop = TRUE,")
        lines.append("};")
        lines.append("")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text("\n".join(lines), encoding="utf-8")
    print(f"Wrote {args.output} ({len(action_items)} actions, variant={args.variant})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
