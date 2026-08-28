#!/usr/bin/env python3
"""Audit PMDCollab special-state source-view layouts per action.

G3R8 proved that Sleep is directionless even though nearby special-state actions
are not necessarily directionless. G3R9 turns that observation into a reusable
source contract: every special-state action resolves its own Anim / Offsets /
Shadow geometry from the pinned PMDCollab source. No category-wide 45-degree or
directionless assumption is allowed.

This stage is intentionally source-audit only. It does not hook EventSleep or
Wake into SoulGold runtime choreography.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import convert_soulgold_g3r4 as g3r4
import convert_soulgold_g3r8_sleep as layout
import pmd_gba_converter as base

SPRITECOLLAB_REV="4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
ACTIONS=("Sleep","EventSleep","Wake")
TARGETS=(
    {"species":"Cyndaquil","id":"0155","direction":"UpRight"},
    {"species":"Marill","id":"0183","direction":"DownLeft"},
)


def main()->int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spritecollab",type=Path,required=True)
    ap.add_argument("--output",type=Path,required=True)
    args=ap.parse_args()
    root=args.spritecollab.resolve(); out=args.output.resolve(); out.parent.mkdir(parents=True,exist_ok=True)

    summary={
        "phase":"G3R9_SPECIAL_STATE_SOURCE_VIEW_AUDIT",
        "spritecollab_revision":SPRITECOLLAB_REV,
        "policy":"RESOLVE_VIEW_PER_ACTION_FROM_ANIM_OFFSETS_SHADOW_GEOMETRY",
        "runtime_policy":"SOURCE_AUDIT_ONLY_NO_EVENT_SLEEP_OR_WAKE_HOOKS",
        "actions":list(ACTIONS),
        "targets":{},
    }

    for target in TARGETS:
        species_dir=root/"sprite"/target["id"]
        metas=g3r4.parse_anim_data_g3r4(species_dir/"AnimData.xml")
        species_rec={"requested_battle_direction":target["direction"],"actions":{}}
        for action_name in ACTIONS:
            action=base.resolve_action(action_name,metas)
            resolved=layout.resolve_sleep_layout(species_dir,action,target["direction"])
            shadow_size,shadow_records=layout.sleep_shadow_records(species_dir,action,resolved)
            rec={
                "source_action":action.source_action,
                "frame_size":[action.frame_width,action.frame_height],
                "frame_count":len(action.durations),
                "durations":[int(x) for x in action.durations],
                "source_layout":resolved["layout"],
                "source_row":int(resolved["row"]),
                "requested_battle_direction":target["direction"],
                "applied_source_direction":resolved["applied_source_direction"],
                "view_policy":resolved["view_policy"],
                "sheet_sizes":resolved["sheet_sizes"],
                "shadow_size":shadow_size,
                "shadow_frame_count":len(shadow_records),
            }
            if rec["shadow_frame_count"] != rec["frame_count"]:
                raise SystemExit(f"{target['species']}/{action_name}: body-shadow frame mismatch")
            species_rec["actions"][action_name]=rec
            print(target["species"],action_name,rec["frame_size"],rec["frame_count"],rec["source_layout"],rec["applied_source_direction"])
        summary["targets"][target["species"]]=species_rec

    for species,record in summary["targets"].items():
        sleep=record["actions"]["Sleep"]
        event=record["actions"]["EventSleep"]
        wake=record["actions"]["Wake"]
        if sleep["source_layout"] != layout.DIRECTIONLESS or sleep["applied_source_direction"] is not None:
            raise SystemExit(f"{species}: pinned Sleep is expected to remain source-directionless")
        if event["source_layout"] != layout.DIRECTIONAL or event["applied_source_direction"] != record["requested_battle_direction"]:
            raise SystemExit(f"{species}: pinned EventSleep is expected to be directional")
        if wake["source_layout"] != layout.DIRECTIONAL or wake["applied_source_direction"] != record["requested_battle_direction"]:
            raise SystemExit(f"{species}: pinned Wake is expected to be directional")

    out.write_text(json.dumps(summary,indent=2)+"\n",encoding="utf-8")
    print("G3R9 special-state per-action source-view audit PASS")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
