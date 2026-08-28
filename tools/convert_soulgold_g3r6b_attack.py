#!/usr/bin/env python3
"""Convert PMDCollab Attack to a lossless SoulGold 64x64 body frame.

PMD source action canvases may be taller than GBA's 64x64 battler OBJ even when
the visible sprite is small. G3R6B therefore distinguishes *source canvas size*
from *opaque pixel extent*.

A source pixel may fall outside the destination 64x64 canvas only when it is
transparent. Every opaque pixel must map inside the destination after aligning
the PMDCollab green body-center marker to the requested SoulGold battle anchor.
No visible pixel is cropped, scaled, resampled, or heuristically shifted.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

import convert_soulgold_g3r4 as g3r4
import pmd_gba_converter as base

CANVAS_W = 64
CANVAS_H = 64
SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"


def normalize_visible_pixels(frame: Image.Image, center: tuple[int,int], anchor: tuple[int,int]):
    dx = anchor[0] - center[0]
    dy = anchor[1] - center[1]
    out = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0,0,0,0))
    src = frame.load()
    dst = out.load()
    opaque_source = 0
    opaque_copied = 0
    transparent_outside = 0
    opaque_outside = []
    min_x=min_y=10**9
    max_x=max_y=-10**9

    for y in range(frame.height):
        for x in range(frame.width):
            r,g,b,a = src[x,y]
            tx=x+dx; ty=y+dy
            if a:
                opaque_source += 1
                min_x=min(min_x,tx); max_x=max(max_x,tx)
                min_y=min(min_y,ty); max_y=max(max_y,ty)
                if not (0 <= tx < CANVAS_W and 0 <= ty < CANVAS_H):
                    opaque_outside.append([x,y,tx,ty])
                    continue
                dst[tx,ty]=(r,g,b,a)
                opaque_copied += 1
            elif not (0 <= tx < CANVAS_W and 0 <= ty < CANVAS_H):
                transparent_outside += 1

    if opaque_outside:
        sample=opaque_outside[:8]
        raise ValueError(
            f"Opaque clipping forbidden: {len(opaque_outside)} visible pixels outside 64x64; sample={sample}"
        )
    if opaque_source != opaque_copied:
        raise ValueError(f"Visible pixel conservation failed: source={opaque_source}, copied={opaque_copied}")
    if opaque_source == 0:
        raise ValueError("Attack frame contains no opaque pixels")

    return out, {
        "paste_x": dx,
        "paste_y": dy,
        "opaque_source_pixels": opaque_source,
        "opaque_copied_pixels": opaque_copied,
        "opaque_destination_bbox": [min_x,min_y,max_x,max_y],
        "transparent_source_pixels_outside_destination": transparent_outside,
        "visible_pixel_conservation": True,
    }


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source",type=Path,required=True)
    ap.add_argument("--species",required=True)
    ap.add_argument("--national-dex",required=True)
    ap.add_argument("--direction",required=True,choices=base.DIRECTIONS)
    ap.add_argument("--anchor-x",type=int,required=True)
    ap.add_argument("--anchor-y",type=int,required=True)
    ap.add_argument("--source-revision",default=SPRITECOLLAB_REV)
    ap.add_argument("--source-repo-path",required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--host-asset-root",required=True)
    args=ap.parse_args()

    source=args.source.resolve()
    out=args.output.resolve()
    out.mkdir(parents=True,exist_ok=True)
    metas=g3r4.parse_anim_data_g3r4(source/"AnimData.xml")
    action=base.resolve_action("Attack",metas)
    anim=base._open_rgba(source/f"{action.source_action}-Anim.png")
    offsets=base._open_rgba(source/f"{action.source_action}-Offsets.png")
    anchor=(args.anchor_x,args.anchor_y)

    normalized=[]
    frame_records=[]
    for i,duration in enumerate(action.durations):
        frame=base.crop_direction_frame(anim,action,args.direction,i)
        off=base.crop_direction_frame(offsets,action,args.direction,i)
        center=base.body_center_from_offsets(off)
        canvas,audit=normalize_visible_pixels(frame,center,anchor)
        normalized.append(canvas)
        frame_records.append({
            "index":i,
            "duration":int(duration),
            "source_center_x":int(center[0]),
            "source_center_y":int(center[1]),
            "paste_x":audit["paste_x"],
            "paste_y":audit["paste_y"],
            "presentation_dx":0,
            "presentation_dy":0,
            "opaque_source_pixels":audit["opaque_source_pixels"],
            "opaque_copied_pixels":audit["opaque_copied_pixels"],
            "opaque_destination_bbox":audit["opaque_destination_bbox"],
            "transparent_source_pixels_outside_destination":audit["transparent_source_pixels_outside_destination"],
            "visible_pixel_conservation":True,
        })

    palette=base.quantized_palette(normalized)
    attack_dir=out/"attack"
    attack_dir.mkdir(exist_ok=True)
    for i,canvas in enumerate(normalized):
        indexed=base.to_indexed_gba(canvas,palette)
        indexed.save(attack_dir/f"frame_{i:02d}.png",optimize=False)
    base.write_jasc_palette(out/"palette.pal",palette)

    manifest={
        "format":"PMD_GBA_SOULGOLD_G3R6B_ATTACK_IR",
        "species":{"name":args.species,"national_dex":int(args.national_dex)},
        "source":{
            "revision":args.source_revision,
            "repo_path":args.source_repo_path,
            "action":"Attack",
        },
        "body_profile":{
            "anchor_target":{"x":anchor[0],"y":anchor[1]},
            "policy":"PMDCOLLAB_GREEN_BODY_CENTER_TRANSPARENT_OVERFLOW_TOLERANT",
        },
        "actions":{
            "Attack":{
                "name":"Attack",
                "source_action":action.source_action,
                "semantic_role":"move_body_action",
                "direction":args.direction,
                "source_frame_width":action.frame_width,
                "source_frame_height":action.frame_height,
                "source_canvas_exceeds_64": action.frame_width>64 or action.frame_height>64,
                "visible_pixels_fit_single_obj":True,
                "rush_frame":action.rush_frame,
                "hit_frame":action.hit_frame,
                "return_frame":action.return_frame,
                "frames":frame_records,
            }
        },
        "conversion":{
            "destination_canvas":[64,64],
            "cropped_visible_pixels":0,
            "scaled":False,
            "resampled":False,
            "transparent_source_overflow_allowed":True,
            "visible_pixel_conservation_required":True,
        },
        "host_asset_root":args.host_asset_root,
    }
    (out/"manifest.ir.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")

    print(f"G3R6B Attack {args.species}: source={action.frame_width}x{action.frame_height}, frames={action.frame_count}")
    print("markers",action.rush_frame,action.hit_frame,action.return_frame)
    print("opaque bboxes",[f["opaque_destination_bbox"] for f in frame_records])
    print("transparent overflow",[f["transparent_source_pixels_outside_destination"] for f in frame_records])
    print("visible pixel conservation PASS")
    return 0


if __name__=="__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr)
        raise
