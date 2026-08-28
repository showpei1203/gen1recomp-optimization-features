#!/usr/bin/env python3
"""Emit SoulGold G3R8 PMDCollab Sleep body descriptors."""
from __future__ import annotations
import argparse, json
from pathlib import Path

FORMAT="PMD_GBA_SOULGOLD_G3R8_SLEEP_IR"

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
    if ir.get("format")!=FORMAT: raise SystemExit(f"G3R8 emitter refuses IR without {FORMAT}")
    action=ir.get("actions",{}).get("Sleep")
    if not action: raise SystemExit("G3R8 Sleep IR missing Sleep")
    species=ir["species"]["name"]
    prefix=f"Pmd{sym(species)}{sym(args.variant.title())}Sleep"
    frames=action["frames"]
    lines=[
        "/* Auto-generated SoulGold G3R8 PMDCollab Sleep body descriptors. */",
        "/* Looping here is presentation metadata only; status ownership is not hooked in G3R8 asset gate. */",
        '#include "global.h"','#include "pmd_gba_runtime.h"',''
    ]
    for f in frames:
        i=int(f["index"])
        if int(f["opaque_source_pixels"])!=int(f["opaque_copied_pixels"]): raise SystemExit(f"Sleep visible pixel mismatch {species}/{i}")
        lines.append(f'const u32 g{prefix}Frame{i:02d}[] = INCBIN_U32("{args.asset_root.rstrip("/")}/sleep/frame_{i:02d}.4bpp.lz");')
    lines += ["",f"static const struct PmdGbaFrame s{prefix}Frames[] =","{"]
    for f in frames:
        i=int(f["index"])
        lines.append(f"    {{ .gfx = g{prefix}Frame{i:02d}, .duration = {int(f['duration'])}, .presentationX = 0, .presentationY = 0 }},")
    lines += ["};","",f"const struct PmdGbaAction g{prefix}Action =","{",f"    .frames = s{prefix}Frames,",f"    .frameCount = ARRAY_COUNT(s{prefix}Frames),","    .loop = TRUE,","};",""]
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text("\n".join(lines),encoding="utf-8")
    print(f"Wrote {args.output}: {species} Sleep frames={len(frames)} loop=TRUE")
    return 0

if __name__=="__main__": raise SystemExit(main())
