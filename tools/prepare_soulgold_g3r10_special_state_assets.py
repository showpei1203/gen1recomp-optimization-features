#!/usr/bin/env python3
"""Prepare G3R10 Sleep-entry and Wake source assets on the G3R8C stack.

G3R10 keeps the already-integrated persistent Sleep action, then adds two
transition actions from the same pinned PMDCollab authority:
- EventSleep: eligible for runtime sleep-entry presentation in this phase.
- Wake: body/shadow/source-view ready, but runtime choreography remains deferred
  until it can be synchronized with SoulGold's native wake/move script without
  delaying or replaying a move.

Every special-state action resolves its own source layout. No category-wide
45-degree assumption is allowed.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import convert_soulgold_g3r4 as g3r4
import convert_soulgold_g3r5 as g3r5shadow
import convert_soulgold_g3r8_sleep as view
import pmd_gba_converter as base
import prepare_soulgold_g3r6a_assets as g3r6a

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
NORMAL_ACTIONS = ("Idle", "Walk", "Nod", "Rotate", "Hurt", "Attack", "Shoot")
SPECIAL_ACTIONS = ("Sleep", "EventSleep", "Wake")
GENERATED_ACTIONS = ("EventSleep", "Wake")
ALL_ACTIONS = NORMAL_ACTIONS + SPECIAL_ACTIONS
FOLDERS = {"EventSleep": "event_sleep", "Wake": "wake"}
TARGETS = (
    {"species": "Cyndaquil", "slug": "cyndaquil", "dex": "155", "spritecollab_id": "0155", "variant": "player", "direction": "UpRight"},
    {"species": "Marill", "slug": "marill", "dex": "183", "spritecollab_id": "0183", "variant": "opponent", "direction": "DownLeft"},
)


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    framework = args.framework_root.resolve()
    spritecollab = args.spritecollab.resolve()
    soulgold = args.soulgold.resolve()
    out = args.output.resolve()
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)
    parent = out / "g3r8_parent"
    staging = out / "staging"
    work = out / "work"

    run([
        sys.executable, str(framework / "tools" / "prepare_soulgold_g3r8_sleep_assets.py"),
        "--framework-root", str(framework),
        "--spritecollab", str(spritecollab),
        "--soulgold", str(soulgold),
        "--output", str(parent),
    ])
    shutil.copytree(parent / "staging", staging)
    work.mkdir()
    parent_summary = json.loads((parent / "G3R8_SLEEP_ASSET_SUMMARY.json").read_text(encoding="utf-8"))

    summary = {
        "phase": "G3R10_SLEEP_ENTRY_TRANSITION_ASSETS",
        "parent": "G3R8C_PERSISTENT_SLEEP_PLUS_G3R9_PER_ACTION_VIEW_AUTHORITY",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "view_policy": "RESOLVE_SPECIAL_STATE_VIEW_PER_ACTION_FROM_ANIM_OFFSETS_SHADOW_GEOMETRY",
        "event_sleep_runtime_policy": "SOURCE_READY_FOR_PERSISTENT_GATE_SLEEP_ENTRY_TRANSITION",
        "wake_runtime_policy": "SOURCE_READY_RUNTIME_DEFERRED_NATIVE_WAKE_MOVE_SYNC_REQUIRED",
        "combat_logic": "UNCHANGED_SOULGOLD_NATIVE",
        "known_ambient_1px_defect": "DEFERRED_ROOT_CAUSE_UNRESOLVED",
        "targets": {},
    }

    old_actions = g3r6a.ACTIONS
    g3r6a.ACTIONS = ALL_ACTIONS
    try:
        for target in TARGETS:
            key = f"{target['species']}_{target['variant']}"
            anchor = [int(v) for v in parent_summary["targets"][key]["battle_anchor"]]
            species_dir = spritecollab / "sprite" / target["spritecollab_id"]
            host_palette = soulgold / "graphics" / "pokemon" / target["slug"] / "normal.pal"
            asset_root = f"graphics/pmd/{target['slug']}/{target['variant']}"
            combined_path = staging / "graphics" / "pmd" / target["slug"] / target["variant"] / "manifest.ir.json"
            combined = json.loads(combined_path.read_text(encoding="utf-8"))
            generated = {}

            for action_name in GENERATED_ACTIONS:
                action_work = work / f"{target['slug']}_{target['variant']}_{action_name.lower()}"
                run([
                    sys.executable, str(framework / "tools" / "convert_soulgold_g3r10_special_state.py"),
                    "--source", str(species_dir),
                    "--species", target["species"],
                    "--national-dex", target["dex"],
                    "--action", action_name,
                    "--direction", target["direction"],
                    "--anchor-x", str(anchor[0]),
                    "--anchor-y", str(anchor[1]),
                    "--source-revision", SPRITECOLLAB_REV,
                    "--source-repo-path", f"sprite/{target['spritecollab_id']}",
                    "--output", str(action_work),
                    "--host-asset-root", asset_root,
                ])
                run([
                    sys.executable, str(framework / "tools" / "pmd_gba_remap_host_palette.py"),
                    "--frames-root", str(action_work),
                    "--host-palette", str(host_palette),
                ])
                output_name = "event_sleep" if action_name == "EventSleep" else "wake"
                run([
                    sys.executable, str(framework / "tools" / "emit_soulgold_g3r10_special_state_c.py"),
                    "--ir", str(action_work / "manifest.ir.json"),
                    "--output", str(staging / "src" / f"pmd_{target['slug']}_{target['variant']}_{output_name}.c"),
                    "--variant", target["variant"],
                    "--action", action_name,
                    "--asset-root", asset_root,
                ])

                manifest = json.loads((action_work / "manifest.ir.json").read_text(encoding="utf-8"))
                generated[action_name] = manifest
                combined["actions"][action_name] = manifest["actions"][action_name]
                folder = FOLDERS[action_name]
                dst = staging / "graphics" / "pmd" / target["slug"] / target["variant"] / folder
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(action_work / folder, dst)

            combined.setdefault("g3r10", {})["special_state_view_policy"] = summary["view_policy"]
            combined["g3r10"]["EventSleep"] = generated["EventSleep"]["special_state_view"]
            combined["g3r10"]["Wake"] = generated["Wake"]["special_state_view"]

            shadow_size, shadow_records = g3r5shadow.source_shadow_records(
                species_dir, target["direction"], list(NORMAL_ACTIONS)
            )
            metas = g3r4.parse_anim_data_g3r4(species_dir / "AnimData.xml")
            special_layouts = {}
            for action_name in SPECIAL_ACTIONS:
                meta = base.resolve_action(action_name, metas)
                resolved = view.resolve_sleep_layout(species_dir, meta, target["direction"])
                special_shadow_size, records = view.sleep_shadow_records(species_dir, meta, resolved)
                if special_shadow_size != shadow_size:
                    raise SystemExit(f"{key}/{action_name}: ShadowSize mismatch")
                shadow_records[action_name] = records
                special_layouts[action_name] = resolved

            final_centers = {}
            for action_name in ALL_ACTIONS:
                body_frames = combined["actions"][action_name]["frames"]
                shadow_frames = shadow_records[action_name]
                if len(body_frames) != len(shadow_frames):
                    raise SystemExit(f"{key}/{action_name}: body-shadow frame mismatch")
                final_centers[action_name] = []
                for body, shadow in zip(body_frames, shadow_frames):
                    sx, sy = [int(v) for v in shadow["center"]]
                    final_centers[action_name].append([
                        sx + int(body["paste_x"]),
                        sy + int(body["paste_y"]),
                    ])

            combined.setdefault("shadow", {})["shadow_size"] = shadow_size
            combined["shadow"]["g3r10_policy"] = "FRAME_SYNCHRONOUS_PMDCOLLAB_ALL_SPECIAL_STATE_ACTIONS"
            shadow_asset = g3r6a.emit_dynamic_shadow_c(
                staging / "src" / f"pmd_{target['slug']}_{target['variant']}_shadow.c",
                target,
                combined,
                shadow_records,
                final_centers,
            )
            combined_path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")

            event = combined["actions"]["EventSleep"]
            wake = combined["actions"]["Wake"]
            if event["source_layout"] != view.DIRECTIONAL or event["direction"] != target["direction"]:
                raise SystemExit(f"{key}: EventSleep pinned directional contract changed")
            if wake["source_layout"] != view.DIRECTIONAL or wake["direction"] != target["direction"]:
                raise SystemExit(f"{key}: Wake pinned directional contract changed")
            if [int(f["duration"]) for f in event["frames"]] != [30, 35]:
                raise SystemExit(f"{key}: EventSleep pinned duration contract changed")
            if [int(f["duration"]) for f in wake["frames"]] != [8, 6, 14, 4, 10]:
                raise SystemExit(f"{key}: Wake pinned duration contract changed")

            summary["targets"][key] = {
                "species": target["species"],
                "variant": target["variant"],
                "battle_anchor": anchor,
                "requested_battle_direction": target["direction"],
                "Sleep": {
                    "source_layout": special_layouts["Sleep"]["layout"],
                    "applied_direction": special_layouts["Sleep"]["applied_source_direction"],
                },
                "EventSleep": {
                    "frame_size": [event["source_frame_width"], event["source_frame_height"]],
                    "frame_count": len(event["frames"]),
                    "durations": [int(f["duration"]) for f in event["frames"]],
                    "source_layout": event["source_layout"],
                    "source_row": event["source_row"],
                    "applied_direction": event["direction"],
                    "visible_pixel_conservation": all(bool(f["visible_pixel_conservation"]) for f in event["frames"]),
                    "shadow_frames": shadow_asset["actions"]["EventSleep"],
                },
                "Wake": {
                    "frame_size": [wake["source_frame_width"], wake["source_frame_height"]],
                    "frame_count": len(wake["frames"]),
                    "durations": [int(f["duration"]) for f in wake["frames"]],
                    "source_layout": wake["source_layout"],
                    "source_row": wake["source_row"],
                    "applied_direction": wake["direction"],
                    "visible_pixel_conservation": all(bool(f["visible_pixel_conservation"]) for f in wake["frames"]),
                    "shadow_frames": shadow_asset["actions"]["Wake"],
                },
                "expanded_shadow_atlas_frame_count": shadow_asset["frame_count"],
                "expanded_shadow_atlas_bytes": shadow_asset["gfx_bytes"],
            }
    finally:
        g3r6a.ACTIONS = old_actions

    (out / "G3R10_SPECIAL_STATE_ASSET_SUMMARY.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    for key, rec in summary["targets"].items():
        print(key, "EventSleep", rec["EventSleep"]["frame_count"], rec["EventSleep"]["source_layout"])
        print(key, "Wake", rec["Wake"]["frame_count"], rec["Wake"]["source_layout"])
    print("G3R10 special-state transition asset preparation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
