#!/usr/bin/env python3
"""Emit the G3R6B PMD Attack body action descriptor."""
from __future__ import annotations
import argparse, json
from pathlib import Path


def sym(text:str)->str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--ir",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--variant",choices=["player","opponent"],required=True)
    ap.add_argument("--asset-root",required=True)
    args=ap.parse_args()
    ir=json.loads(args.ir.read_text(encoding="utf-8"))
    if ir.get("format")!="PMD_GBA_SOULGOLD_G3R6B_ATTACK_IR":
        raise SystemExit("Refusing non-G3R6B Attack IR")
    rec=ir["actions"]["Attack"]
    if not rec.get("visible_pixels_fit_single_obj"):
        raise SystemExit("Attack IR is not single-OBJ visible-pixel safe")
    species=ir["species"]["name"]
    prefix=f"Pmd{sym(species)}{sym(args.variant.title())}Attack"
    lines=[
        "/* Auto-generated G3R6B transparent-overflow PMDCollab Attack. */",
        "/* Source canvas may exceed 64px; every opaque pixel is conserved in 64x64. */",
        '#include "global.h"',
        '#include "pmd_gba_runtime.h"',
        "",
    ]
    for frame in rec["frames"]:
        i=int(frame["index"])
        lines.append(f'const u32 g{prefix}Frame{i:02d}[] = INCBIN_U32("{args.asset_root.rstrip("/")}/attack/frame_{i:02d}.4bpp.lz");')
    lines += ["",f"static const struct PmdGbaFrame s{prefix}Frames[] =","{"]
    for frame in rec["frames"]:
        i=int(frame["index"])
        if not frame.get("visible_pixel_conservation") or int(frame["opaque_source_pixels"])!=int(frame["opaque_copied_pixels"]):
            raise SystemExit(f"{species} Attack frame {i} lost visible pixels")
        if int(frame.get("presentation_dx",0)) or int(frame.get("presentation_dy",0)):
            raise SystemExit(f"{species} Attack must not overwrite native move x2/y2")
        lines.append(
            f"    {{ .gfx = g{prefix}Frame{i:02d}, .duration = {int(frame['duration'])}, .presentationX = 0, .presentationY = 0 }},"
        )
    lines += [
        "};","",
        f"const struct PmdGbaAction g{prefix}Action =","{",
        f"    .frames = s{prefix}Frames,",
        f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),",
        "    .loop = FALSE,",
        "};","",
        f"const u8 g{prefix}RushFrame = {int(rec['rush_frame'])};",
        f"const u8 g{prefix}HitFrame = {int(rec['hit_frame'])};",
        f"const u8 g{prefix}ReturnFrame = {int(rec['return_frame'])};",
        "",
    ]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text("\n".join(lines),encoding="utf-8")
    print("Wrote",args.output,"frames",len(rec["frames"]))
    return 0

if __name__=="__main__":
    raise SystemExit(main())
