#!/usr/bin/env python3
"""Convert PMDCollab Sleep to a lossless SoulGold 64x64 body frame sequence.

G3R8 is an asset/metadata gate only. It does not yet hook SoulGold sleep status
lifecycle. Every visible PMD pixel is conserved and aligned using the authored
green body-center metadata at the accepted battle anchor.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

import convert_soulgold_g3r4 as g3r4
import convert_soulgold_g3r6b_attack as lossless
import pmd_gba_converter as base

SPRITECOLLAB_REV="4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"


def main()->int:
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

    source=args.source.resolve(); out=args.output.resolve(); out.mkdir(parents=True,exist_ok=True)
    metas=g3r4.parse_anim_data_g3r4(source/"AnimData.xml")
    action=base.resolve_action("Sleep",metas)
    anim=base._open_rgba(source/f"{action.source_action}-Anim.png")
    offsets=base._open_rgba(source/f"{action.source_action}-Offsets.png")
    anchor=(args.anchor_x,args.anchor_y)
    normalized=[]; records=[]
    for i,duration in enumerate(action.durations):
        frame=base.crop_direction_frame(anim,action,args.direction,i)
        off=base.crop_direction_frame(offsets,action,args.direction,i)
        center=base.body_center_from_offsets(off)
        canvas,audit=lossless.normalize_visible_pixels(frame,center,anchor)
        normalized.append(canvas)
        records.append({
            "index":i,"duration":int(duration),
            "source_center_x":int(center[0]),"source_center_y":int(center[1]),
            "paste_x":audit["paste_x"],"paste_y":audit["paste_y"],
            "presentation_dx":0,"presentation_dy":0,
            "opaque_source_pixels":audit["opaque_source_pixels"],
            "opaque_copied_pixels":audit["opaque_copied_pixels"],
            "opaque_destination_bbox":audit["opaque_destination_bbox"],
            "transparent_source_pixels_outside_destination":audit["transparent_source_pixels_outside_destination"],
            "visible_pixel_conservation":True,
        })

    palette=base.quantized_palette(normalized)
    sleep_dir=out/"sleep"; sleep_dir.mkdir(exist_ok=True)
    for i,canvas in enumerate(normalized):
        base.to_indexed_gba(canvas,palette).save(sleep_dir/f"frame_{i:02d}.png",optimize=False)
    base.write_jasc_palette(out/"palette.pal",palette)
    manifest={
        "format":"PMD_GBA_SOULGOLD_G3R8_SLEEP_IR",
        "species":{"name":args.species,"national_dex":int(args.national_dex)},
        "source":{"revision":args.source_revision,"repo_path":args.source_repo_path,"action":"Sleep"},
        "body_profile":{"anchor_target":{"x":anchor[0],"y":anchor[1]},"policy":"PMDCOLLAB_GREEN_BODY_CENTER_VISIBLE_PIXELS_100_PERCENT_CONSERVED"},
        "actions":{"Sleep":{
            "name":"Sleep","source_action":action.source_action,"semantic_role":"persistent_sleep_status_body_candidate",
            "direction":args.direction,"source_frame_width":action.frame_width,"source_frame_height":action.frame_height,
            "visible_pixels_fit_single_obj":True,"rush_frame":action.rush_frame,"hit_frame":action.hit_frame,"return_frame":action.return_frame,
            "loop_candidate":True,"frames":records,
        }},
        "conversion":{"destination_canvas":[64,64],"cropped_visible_pixels":0,"scaled":False,"resampled":False,"visible_pixel_conservation_required":True},
        "host_asset_root":args.host_asset_root,
    }
    (out/"manifest.ir.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"G3R8 Sleep {args.species}: {action.frame_width}x{action.frame_height}, frames={action.frame_count}, durations={list(action.durations)}")
    print("visible pixel conservation PASS")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise
