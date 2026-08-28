#!/usr/bin/env python3
"""Prepare SoulGold G3R6A ambient + PMDCollab Hurt reaction assets.

G3R6A deliberately leaves the unresolved Cyndaquil ambient 1px defect on the
ledger and advances to a distinct reaction class: Hurt.

A first CI attempt proved that Cyndaquil Hurt is 40x56 and individually fits a
64x64 GBA OBJ, but its PMDCollab body center cannot be placed at the existing
ambient anchor (32,44) without clipping the bottom of the source frame. Cropping
or scaling is forbidden.

G3R6A therefore resolves an action-specific clip-safe canvas anchor from every
Hurt Offsets.png frame. The source pixels are normalized to that anchor, then a
single constant runtime x2/y2 compensation restores the exact ambient battle
anchor. This changes storage geometry only, not the intended screen-space PMD
body center. Authentic per-frame Hurt shadows are generated from Hurt-Shadow.png
and follow the same body x2/y2 compensation.
"""

from __future__ import annotations

import argparse
import json
import shutil
import statistics
import subprocess
import sys
from pathlib import Path

from PIL import Image

import convert_soulgold_g3r4 as g3r4
import convert_soulgold_g3r5 as g3r5shadow
import pmd_gba_converter as base
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
MAX_HURT_COMPENSATION = 16

TARGETS = (
    {"species": "Cyndaquil", "slug": "cyndaquil", "dex": "155", "spritecollab_id": "0155", "variant": "player", "direction": "UpRight"},
    {"species": "Marill", "slug": "marill", "dex": "183", "spritecollab_id": "0183", "variant": "opponent", "direction": "DownLeft"},
)

# Preserve G3R5C ambient output exactly. This remains a known defect ledger
# entry, not an authority for the new Hurt reaction.
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


def clamp(value: int, lo: int, hi: int) -> int:
    return min(max(value, lo), hi)


def resolve_clip_safe_anchor(species_dir: Path, direction: str, action_name: str, desired: tuple[int, int]) -> dict:
    """Find a single canvas anchor that keeps every source action frame intact.

    For a source body center C and source frame size W/H, an anchor A is legal
    exactly when C <= A <= C + (64 - W/H). Intersect those ranges over all
    frames, then choose the legal point nearest the desired battle anchor.
    """
    metas = g3r4.parse_anim_data_g3r4(species_dir / "AnimData.xml")
    resolved = base.resolve_action(action_name, metas)
    if resolved.frame_width > base.CANVAS_W or resolved.frame_height > base.CANVAS_H:
        raise SystemExit(
            f"{action_name} is intrinsically {resolved.frame_width}x{resolved.frame_height}; "
            "single-OBJ clip-safe anchoring cannot solve this action"
        )

    offsets = Image.open(species_dir / f"{resolved.source_action}-Offsets.png").convert("RGBA")
    centers: list[list[int]] = []
    x_lo, y_lo = -32768, -32768
    x_hi, y_hi = 32767, 32767
    per_frame_bounds: list[dict[str, object]] = []

    for i in range(resolved.frame_count):
        crop = base.crop_direction_frame(offsets, resolved, direction, i)
        cx, cy = base.body_center_from_offsets(crop)
        lo_x = cx
        hi_x = cx + base.CANVAS_W - resolved.frame_width
        lo_y = cy
        hi_y = cy + base.CANVAS_H - resolved.frame_height
        x_lo, x_hi = max(x_lo, lo_x), min(x_hi, hi_x)
        y_lo, y_hi = max(y_lo, lo_y), min(y_hi, hi_y)
        centers.append([cx, cy])
        per_frame_bounds.append({
            "frame": i,
            "body_center": [cx, cy],
            "x_range": [lo_x, hi_x],
            "y_range": [lo_y, hi_y],
        })

    if x_lo > x_hi or y_lo > y_hi:
        raise SystemExit(
            f"{action_name} has no common 64x64 clip-safe anchor: "
            f"x=[{x_lo},{x_hi}] y=[{y_lo},{y_hi}]. Multi-OBJ required."
        )

    safe = [clamp(desired[0], x_lo, x_hi), clamp(desired[1], y_lo, y_hi)]
    compensation = [desired[0] - safe[0], desired[1] - safe[1]]
    if any(abs(v) > MAX_HURT_COMPENSATION for v in compensation):
        raise SystemExit(f"Suspicious {action_name} clip compensation {compensation}")

    return {
        "source_action": resolved.source_action,
        "frame_size": [resolved.frame_width, resolved.frame_height],
        "frame_count": resolved.frame_count,
        "source_body_centers": centers,
        "per_frame_legal_anchor_bounds": per_frame_bounds,
        "common_legal_anchor_x": [x_lo, x_hi],
        "common_legal_anchor_y": [y_lo, y_hi],
        "desired_battle_anchor": [desired[0], desired[1]],
        "clip_safe_canvas_anchor": safe,
        "runtime_compensation": compensation,
    }


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
                "battle_offset_before_body_x2y2": [dx, dy],
                "mask_bbox": rec["mask_bbox"],
                "obj_bbox": obj_bbox,
                "mask_pixels": int(rec["mask_pixel_count"]),
            })
            global_index += 1

    lines = [
        "/* Auto-generated G3R6A frame-synchronous authentic PMDCollab shadow atlas. */",
        f"/* source=SpriteCollab sprite/{target['spritecollab_id']} @ {SPRITECOLLAB_REV} */",
        "/* Includes ambient + Hurt; body x2/y2 adds action clip compensation at runtime. */",
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
            lines.append(
                f"    {{ .tileOffset = {fr['tileOffset']}, .xOffset = {fr['xOffset']}, .yOffset = {fr['yOffset']} }},"
            )
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
    return {
        "frame_count": global_index,
        "gfx_bytes": len(raw_all),
        "actions": action_frames,
        "mask_audit": mask_audit,
    }


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

    # Reuse the audited G3R5 resolver only for the known clip-safe ambient
    # anchors and PMD source provenance. G3R6A regenerates its actual body set.
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
        "hurt_body_policy": "ACTION_SPECIFIC_CLIP_SAFE_CANVAS_PLUS_EXACT_BATTLE_ANCHOR_COMPENSATION",
        "hurt_trigger": "SOULGOLD_CONTROLLER_HITANIMATION_PMD_OWNERSHIP_OVERRIDE",
        "shadow_policy": "FRAME_SYNCHRONOUS_PMDCOLLAB_SHADOW_PNG_AMBIENT_PLUS_HURT",
        "targets": {},
    }

    for target in TARGETS:
        key = f"{target['species']}_{target['variant']}"
        base_rec = base_summary["targets"][key]
        desired_anchor = tuple(int(v) for v in base_rec["resolved_body_anchor"])
        species_dir = spritecollab / "sprite" / target["spritecollab_id"]
        host_palette = soulgold / "graphics" / "pokemon" / target["slug"] / "normal.pal"
        variant_dir = work / f"{target['slug']}_{target['variant']}"
        hurt_dir = work / f"{target['slug']}_{target['variant']}_hurt"

        # Ambient remains exactly on the existing G3R5C canvas anchor.
        run([
            sys.executable, str(framework / "tools" / "convert_soulgold_g3r4.py"),
            "--source", str(species_dir), "--species", target["species"],
            "--national-dex", target["dex"], "--actions", ",".join(AMBIENT_ACTIONS),
            "--direction", target["direction"], "--anchor-x", str(desired_anchor[0]), "--anchor-y", str(desired_anchor[1]),
            "--source-revision", SPRITECOLLAB_REV, "--source-repo-path", f"sprite/{target['spritecollab_id']}",
            "--output", str(variant_dir), "--host-asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])

        hurt_anchor = resolve_clip_safe_anchor(species_dir, target["direction"], "Hurt", desired_anchor)
        safe_x, safe_y = [int(v) for v in hurt_anchor["clip_safe_canvas_anchor"]]
        comp_x, comp_y = [int(v) for v in hurt_anchor["runtime_compensation"]]

        # Hurt is converted separately because its taller frame needs a different
        # storage anchor. The final x2/y2 compensation restores battle geometry.
        run([
            sys.executable, str(framework / "tools" / "convert_soulgold_g3r4.py"),
            "--source", str(species_dir), "--species", target["species"],
            "--national-dex", target["dex"], "--actions", "Hurt",
            "--direction", target["direction"], "--anchor-x", str(safe_x), "--anchor-y", str(safe_y),
            "--source-revision", SPRITECOLLAB_REV, "--source-repo-path", f"sprite/{target['spritecollab_id']}",
            "--output", str(hurt_dir), "--host-asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])

        manifest_path = variant_dir / "manifest.ir.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        hurt_manifest = json.loads((hurt_dir / "manifest.ir.json").read_text(encoding="utf-8"))
        if "Hurt" in manifest["actions"]:
            raise SystemExit(f"{key}: ambient manifest unexpectedly already contains Hurt")
        manifest["actions"]["Hurt"] = hurt_manifest["actions"]["Hurt"]
        shutil.copytree(hurt_dir / "hurt", variant_dir / "hurt")
        manifest.setdefault("body_profile", {})["action_canvas_anchors"] = {
            "ambient": [desired_anchor[0], desired_anchor[1]],
            "Hurt": [safe_x, safe_y],
        }

        shadow_size, shadow_records = g3r5shadow.source_shadow_records(
            species_dir, target["direction"], list(ACTIONS)
        )
        final_centers: dict[str, list[list[int]]] = {}
        for action in ACTIONS:
            final_centers[action] = []
            frames = manifest["actions"][action]["frames"]
            records = shadow_records[action]
            if len(frames) != len(records):
                raise SystemExit(f"{key}/{action}: body/shadow frame count mismatch")
            for frame, rec in zip(frames, records):
                sx, sy = [int(v) for v in rec["center"]]
                final_centers[action].append([sx + int(frame["paste_x"]), sy + int(frame["paste_y"])])

        idle0 = final_centers["Idle"][0]
        body_corrections: dict[str, list[int]] = {}
        action_ground: dict[str, int] = {}
        for action in AMBIENT_ACTIONS:
            raw = [int(idle0[1]) - int(center[1]) for center in final_centers[action]]
            action_dy = int(statistics.median(raw))
            if abs(action_dy) > MAX_AMBIENT_CORRECTION:
                raise SystemExit(f"{key}/{action} ambient correction {action_dy}px exceeds ±1")
            action_ground[action] = action_dy
            body_corrections[action] = []
            for frame in manifest["actions"][action]["frames"]:
                idx = int(frame["index"])
                dy = action_dy + int(
                    RUNTIME_MICRO_OVERRIDES.get((target["species"], target["variant"], action, idx), 0)
                )
                if abs(dy) > MAX_AMBIENT_CORRECTION:
                    raise SystemExit(f"{key}/{action}/{idx} correction {dy}px exceeds ±1")
                frame["presentation_dx"] = 0
                frame["presentation_dy"] = dy
                body_corrections[action].append(dy)

        body_corrections["Hurt"] = []
        for frame in manifest["actions"]["Hurt"]["frames"]:
            frame["presentation_dx"] = comp_x
            frame["presentation_dy"] = comp_y
            body_corrections["Hurt"].append(comp_y)
            # Converter authority: source center + paste equals safe anchor.
            if int(frame["source_center_x"]) + int(frame["paste_x"]) != safe_x:
                raise SystemExit(f"{key}/Hurt lost clip-safe X anchor")
            if int(frame["source_center_y"]) + int(frame["paste_y"]) != safe_y:
                raise SystemExit(f"{key}/Hurt lost clip-safe Y anchor")
            # Runtime compensation must reconstruct the desired battle anchor.
            if safe_x + comp_x != desired_anchor[0] or safe_y + comp_y != desired_anchor[1]:
                raise SystemExit(f"{key}/Hurt compensation does not reconstruct battle anchor")

        manifest["grounding"] = {
            "battle_vertical_authority": "G3R6A_AMBIENT_ACCEPTED_PLUS_HURT_CLIP_SAFE_COMPENSATION",
            "ambient_action_ground_corrections": action_ground,
            "presentation_corrections_y": body_corrections,
            "hurt_desired_battle_anchor": [desired_anchor[0], desired_anchor[1]],
            "hurt_clip_safe_canvas_anchor": [safe_x, safe_y],
            "hurt_clip_compensation": [comp_x, comp_y],
            "hurt_clip_safe_audit": hurt_anchor,
            "hurt_grounding_heuristic": False,
            "hurt_crop_or_scale": False,
            "known_deferred_defect": "CYNDAQUIL_AMBIENT_SINGLE_1PX_SINK_ROOT_CAUSE_UNRESOLVED",
        }
        manifest["shadow"] = {
            "included_in_body_frames": False,
            "policy": "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK_CENTERED_ON_BATTLE_X",
            "shadow_size": shadow_size,
            "g3r6a_policy": "FRAME_SYNCHRONOUS_PMDCOLLAB_SHADOW_PNG_AMBIENT_PLUS_HURT",
            "hurt_runtime_relation": "CANVAS_SHADOW_OFFSET_PLUS_BODY_X2Y2_CLIP_COMPENSATION",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        # Remap after merging Hurt so all frames use the SoulGold species palette.
        run([
            sys.executable, str(framework / "tools" / "pmd_gba_remap_host_palette.py"),
            "--frames-root", str(variant_dir), "--host-palette", str(host_palette),
        ])
        run([
            sys.executable, str(framework / "tools" / "emit_soulgold_g3r6a_c.py"),
            "--ir", str(manifest_path),
            "--output", str(staging / "src" / f"pmd_{target['slug']}_{target['variant']}_ambient.c"),
            "--variant", target["variant"],
            "--asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])
        copy_variant_assets(variant_dir, staging / "graphics" / "pmd" / target["slug"] / target["variant"])
        shadow_asset = emit_dynamic_shadow_c(
            staging / "src" / f"pmd_{target['slug']}_{target['variant']}_shadow.c",
            target, manifest, shadow_records, final_centers,
        )

        hurt_meta = manifest["actions"]["Hurt"]
        summary["targets"][key] = {
            "species": target["species"],
            "variant": target["variant"],
            "direction": target["direction"],
            "resolved_ambient_body_anchor": [desired_anchor[0], desired_anchor[1]],
            "body_presentation_corrections_y": body_corrections,
            "hurt_frame_count": len(hurt_meta["frames"]),
            "hurt_durations": [int(f["duration"]) for f in hurt_meta["frames"]],
            "hurt_frame_size": [int(hurt_meta["source_frame_width"]), int(hurt_meta["source_frame_height"])],
            "hurt_clip_safe_anchor": [safe_x, safe_y],
            "hurt_battle_anchor": [desired_anchor[0], desired_anchor[1]],
            "hurt_clip_compensation": [comp_x, comp_y],
            "hurt_clip_safe_audit": hurt_anchor,
            "dynamic_shadow": shadow_asset,
        }

    for key, rec in summary["targets"].items():
        if rec["hurt_frame_count"] != 2:
            raise SystemExit(f"{key}: expected two PMDCollab Hurt frames")
        if rec["hurt_durations"] != [2, 8]:
            raise SystemExit(f"{key}: expected PMDCollab Hurt durations [2,8], got {rec['hurt_durations']}")
        if rec["hurt_frame_size"][0] > 64 or rec["hurt_frame_size"][1] > 64:
            raise SystemExit(f"{key}: Hurt unexpectedly exceeds single OBJ")
        if len(rec["dynamic_shadow"]["actions"]["Hurt"]) != 2:
            raise SystemExit(f"{key}: Hurt shadow timeline mismatch")
        safe = rec["hurt_clip_safe_anchor"]
        comp = rec["hurt_clip_compensation"]
        battle = rec["hurt_battle_anchor"]
        if [safe[0] + comp[0], safe[1] + comp[1]] != battle:
            raise SystemExit(f"{key}: clip-safe compensation invariant failed")

    (out / "G3R6A_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    for key, rec in summary["targets"].items():
        print(
            key,
            "Hurt size=", rec["hurt_frame_size"],
            "safeAnchor=", rec["hurt_clip_safe_anchor"],
            "battleAnchor=", rec["hurt_battle_anchor"],
            "comp=", rec["hurt_clip_compensation"],
        )
    print("Prepared SoulGold G3R6A Hurt reaction staging bundle:", staging)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
