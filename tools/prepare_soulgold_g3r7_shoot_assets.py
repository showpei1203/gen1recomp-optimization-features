#!/usr/bin/env python3
"""Prepare G3R7 Shoot assets on top of the complete G3R6B staging bundle.

This phase only establishes source-authoritative PMDCollab Shoot body/shadow data.
It does not yet decide which SoulGold moves should select Shoot instead of Attack.
That selector is intentionally deferred until move semantics are audited.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

import convert_soulgold_g3r5 as g3r5shadow
import prepare_soulgold_g3r6a_assets as g3r6a

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
ALL_ACTIONS = ("Idle", "Walk", "Nod", "Rotate", "Hurt", "Attack", "Shoot")
TARGETS = (
    {"species":"Cyndaquil","slug":"cyndaquil","dex":"155","spritecollab_id":"0155","variant":"player","direction":"UpRight"},
    {"species":"Marill","slug":"marill","dex":"183","spritecollab_id":"0183","variant":"opponent","direction":"DownLeft"},
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
    parent = out / "g3r6b_parent"
    staging = out / "staging"
    work = out / "work"

    run([
        sys.executable, str(framework / "tools" / "prepare_soulgold_g3r6b_assets.py"),
        "--framework-root", str(framework),
        "--spritecollab", str(spritecollab),
        "--soulgold", str(soulgold),
        "--output", str(parent),
    ])
    shutil.copytree(parent / "staging", staging)
    work.mkdir()
    parent_summary = json.loads((parent / "G3R6B_ASSET_SUMMARY.json").read_text(encoding="utf-8"))

    summary = {
        "phase": "G3R7_SHOOT_SOURCE_ASSETS",
        "parent": "G3R6B_ATTACK_BUILD_GATE",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "shoot_body_policy": "PMDCOLLAB_GREEN_BODY_CENTER_VISIBLE_PIXELS_100_PERCENT_CONSERVED",
        "shoot_shadow_policy": "FRAME_SYNCHRONOUS_AUTHENTIC_PMDCOLLAB_SHOOT_SHADOW",
        "move_selector_policy": "NOT_IMPLEMENTED_SOURCE_ASSET_GATE_ONLY",
        "combat_timing_policy": "SOULGOLD_REMAINS_AUTHORITATIVE",
        "known_ambient_1px_defect": "DEFERRED_ROOT_CAUSE_UNRESOLVED",
        "targets": {},
    }

    old_actions = g3r6a.ACTIONS
    g3r6a.ACTIONS = ALL_ACTIONS
    try:
        for target in TARGETS:
            key = f"{target['species']}_{target['variant']}"
            parent_rec = parent_summary["targets"][key]
            anchor = parent_rec["battle_anchor"]
            species_dir = spritecollab / "sprite" / target["spritecollab_id"]
            host_palette = soulgold / "graphics" / "pokemon" / target["slug"] / "normal.pal"
            shoot_dir = work / f"{target['slug']}_{target['variant']}_shoot"
            asset_root = f"graphics/pmd/{target['slug']}/{target['variant']}"

            run([
                sys.executable, str(framework / "tools" / "convert_soulgold_g3r7_shoot.py"),
                "--source", str(species_dir),
                "--species", target["species"],
                "--national-dex", target["dex"],
                "--direction", target["direction"],
                "--anchor-x", str(anchor[0]),
                "--anchor-y", str(anchor[1]),
                "--source-revision", SPRITECOLLAB_REV,
                "--source-repo-path", f"sprite/{target['spritecollab_id']}",
                "--output", str(shoot_dir),
                "--host-asset-root", asset_root,
            ])
            run([
                sys.executable, str(framework / "tools" / "pmd_gba_remap_host_palette.py"),
                "--frames-root", str(shoot_dir),
                "--host-palette", str(host_palette),
            ])
            run([
                sys.executable, str(framework / "tools" / "emit_soulgold_g3r7_shoot_c.py"),
                "--ir", str(shoot_dir / "manifest.ir.json"),
                "--output", str(staging / "src" / f"pmd_{target['slug']}_{target['variant']}_shoot.c"),
                "--variant", target["variant"],
                "--asset-root", asset_root,
            ])

            dst = staging / "graphics" / "pmd" / target["slug"] / target["variant"] / "shoot"
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(shoot_dir / "shoot", dst)

            combined_path = staging / "graphics" / "pmd" / target["slug"] / target["variant"] / "manifest.ir.json"
            combined = json.loads(combined_path.read_text(encoding="utf-8"))
            shoot_manifest = json.loads((shoot_dir / "manifest.ir.json").read_text(encoding="utf-8"))
            combined["actions"]["Shoot"] = shoot_manifest["actions"]["Shoot"]
            combined.setdefault("g3r7", {})["shoot_conversion"] = shoot_manifest["conversion"]
            combined["g3r7"]["shoot_body_profile"] = shoot_manifest["body_profile"]
            combined_path.write_text(json.dumps(combined, indent=2) + "\n", encoding="utf-8")

            shadow_size, shadow_records = g3r5shadow.source_shadow_records(
                species_dir, target["direction"], list(ALL_ACTIONS)
            )
            final_centers = {}
            for action in ALL_ACTIONS:
                final_centers[action] = []
                frames = combined["actions"][action]["frames"]
                records = shadow_records[action]
                if len(frames) != len(records):
                    raise SystemExit(f"{key}/{action} body-shadow mismatch {len(frames)} vs {len(records)}")
                for frame, rec in zip(frames, records):
                    sx, sy = [int(v) for v in rec["center"]]
                    final_centers[action].append([
                        sx + int(frame["paste_x"]),
                        sy + int(frame["paste_y"]),
                    ])
            combined.setdefault("shadow", {})["shadow_size"] = shadow_size
            combined["shadow"]["g3r7_policy"] = "FRAME_SYNCHRONOUS_PMDCOLLAB_AMBIENT_HURT_ATTACK_SHOOT"
            shadow_asset = g3r6a.emit_dynamic_shadow_c(
                staging / "src" / f"pmd_{target['slug']}_{target['variant']}_shadow.c",
                target, combined, shadow_records, final_centers,
            )

            shoot = shoot_manifest["actions"]["Shoot"]
            if any(not f["visible_pixel_conservation"] for f in shoot["frames"]):
                raise SystemExit(f"{key}: Shoot visible pixel conservation failed")
            if any(int(f["opaque_source_pixels"]) != int(f["opaque_copied_pixels"]) for f in shoot["frames"]):
                raise SystemExit(f"{key}: Shoot copied pixel mismatch")
            if len(shadow_asset["actions"]["Shoot"]) != len(shoot["frames"]):
                raise SystemExit(f"{key}: Shoot shadow timeline mismatch")

            summary["targets"][key] = {
                "species": target["species"],
                "variant": target["variant"],
                "direction": target["direction"],
                "battle_anchor": anchor,
                "shoot_source_frame_size": [shoot["source_frame_width"], shoot["source_frame_height"]],
                "shoot_frame_count": len(shoot["frames"]),
                "shoot_durations": [int(f["duration"]) for f in shoot["frames"]],
                "shoot_markers": {
                    "rush": shoot["rush_frame"],
                    "hit": shoot["hit_frame"],
                    "return": shoot["return_frame"],
                },
                "visible_pixel_conservation": True,
                "opaque_destination_bboxes": [f["opaque_destination_bbox"] for f in shoot["frames"]],
                "shoot_shadow_frames": shadow_asset["actions"]["Shoot"],
                "expanded_shadow_atlas_frame_count": shadow_asset["frame_count"],
                "expanded_shadow_atlas_bytes": shadow_asset["gfx_bytes"],
            }
    finally:
        g3r6a.ACTIONS = old_actions

    (out / "G3R7_SHOOT_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for key, rec in summary["targets"].items():
        print(key, "Shoot", rec["shoot_source_frame_size"], "frames", rec["shoot_frame_count"], "markers", rec["shoot_markers"])
        print(" durations", rec["shoot_durations"])
    print("G3R7 Shoot source asset preparation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
