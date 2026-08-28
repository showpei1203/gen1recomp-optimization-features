#!/usr/bin/env python3
"""Convert PMDCollab Sleep to a lossless SoulGold 64x64 body sequence.

Special-state actions are not forced into the normal 45-degree battle-facing
contract. PMDCollab Sleep may be an authored directionless single-row sheet.
When that source layout is present, G3R8 preserves it verbatim instead of
inventing an UpRight/DownLeft row. Directional 8-row Sleep remains supported
when the source actually provides it.

G3R8 is still an asset/metadata gate only. Every visible PMD pixel is conserved
and aligned by the authored green body-center metadata at the accepted SoulGold
battle anchor. Shadow extraction uses the exact same resolved layout.
"""
from __future__ import annotations
import argparse, json, sys
from pathlib import Path

from PIL import Image

import convert_soulgold_g3r4 as g3r4
import convert_soulgold_g3r5 as g3r5shadow
import convert_soulgold_g3r6b_attack as lossless
import pmd_gba_converter as base

SPRITECOLLAB_REV="4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
DIRECTIONLESS="DIRECTIONLESS_SINGLE_ROW"
DIRECTIONAL="DIRECTIONAL_8_ROWS"


def _sheet_geometry_ok(sheet: Image.Image, action) -> tuple[bool,bool]:
    required_w=action.frame_width * len(action.durations)
    single=sheet.width >= required_w and sheet.height >= action.frame_height and sheet.height < action.frame_height * len(base.DIRECTIONS)
    directional=sheet.width >= required_w and sheet.height >= action.frame_height * len(base.DIRECTIONS)
    return single,directional


def resolve_sleep_layout(source: Path, action, requested_direction: str) -> dict[str,object]:
    if requested_direction not in base.DIRECTIONS:
        raise ValueError(f"Unsupported PMD direction: {requested_direction}")
    sheets={}
    for suffix in ("Anim","Offsets","Shadow"):
        path=source/f"{action.source_action}-{suffix}.png"
        if not path.is_file():
            raise ValueError(f"Missing PMD Sleep source authority: {path}")
        sheets[suffix]=Image.open(path).convert("RGBA")

    checks={name:_sheet_geometry_ok(sheet,action) for name,sheet in sheets.items()}
    if all(single and not directional for single,directional in checks.values()):
        layout=DIRECTIONLESS; row=0; applied_direction=None
    elif all(directional for single,directional in checks.values()):
        layout=DIRECTIONAL; row=base.DIRECTIONS.index(requested_direction); applied_direction=requested_direction
    else:
        dims={name:list(sheet.size) for name,sheet in sheets.items()}
        raise ValueError(
            f"Sleep Anim/Offsets/Shadow disagree on layout or geometry: {dims}; "
            f"frame={action.frame_width}x{action.frame_height}, frames={len(action.durations)}"
        )

    return {
        "layout":layout,
        "row":row,
        "requested_battle_direction":requested_direction,
        "applied_source_direction":applied_direction,
        "view_policy":"PRESERVE_PMDCOLLAB_SPECIAL_STATE_SOURCE_VIEW" if layout==DIRECTIONLESS else "USE_REQUESTED_BATTLE_DIRECTION_WHEN_SOURCE_IS_DIRECTIONAL",
        "sheet_sizes":{name:list(sheet.size) for name,sheet in sheets.items()},
    }


def crop_resolved_frame(sheet: Image.Image, action, layout: dict[str,object], frame_index: int) -> Image.Image:
    row=int(layout["row"]); w=action.frame_width; h=action.frame_height
    return sheet.crop((frame_index*w,row*h,(frame_index+1)*w,(row+1)*h))


def sleep_shadow_records(source: Path, action, layout: dict[str,object]) -> tuple[int,list[dict[str,object]]]:
    shadow_size=g3r5shadow.parse_shadow_size(source/"AnimData.xml")
    sheet=Image.open(source/f"{action.source_action}-Shadow.png").convert("RGBA")
    records=[]
    for i in range(len(action.durations)):
        rec=g3r5shadow.shadow_frame_record(crop_resolved_frame(sheet,action,layout,i),shadow_size)
        rec["frame_index"]=i
        rec["source_layout"]=layout["layout"]
        rec["source_row"]=int(layout["row"])
        records.append(rec)
    return shadow_size,records


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
    layout=resolve_sleep_layout(source,action,args.direction)
    anchor=(args.anchor_x,args.anchor_y)
    normalized=[]; records=[]
    for i,duration in enumerate(action.durations):
        frame=crop_resolved_frame(anim,action,layout,i)
        off=crop_resolved_frame(offsets,action,layout,i)
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
        "special_state_view":layout,
        "actions":{"Sleep":{
            "name":"Sleep","source_action":action.source_action,"semantic_role":"persistent_sleep_status_body_candidate",
            "direction":layout["applied_source_direction"],"requested_battle_direction":args.direction,
            "source_layout":layout["layout"],"source_row":layout["row"],"view_policy":layout["view_policy"],
            "source_frame_width":action.frame_width,"source_frame_height":action.frame_height,
            "visible_pixels_fit_single_obj":True,"rush_frame":action.rush_frame,"hit_frame":action.hit_frame,"return_frame":action.return_frame,
            "loop_candidate":True,"frames":records,
        }},
        "conversion":{"destination_canvas":[64,64],"cropped_visible_pixels":0,"scaled":False,"resampled":False,"visible_pixel_conservation_required":True},
        "host_asset_root":args.host_asset_root,
    }
    (out/"manifest.ir.json").write_text(json.dumps(manifest,indent=2)+"\n",encoding="utf-8")
    print(f"G3R8 Sleep {args.species}: {action.frame_width}x{action.frame_height}, frames={action.frame_count}, durations={list(action.durations)}")
    print("layout",layout["layout"],"requested",args.direction,"applied",layout["applied_source_direction"],"sheets",layout["sheet_sizes"])
    print("visible pixel conservation PASS")
    return 0

if __name__=="__main__":
    try: raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}",file=sys.stderr); raise
