#!/usr/bin/env python3
"""Prepare SoulGold G3R6A ambient + PMDCollab Hurt reaction assets.

G3R6A deliberately does not continue tuning the unresolved ambient 1px issue.
It preserves the G3R5C ambient body output exactly, then adds Hurt as a separate
reaction class. Hurt uses PMDCollab green body-center normalization with zero
battle grounding correction, plus its own frame-synchronous *-Shadow.png data.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

import convert_soulgold_g3r5 as g3r5shadow
import prepare_soulgold_g3r5_assets as g3r5prep

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
AMBIENT_ACTIONS = ("Idle", "Walk", "Nod", "Rotate")
REACTION_ACTIONS = ("Hurt",)
ACTIONS = AMBIENT_ACTIONS + REACTION_ACTIONS
SHADOW_FRAME_BYTES = 0x80
SHADOW_TILES_PER_FRAME = 4
BODY_CANVAS_CENTER = 32
MAX_AMBIENT_CORRECTION = 1

TARGETS = (
    {"species": "Cyndaquil", "slug": "cyndaquil", "dex": "155", "spritecollab_id": "0155", "variant": "player", "direction": "UpRight"},
    {"species": "Marill", "slug": "marill", "dex": "183", "spritecollab_id": "0183", "variant": "opponent", "direction": "DownLeft"},
)

# Preserve G3R5C exactly. This is a known visual defect ledger item, not a new
# heuristic authority for reactions.
RUNTIME_MICRO_OVERRIDES = {
    ("Cyndaquil", "player", "Idle", 1): -1,
}


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def copy_variant_assets(src: Path, dst: Path) -> None:
    if dst.exists():
        shutil.rmtree(dst)
    dst.mkdir(parents=True, exist_ok=True)
    for action in ACTIONS:
        shutil.copytree(src / action.lower(), dst / action.lower())
    shutil.copy2(src / "manifest.ir.json", dst / "manifest.ir.json")


def sym(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def c_bytes(raw: list[int]) -> list[str]:
    return ["    " + ", ".join(f"0x{x:02X}" for x in raw[i:i + 16]) + "," for i in range(0, len(raw), 16)]


def emit_dynamic_shadow_c(path: Path, target: dict[str, str], manifest: dict, shadow_records: dict, final_centers: dict) -> dict:
    species = target["species"]
    prefix = f"Pmd{sym(species)}{sym(target['variant'].title())}"
    idle0 = final_centers["Idle"][0]
    battle_base_x = 0
    battle_base_y = int(idle0[1]) - BODY_CANVAS_CENTER

    raw_all: list[int] = []
    action_frames: dict[str, list[dict[str, int]]] = {}
    mask_audit: dict[str, list[dict]] = {}
    global_index = 0

    for action in ACTIONS:
        action_frames[action] = []
        mask_audit[action] = []
        for i, rec in enumerate(shadow_records[action]):
            raw, obj_bbox = g3r5prep.pack_shadow_4bpp(
                [[int(x), int(y)] for x, y in rec["mask_pixels"]],
                [int(v) for v in rec["center"]],
            )
            if len(raw) != SHADOW_FRAME_BYTES:
                raise SystemExit(f"{species}/{action}/{i} shadow packed to {len(raw)} bytes")
            raw_all.extend(raw)
            center = final_centers[action][i]
            dx = battle_base_x + int(center[0]) - int(idle0[0])
            dy = battle_base_y + int(center[1]) - int(idle0[1])
            action_frames[action].append({
                "tileOffset": global_index * SHADOW_TILES_PER_FRAME,
                "xOffset": dx,
                "yOffset": dy,
            })
            mask_audit[action].append({
                "source_center": rec["center"],
                "normalized_center": center,
                "battle_offset": [dx, dy],
                "mask_bbox": rec["mask_bbox"],
                "obj_bbox": obj_bbox,
                "mask_pixels": int(rec["mask_pixel_count"]),
            })
            global_index += 1

    lines = [
        "/* Auto-generated G3R6A frame-synchronous authentic PMDCollab shadow atlas. */",
        f"/* source=SpriteCollab sprite/{target['spritecollab_id']} @ {SPRITECOLLAB_REV} */",
        "/* Includes ambient + Hurt; Hurt shadow advances with Hurt body frame index. */",
        '#include "global.h"',
        '#include "pmd_soulgold_dynamic_shadow.h"',
        "",
        f"const u8 g{prefix}GroundShadowGfx[{len(raw_all)}] __attribute__((aligned(4))) =",
        "{",
        *c_bytes(raw_all),
        "};",
        f"const u16 g{prefix}GroundShadowGfxSize = sizeof(g{prefix}GroundShadowGfx);",
        f"const s8 g{prefix}GroundShadowXOffset = 0;",
        f"const s8 g{prefix}GroundShadowYOffset = {battle_base_y};",
        f"const u8 g{prefix}GroundShadowShadowSize = {int(manifest['shadow']['shadow_size'])};",
        "",
    ]

    for action in ACTIONS:
        frames_sym = f"s{prefix}{sym(action)}ShadowFrames"
        action_sym = f"g{prefix}{sym(action)}ShadowAction"
        lines += [f"static const struct PmdSoulGoldShadowFrame {frames_sym}[] =", "{"]
        for fr in action_frames[action]:
            lines.append(f"    {{ .tileOffset = {fr['tileOffset']}, .xOffset = {fr['xOffset']}, .yOffset = {fr['yOffset']} }},")
        lines += ["};", "", f"const struct PmdSoulGoldShadowAction {action_sym} =", "{",
                  f"    .frames = {frames_sym},", f"    .frameCount = ARRAY_COUNT({frames_sym}),", "};", ""]

    idle0_fr = action_frames["Idle"][0]
    lines += [
        f"static const struct PmdSoulGoldShadowFrame s{prefix}HomeShadowFrames[] =", "{",
        f"    {{ .tileOffset = {idle0_fr['tileOffset']}, .xOffset = {idle0_fr['xOffset']}, .yOffset = {idle0_fr['yOffset']} }},",
        "};", "",
        f"const struct PmdSoulGoldShadowAction g{prefix}HomeShadowAction =", "{",
        f"    .frames = s{prefix}HomeShadowFrames,",
        f"    .frameCount = ARRAY_COUNT(s{prefix}HomeShadowFrames),",
        "};", "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")
    return {"frame_count": global_index, "gfx_bytes": len(raw_all), "actions": action_frames, "mask_audit": mask_audit}


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
    base_out = out / "g3r5_authority"
    staging = out / "staging"
    work = out / "work"
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    run([
        sys.executable, str(framework / "tools" / "prepare_soulgold_g3r5_assets.py"),
        "--framework-root", str(framework), "--spritecollab", str(spritecollab),
        "--soulgold", str(soulgold), "--output", str(base_out),
    ])
    base_summary = json.loads((base_out / "G3R5_ASSET_SUMMARY.json").read_text(encoding="utf-8"))
    shutil.copytree(base_out / "staging", staging)
    work.mkdir(parents=True)

    summary = {
        "phase": "G3R6A_HURT_REACTION",
        "parent": "G3R5C_SHADOW_ACCEPTED_AMBIENT_1PX_DEFERRED",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "ambient_policy": "PRESERVE_G3R5C_OUTPUT_WITH_KNOWN_1PX_DEFECT_DEFERRED",
        "hurt_body_policy": "PMDCOLLAB_GREEN_BODY_CENTER_ZERO_PRESENTATION_CORRECTION",
        "hurt_trigger": "SOULGOLD_CONTROLLER_HITANIMATION_PMDOwnership_OVERRIDE",
        "shadow_policy": "FRAME_SYNCHRONOUS_PMDCOLLAB_SHADOW_PNG_AMBIENT_PLUS_HURT",
        "targets": {},
    }

    for target in TARGETS:
        key = f"{target['species']}_{target['variant']}"
        base_rec = base_summary["targets"][key]
        anchor_x, anchor_y = [int(v) for v in base_rec["resolved_body_anchor"]]
        species_dir = spritecollab / "sprite" / target["spritecollab_id"]
        host_palette = soulgold / "graphics" / "pokemon" / target["slug"] / "normal.pal"
        variant_dir = work / f"{target['slug']}_{target['variant']}"

        run([
            sys.executable, str(framework / "tools" / "convert_soulgold_g3r4.py"),
            "--source", str(species_dir), "--species", target["species"],
            "--national-dex", target["dex"], "--actions", ",".join(ACTIONS),
            "--direction", target["direction"], "--anchor-x", str(anchor_x), "--anchor-y", str(anchor_y),
            "--source-revision", SPRITECOLLAB_REV, "--source-repo-path", f"sprite/{target['spritecollab_id']}",
            "--output", str(variant_dir), "--host-asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])

        manifest_path = variant_dir / "manifest.ir.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        shadow_size, shadow_records = g3r5shadow.source_shadow_records(species_dir, target["direction"], list(ACTIONS))
        final_centers = {}
        for action in ACTIONS:
            final_centers[action] = []
            for frame, rec in zip(manifest["actions"][action]["frames"], shadow_records[action]):
                sx, sy = [int(v) for v in rec["center"]]
                final_centers[action].append([sx + int(frame["paste_x"]), sy + int(frame["paste_y"])])

        idle0 = final_centers["Idle"][0]
        body_corrections = {}
        action_ground = {}
        for action in AMBIENT_ACTIONS:
            raw = [int(idle0[1]) - int(center[1]) for center in final_centers[action]]
            action_dy = int(statistics.median(raw))
            if abs(action_dy) > MAX_AMBIENT_CORRECTION:
                raise SystemExit(f"{key}/{action} ambient correction {action_dy}px exceeds ±1")
            action_ground[action] = action_dy
            body_corrections[action] = []
            for frame in manifest["actions"][action]["frames"]:
                idx = int(frame["index"])
                dy = action_dy + int(RUNTIME_MICRO_OVERRIDES.get((target["species"], target["variant"], action, idx), 0))
                if abs(dy) > MAX_AMBIENT_CORRECTION:
                    raise SystemExit(f"{key}/{action}/{idx} correction {dy}px exceeds ±1")
                frame["presentation_dx"] = 0
                frame["presentation_dy"] = dy
                body_corrections[action].append(dy)

        for action in REACTION_ACTIONS:
            body_corrections[action] = []
            for frame in manifest["actions"][action]["frames"]:
                frame["presentation_dx"] = 0
                frame["presentation_dy"] = 0
                body_corrections[action].append(0)

        manifest["grounding"] = {
            "battle_vertical_authority": "G3R6A_AMBIENT_ACCEPTED_PLUS_HURT_SOURCE_BODY_CENTER",
            "ambient_action_ground_corrections": action_ground,
            "presentation_corrections_y": body_corrections,
            "hurt_grounding_heuristic": False,
            "known_deferred_defect": "CYNDAQUIL_AMBIENT_SINGLE_1PX_SINK_ROOT_CAUSE_UNRESOLVED",
        }
        manifest["shadow"] = {
            "included_in_body_frames": False,
            "policy": "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK_CENTERED_ON_BATTLE_X",
            "shadow_size": shadow_size,
            "g3r6a_policy": "FRAME_SYNCHRONOUS_PMDCOLLAB_SHADOW_PNG_AMBIENT_PLUS_HURT",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        run([sys.executable, str(framework / "tools" / "pmd_gba_remap_host_palette.py"), "--frames-root", str(variant_dir), "--host-palette", str(host_palette)])
        run([
            sys.executable, str(framework / "tools" / "emit_soulgold_g3r6a_c.py"),
            "--ir", str(manifest_path),
            "--output", str(staging / "src" / f"pmd_{target['slug']}_{target['variant']}_ambient.c"),
            "--variant", target["variant"], "--asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])
        copy_variant_assets(variant_dir, staging / "graphics" / "pmd" / target["slug"] / target["variant"])
        shadow_asset = emit_dynamic_shadow_c(staging / "src" / f"pmd_{target['slug']}_{target['variant']}_shadow.c", target, manifest, shadow_records, final_centers)

        hurt_meta = manifest["actions"]["Hurt"]
        summary["targets"][key] = {
            "species": target["species"], "variant": target["variant"], "direction": target["direction"],
            "resolved_body_anchor": [anchor_x, anchor_y], "body_presentation_corrections": body_corrections,
            "hurt_frame_count": len(hurt_meta["frames"]),
            "hurt_durations": [int(f["duration"]) for f in hurt_meta["frames"]],
            "hurt_frame_size": [int(hurt_meta["source_frame_width"]), int(hurt_meta["source_frame_height"])],
            "dynamic_shadow": shadow_asset,
        }

    for key, rec in summary["targets"].items():
        if rec["hurt_frame_count"] != 2:
            raise SystemExit(f"{key}: expected two PMDCollab Hurt frames")
        if rec["hurt_durations"] != [2, 8]:
            raise SystemExit(f"{key}: expected PMDCollab Hurt durations [2,8], got {rec['hurt_durations']}")
        if rec["body_presentation_corrections"]["Hurt"] != [0, 0]:
            raise SystemExit(f"{key}: Hurt received forbidden grounding correction")
        if len(rec["dynamic_shadow"]["actions"]["Hurt"]) != 2:
            raise SystemExit(f"{key}: Hurt shadow timeline mismatch")

    (out / "G3R6A_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("Prepared SoulGold G3R6A Hurt reaction staging bundle:", staging)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
