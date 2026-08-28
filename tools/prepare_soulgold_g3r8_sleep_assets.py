#!/usr/bin/env python3
"""Prepare G3R8 source-authoritative Sleep body/shadow assets on G3R7 staging.

Special-state Sleep is allowed to preserve a directionless PMDCollab source
view. Normal battle-facing direction is only used when the source action really
contains the 8-row directional layout.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path

import convert_soulgold_g3r4 as g3r4
import convert_soulgold_g3r5 as g3r5shadow
import convert_soulgold_g3r8_sleep as g3r8sleep
import pmd_gba_converter as base
import prepare_soulgold_g3r6a_assets as g3r6a

SPRITECOLLAB_REV="4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV="b5122bdf188943862c13abe4938e88b7bb3c5c4a"
ALL_ACTIONS=("Idle","Walk","Nod","Rotate","Hurt","Attack","Shoot","Sleep")
NON_SLEEP_ACTIONS=tuple(a for a in ALL_ACTIONS if a!="Sleep")
TARGETS=(
    {"species":"Cyndaquil","slug":"cyndaquil","dex":"155","spritecollab_id":"0155","variant":"player","direction":"UpRight"},
    {"species":"Marill","slug":"marill","dex":"183","spritecollab_id":"0183","variant":"opponent","direction":"DownLeft"},
)

def run(cmd:list[str])->None:
    print("+"," ".join(str(x) for x in cmd)); subprocess.run(cmd,check=True)

def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spritecollab",type=Path,required=True); ap.add_argument("--soulgold",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True); ap.add_argument("--framework-root",type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args(); framework=args.framework_root.resolve(); spritecollab=args.spritecollab.resolve(); soulgold=args.soulgold.resolve(); out=args.output.resolve()
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True); parent=out/"g3r7_parent"; staging=out/"staging"; work=out/"work"
    run([sys.executable,str(framework/"tools"/"prepare_soulgold_g3r7_shoot_assets.py"),"--framework-root",str(framework),"--spritecollab",str(spritecollab),"--soulgold",str(soulgold),"--output",str(parent)])
    shutil.copytree(parent/"staging",staging); work.mkdir()
    parent_summary=json.loads((parent/"G3R7_SHOOT_ASSET_SUMMARY.json").read_text(encoding="utf-8"))
    summary={
        "phase":"G3R8_SLEEP_SOURCE_ASSETS","parent":"G3R7_ATTACK_SHOOT_SOURCE_STACK",
        "soulgold_revision":SOULGOLD_REV,"spritecollab_revision":SPRITECOLLAB_REV,
        "special_state_view_policy":"SPECIAL_STATE_MAY_PRESERVE_DIRECTIONLESS_PMDCOLLAB_VIEW",
        "sleep_body_policy":"PMDCOLLAB_GREEN_BODY_CENTER_VISIBLE_PIXELS_100_PERCENT_CONSERVED",
        "sleep_shadow_policy":"FRAME_SYNCHRONOUS_AUTHENTIC_PMDCOLLAB_SLEEP_SHADOW_SAME_SOURCE_LAYOUT_AS_BODY",
        "sleep_runtime_policy":"NOT_HOOKED_ASSET_GATE_ONLY",
        "known_ambient_1px_defect":"DEFERRED_ROOT_CAUSE_UNRESOLVED","targets":{}
    }
    old_actions=g3r6a.ACTIONS; g3r6a.ACTIONS=ALL_ACTIONS
    try:
        for target in TARGETS:
            key=f"{target['species']}_{target['variant']}"; anchor=parent_summary["targets"][key]["battle_anchor"]
            species_dir=spritecollab/"sprite"/target["spritecollab_id"]; host_palette=soulgold/"graphics"/"pokemon"/target["slug"]/"normal.pal"
            sleep_dir=work/f"{target['slug']}_{target['variant']}_sleep"; asset_root=f"graphics/pmd/{target['slug']}/{target['variant']}"
            run([sys.executable,str(framework/"tools"/"convert_soulgold_g3r8_sleep.py"),"--source",str(species_dir),"--species",target["species"],"--national-dex",target["dex"],"--direction",target["direction"],"--anchor-x",str(anchor[0]),"--anchor-y",str(anchor[1]),"--source-revision",SPRITECOLLAB_REV,"--source-repo-path",f"sprite/{target['spritecollab_id']}","--output",str(sleep_dir),"--host-asset-root",asset_root])
            run([sys.executable,str(framework/"tools"/"pmd_gba_remap_host_palette.py"),"--frames-root",str(sleep_dir),"--host-palette",str(host_palette)])
            run([sys.executable,str(framework/"tools"/"emit_soulgold_g3r8_sleep_c.py"),"--ir",str(sleep_dir/"manifest.ir.json"),"--output",str(staging/"src"/f"pmd_{target['slug']}_{target['variant']}_sleep.c"),"--variant",target["variant"],"--asset-root",asset_root])
            dst=staging/"graphics"/"pmd"/target["slug"]/target["variant"]/"sleep"
            if dst.exists(): shutil.rmtree(dst)
            shutil.copytree(sleep_dir/"sleep",dst)
            combined_path=staging/"graphics"/"pmd"/target["slug"]/target["variant"]/"manifest.ir.json"
            combined=json.loads(combined_path.read_text(encoding="utf-8")); sleep_manifest=json.loads((sleep_dir/"manifest.ir.json").read_text(encoding="utf-8"))
            combined["actions"]["Sleep"]=sleep_manifest["actions"]["Sleep"]
            combined.setdefault("g3r8",{})["sleep_conversion"]=sleep_manifest["conversion"]
            combined["g3r8"]["special_state_view"]=sleep_manifest["special_state_view"]
            combined_path.write_text(json.dumps(combined,indent=2)+"\n",encoding="utf-8")

            # Existing actions keep their proven directional extraction. Sleep
            # is resolved independently because PMDCollab may author it as a
            # directionless single-row special-state action.
            shadow_size,shadow_records=g3r5shadow.source_shadow_records(species_dir,target["direction"],list(NON_SLEEP_ACTIONS))
            metas=g3r4.parse_anim_data_g3r4(species_dir/"AnimData.xml")
            sleep_meta=base.resolve_action("Sleep",metas)
            sleep_layout=g3r8sleep.resolve_sleep_layout(species_dir,sleep_meta,target["direction"])
            sleep_shadow_size,sleep_shadow=g3r8sleep.sleep_shadow_records(species_dir,sleep_meta,sleep_layout)
            if sleep_shadow_size != shadow_size:
                raise SystemExit(f"{key}: ShadowSize changed between normal and Sleep extraction")
            shadow_records["Sleep"]=sleep_shadow

            final_centers={}
            for action in ALL_ACTIONS:
                final_centers[action]=[]; frames=combined["actions"][action]["frames"]; records=shadow_records[action]
                if len(frames)!=len(records): raise SystemExit(f"{key}/{action} body-shadow mismatch")
                for f,r in zip(frames,records):
                    sx,sy=[int(v) for v in r["center"]]; final_centers[action].append([sx+int(f["paste_x"]),sy+int(f["paste_y"])])
            combined.setdefault("shadow",{})["shadow_size"]=shadow_size; combined["shadow"]["g3r8_policy"]="FRAME_SYNCHRONOUS_PMDCOLLAB_WITH_SPECIAL_STATE_LAYOUT"
            shadow_asset=g3r6a.emit_dynamic_shadow_c(staging/"src"/f"pmd_{target['slug']}_{target['variant']}_shadow.c",target,combined,shadow_records,final_centers)
            sleep=sleep_manifest["actions"]["Sleep"]
            if len(sleep["frames"])!=2 or [int(f["duration"]) for f in sleep["frames"]] != [30,35]: raise SystemExit(f"{key} pinned Sleep contract changed")
            if len(shadow_asset["actions"]["Sleep"])!=2: raise SystemExit(f"{key} Sleep shadow mismatch")
            if sleep["source_layout"]==g3r8sleep.DIRECTIONLESS and sleep["direction"] is not None:
                raise SystemExit(f"{key}: directionless Sleep must not invent a battle direction")
            summary["targets"][key]={
                "species":target["species"],"variant":target["variant"],"requested_battle_direction":target["direction"],"battle_anchor":anchor,
                "sleep_source_frame_size":[sleep["source_frame_width"],sleep["source_frame_height"]],"sleep_frame_count":2,"sleep_durations":[30,35],
                "sleep_source_layout":sleep["source_layout"],"sleep_source_row":sleep["source_row"],"sleep_applied_direction":sleep["direction"],
                "sleep_view_policy":sleep["view_policy"],"sleep_sheet_sizes":sleep_manifest["special_state_view"]["sheet_sizes"],
                "visible_pixel_conservation":all(bool(f["visible_pixel_conservation"]) for f in sleep["frames"]),
                "sleep_shadow_frames":shadow_asset["actions"]["Sleep"],"expanded_shadow_atlas_frame_count":shadow_asset["frame_count"],"expanded_shadow_atlas_bytes":shadow_asset["gfx_bytes"]
            }
    finally: g3r6a.ACTIONS=old_actions
    (out/"G3R8_SLEEP_ASSET_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    for k,r in summary["targets"].items(): print(k,"Sleep",r["sleep_source_frame_size"],r["sleep_durations"],r["sleep_source_layout"],"atlas",r["expanded_shadow_atlas_frame_count"])
    print("G3R8 Sleep source asset preparation PASS"); return 0

if __name__=="__main__": raise SystemExit(main())
