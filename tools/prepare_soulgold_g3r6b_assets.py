#!/usr/bin/env python3
"""Prepare G3R6B assets by preserving G3R6A and adding lossless PMD Attack.

Ambient, the known unresolved Cyndaquil 1px issue, and Hurt are inherited from
G3R6A without reinterpretation. Attack is generated separately with the
transparent-overflow converter: the PMD source canvas may exceed 64px, but every
visible pixel must fit after green body-center alignment to the accepted battle
anchor.

The existing per-species shadow atlas is regenerated to append authentic
Attack-Shadow.png frames. This keeps one tile tag per PMD species and lets the
proven dynamic-shadow renderer select Attack frames using the same action/frame
index contract as ambient and Hurt.
"""
from __future__ import annotations
import argparse, json, shutil, subprocess, sys
from pathlib import Path

import convert_soulgold_g3r5 as g3r5shadow
import prepare_soulgold_g3r6a_assets as g3r6a

SPRITECOLLAB_REV="4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV="b5122bdf188943862c13abe4938e88b7bb3c5c4a"
ALL_ACTIONS=("Idle","Walk","Nod","Rotate","Hurt","Attack")
TARGETS=(
    {"species":"Cyndaquil","slug":"cyndaquil","dex":"155","spritecollab_id":"0155","variant":"player","direction":"UpRight"},
    {"species":"Marill","slug":"marill","dex":"183","spritecollab_id":"0183","variant":"opponent","direction":"DownLeft"},
)


def run(cmd:list[str])->None:
    print("+"," ".join(str(x) for x in cmd))
    subprocess.run(cmd,check=True)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spritecollab",type=Path,required=True)
    ap.add_argument("--soulgold",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    ap.add_argument("--framework-root",type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args()
    framework=args.framework_root.resolve(); spritecollab=args.spritecollab.resolve(); soulgold=args.soulgold.resolve(); out=args.output.resolve()
    if out.exists(): shutil.rmtree(out)
    out.mkdir(parents=True)
    parent=out/"g3r6a_parent"
    staging=out/"staging"
    work=out/"work"

    run([sys.executable,str(framework/"tools"/"prepare_soulgold_g3r6a_assets.py"),
         "--framework-root",str(framework),"--spritecollab",str(spritecollab),
         "--soulgold",str(soulgold),"--output",str(parent)])
    shutil.copytree(parent/"staging",staging)
    work.mkdir()
    parent_summary=json.loads((parent/"G3R6A_ASSET_SUMMARY.json").read_text(encoding="utf-8"))

    summary={
        "phase":"G3R6B_ATTACK_BODY_ASSETS",
        "parent":"G3R6A_HURT_BUILD_PASS_RUNTIME_PENDING",
        "soulgold_revision":SOULGOLD_REV,
        "spritecollab_revision":SPRITECOLLAB_REV,
        "ambient_hurt_policy":"BYTE_PIPELINE_INHERITED_FROM_G3R6A",
        "known_ambient_1px_defect":"DEFERRED_ROOT_CAUSE_UNRESOLVED",
        "attack_body_policy":"GREEN_BODY_CENTER_PLUS_TRANSPARENT_OVERFLOW_TOLERANCE_VISIBLE_PIXELS_100_PERCENT_CONSERVED",
        "attack_runtime_spatial_policy":"FRAME_PIXELS_ONLY_NATIVE_MOVE_X2Y2_REMAINS_OWNER",
        "attack_shadow_policy":"AUTHENTIC_FRAME_SYNCHRONOUS_PMDCOLLAB_ATTACK_SHADOW_APPENDED_TO_SPECIES_ATLAS",
        "targets":{},
    }

    old_actions=g3r6a.ACTIONS
    g3r6a.ACTIONS=ALL_ACTIONS
    try:
        for target in TARGETS:
            key=f"{target['species']}_{target['variant']}"
            parent_rec=parent_summary["targets"][key]
            anchor=parent_rec["resolved_ambient_body_anchor"]
            species_dir=spritecollab/"sprite"/target["spritecollab_id"]
            host_palette=soulgold/"graphics"/"pokemon"/target["slug"]/"normal.pal"
            attack_dir=work/f"{target['slug']}_{target['variant']}_attack"
            asset_root=f"graphics/pmd/{target['slug']}/{target['variant']}"

            run([sys.executable,str(framework/"tools"/"convert_soulgold_g3r6b_attack.py"),
                 "--source",str(species_dir),"--species",target["species"],"--national-dex",target["dex"],
                 "--direction",target["direction"],"--anchor-x",str(anchor[0]),"--anchor-y",str(anchor[1]),
                 "--source-revision",SPRITECOLLAB_REV,"--source-repo-path",f"sprite/{target['spritecollab_id']}",
                 "--output",str(attack_dir),"--host-asset-root",asset_root])
            run([sys.executable,str(framework/"tools"/"pmd_gba_remap_host_palette.py"),
                 "--frames-root",str(attack_dir),"--host-palette",str(host_palette)])
            run([sys.executable,str(framework/"tools"/"emit_soulgold_g3r6b_attack_c.py"),
                 "--ir",str(attack_dir/"manifest.ir.json"),
                 "--output",str(staging/"src"/f"pmd_{target['slug']}_{target['variant']}_attack.c"),
                 "--variant",target["variant"],"--asset-root",asset_root])

            dst_attack=staging/"graphics"/"pmd"/target["slug"]/target["variant"]/"attack"
            if dst_attack.exists(): shutil.rmtree(dst_attack)
            shutil.copytree(attack_dir/"attack",dst_attack)

            combined_manifest_path=staging/"graphics"/"pmd"/target["slug"]/target["variant"]/"manifest.ir.json"
            combined=json.loads(combined_manifest_path.read_text(encoding="utf-8"))
            attack_manifest=json.loads((attack_dir/"manifest.ir.json").read_text(encoding="utf-8"))
            combined["actions"]["Attack"]=attack_manifest["actions"]["Attack"]
            combined.setdefault("g3r6b",{})["attack_conversion"]=attack_manifest["conversion"]
            combined["g3r6b"]["attack_body_profile"]=attack_manifest["body_profile"]
            combined_manifest_path.write_text(json.dumps(combined,indent=2)+"\n",encoding="utf-8")

            shadow_size,shadow_records=g3r5shadow.source_shadow_records(species_dir,target["direction"],list(ALL_ACTIONS))
            final_centers={}
            for action in ALL_ACTIONS:
                final_centers[action]=[]
                frames=combined["actions"][action]["frames"]
                records=shadow_records[action]
                if len(frames)!=len(records):
                    raise SystemExit(f"{key}/{action} body-shadow frame mismatch {len(frames)} vs {len(records)}")
                for frame,rec in zip(frames,records):
                    sx,sy=[int(v) for v in rec["center"]]
                    final_centers[action].append([sx+int(frame["paste_x"]),sy+int(frame["paste_y"])])
            combined.setdefault("shadow",{})["shadow_size"]=shadow_size
            combined["shadow"]["g3r6b_policy"]="FRAME_SYNCHRONOUS_PMDCOLLAB_AMBIENT_HURT_ATTACK"
            shadow_asset=g3r6a.emit_dynamic_shadow_c(
                staging/"src"/f"pmd_{target['slug']}_{target['variant']}_shadow.c",
                target,combined,shadow_records,final_centers)

            attack=attack_manifest["actions"]["Attack"]
            if any(not f["visible_pixel_conservation"] for f in attack["frames"]):
                raise SystemExit(f"{key}: visible pixel conservation failed")
            if any(int(f["opaque_source_pixels"])!=int(f["opaque_copied_pixels"]) for f in attack["frames"]):
                raise SystemExit(f"{key}: Attack copied pixel count mismatch")
            if [attack["rush_frame"],attack["hit_frame"],attack["return_frame"]] != [1,3,6]:
                raise SystemExit(f"{key}: pinned Attack markers changed")
            if len(shadow_asset["actions"]["Attack"]) != len(attack["frames"]):
                raise SystemExit(f"{key}: Attack shadow timeline mismatch")

            summary["targets"][key]={
                "species":target["species"],"variant":target["variant"],"direction":target["direction"],
                "battle_anchor":anchor,
                "attack_source_frame_size":[attack["source_frame_width"],attack["source_frame_height"]],
                "attack_frame_count":len(attack["frames"]),
                "attack_durations":[int(f["duration"]) for f in attack["frames"]],
                "attack_markers":{"rush":attack["rush_frame"],"hit":attack["hit_frame"],"return":attack["return_frame"]},
                "opaque_destination_bboxes":[f["opaque_destination_bbox"] for f in attack["frames"]],
                "opaque_pixels":[int(f["opaque_source_pixels"]) for f in attack["frames"]],
                "transparent_overflow_pixels":[int(f["transparent_source_pixels_outside_destination"]) for f in attack["frames"]],
                "visible_pixel_conservation":True,
                "attack_shadow_frames":shadow_asset["actions"]["Attack"],
                "expanded_shadow_atlas_frame_count":shadow_asset["frame_count"],
                "expanded_shadow_atlas_bytes":shadow_asset["gfx_bytes"],
            }
    finally:
        g3r6a.ACTIONS=old_actions

    (out/"G3R6B_ASSET_SUMMARY.json").write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    for key,rec in summary["targets"].items():
        print(key, "Attack source",rec["attack_source_frame_size"],"frames",rec["attack_frame_count"],"markers",rec["attack_markers"])
        print(" opaque bboxes",rec["opaque_destination_bboxes"])
    print("G3R6B Attack asset preparation PASS")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
