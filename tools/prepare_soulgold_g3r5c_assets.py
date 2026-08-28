#!/usr/bin/env python3
"""Prepare SoulGold G3R5C grounded body + frame-synchronous PMD shadows.

G3R5B proved two separate facts:
1. PMDCollab Shadow.png is shadow-placement metadata and must not be applied as
   a per-frame body translation.
2. A whole grounded ambient action can still have a source-authored ground
   baseline that differs from Idle0. For Cyndaquil, the PMD shadow centers put
   Nod consistently ~1 px below Idle0 while Idle/Walk/Rotate center around the
   Idle0 ground plane.

G3R5C therefore uses a two-level body policy:
- one CONSTANT action-ground correction derived from the median PMD shadow
  center delta for each grounded ambient action;
- only explicit human-runtime micro overrides inside an action (currently the
  already-proven Cyndaquil Idle frame 1 -1 px correction).

Shadow rendering is fully independent. Every body frame gets its matching
PMDCollab *-Shadow.png mask and white-center delta. The battle calibration keeps
Idle0 centered on SoulGold battler X, then preserves all authored per-frame
shadow movement relative to that baseline.
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
ACTIONS = ("Idle", "Walk", "Nod", "Rotate")
SHADOW_FRAME_BYTES = 0x80
SHADOW_TILES_PER_FRAME = 4
BODY_CANVAS_CENTER = 32
MAX_BODY_CORRECTION = 1

TARGETS = (
    {"species": "Cyndaquil", "slug": "cyndaquil", "dex": "155", "spritecollab_id": "0155", "variant": "player", "direction": "UpRight"},
    {"species": "Marill", "slug": "marill", "dex": "183", "spritecollab_id": "0183", "variant": "opponent", "direction": "DownLeft"},
)

# This is deliberately tiny and evidence-backed. Do not turn this into another
# heuristic that silently edits every frame.
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


def emit_dynamic_shadow_c(
    path: Path,
    target: dict[str, str],
    manifest: dict[str, object],
    shadow_records: dict[str, list[dict[str, object]]],
    final_centers: dict[str, list[list[int]]],
) -> dict[str, object]:
    species = target["species"]
    variant = target["variant"]
    prefix = f"Pmd{sym(species)}{sym(variant.title())}"
    idle0 = final_centers["Idle"][0]
    battle_base_x = 0
    battle_base_y = int(idle0[1]) - BODY_CANVAS_CENTER

    raw_all: list[int] = []
    action_frames: dict[str, list[dict[str, int]]] = {}
    global_index = 0
    mask_audit: dict[str, list[dict[str, object]]] = {}

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

    if len(raw_all) != global_index * SHADOW_FRAME_BYTES:
        raise SystemExit("Dynamic shadow atlas byte count mismatch")

    lines = [
        "/* Auto-generated G3R5C frame-synchronous authentic PMDCollab shadow atlas. */",
        f"/* source=SpriteCollab sprite/{target['spritecollab_id']} @ {SPRITECOLLAB_REV} */",
        "/* Every action/frame uses its matching *-Shadow.png mask and white center. */",
        "/* Idle0 X is battle-calibrated to battler center; authored frame deltas are preserved. */",
        '#include "global.h"',
        '#include "pmd_soulgold_dynamic_shadow.h"',
        "",
        f"const u8 g{prefix}GroundShadowGfx[{len(raw_all)}] __attribute__((aligned(4))) =",
        "{",
        *c_bytes(raw_all),
        "};",
        f"const u16 g{prefix}GroundShadowGfxSize = sizeof(g{prefix}GroundShadowGfx);",
        # Legacy G3R5 adapter symbols stay available because that adapter still
        # owns body staging. G3R5C does not call its static shadow renderer.
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
        f"static const struct PmdSoulGoldShadowFrame s{prefix}HomeShadowFrames[] =",
        "{",
        f"    {{ .tileOffset = {idle0_fr['tileOffset']}, .xOffset = {idle0_fr['xOffset']}, .yOffset = {idle0_fr['yOffset']} }},",
        "};",
        "",
        f"const struct PmdSoulGoldShadowAction g{prefix}HomeShadowAction =",
        "{",
        f"    .frames = s{prefix}HomeShadowFrames,",
        f"    .frameCount = ARRAY_COUNT(s{prefix}HomeShadowFrames),",
        "};",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "frame_count": global_index,
        "gfx_bytes": len(raw_all),
        "battle_idle0_x_offset": battle_base_x,
        "battle_idle0_y_offset": battle_base_y,
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

    # Reuse G3R5 only for audited anchor resolution and PMD ShadowSize/source
    # validation. Its rejected per-frame body corrections are never reused.
    run([
        sys.executable, str(framework / "tools" / "prepare_soulgold_g3r5_assets.py"),
        "--framework-root", str(framework),
        "--spritecollab", str(spritecollab),
        "--soulgold", str(soulgold),
        "--output", str(base_out),
    ])
    base_summary = json.loads((base_out / "G3R5_ASSET_SUMMARY.json").read_text(encoding="utf-8"))
    shutil.copytree(base_out / "staging", staging)
    work.mkdir(parents=True)

    summary: dict[str, object] = {
        "phase": "G3R5C_ACTION_GROUND_DYNAMIC_SHADOW",
        "parent": "G3R5B_RUNTIME_PARTIAL_FAIL",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "body_policy": "G3R4_GREEN_CENTER_PLUS_CONSTANT_ACTION_GROUND_PLUS_RUNTIME_MICRO_OVERRIDE",
        "action_ground_authority": "MEDIAN_PMDCOLLAB_SHADOW_WHITE_CENTER_DELTA_TO_IDLE0",
        "shadow_policy": "FRAME_SYNCHRONOUS_PMDCOLLAB_SHADOW_PNG",
        "shadow_runtime_relation": "BODY_BASE_XY_PLUS_BODY_X2Y2_PLUS_FRAME_SHADOW_OFFSET",
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
            "--source", str(species_dir),
            "--species", target["species"],
            "--national-dex", target["dex"],
            "--actions", ",".join(ACTIONS),
            "--direction", target["direction"],
            "--anchor-x", str(anchor_x),
            "--anchor-y", str(anchor_y),
            "--source-revision", SPRITECOLLAB_REV,
            "--source-repo-path", f"sprite/{target['spritecollab_id']}",
            "--output", str(variant_dir),
            "--host-asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])

        manifest_path = variant_dir / "manifest.ir.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        shadow_size, shadow_records = g3r5shadow.source_shadow_records(species_dir, target["direction"], list(ACTIONS))
        final_centers: dict[str, list[list[int]]] = {}
        for action in ACTIONS:
            final_centers[action] = []
            frames = manifest["actions"][action]["frames"]
            for frame, rec in zip(frames, shadow_records[action]):
                sx, sy = [int(v) for v in rec["center"]]
                final_centers[action].append([sx + int(frame["paste_x"]), sy + int(frame["paste_y"])])

        idle0 = final_centers["Idle"][0]
        action_ground: dict[str, int] = {}
        raw_ground_deltas: dict[str, list[int]] = {}
        body_corrections: dict[str, list[int]] = {}
        overrides_used: list[dict[str, object]] = []

        for action in ACTIONS:
            raw = [int(idle0[1]) - int(center[1]) for center in final_centers[action]]
            raw_ground_deltas[action] = raw
            # int(median) intentionally truncates +/-0.5 toward zero. Ambient
            # intra-action 1px shadow motion is preserved; only a consistent
            # whole-action ground-plane displacement becomes body correction.
            action_dy = int(statistics.median(raw))
            if abs(action_dy) > MAX_BODY_CORRECTION:
                raise SystemExit(f"{key}/{action} action ground correction {action_dy}px exceeds ±1")
            action_ground[action] = action_dy
            body_corrections[action] = []
            for frame in manifest["actions"][action]["frames"]:
                idx = int(frame["index"])
                override = int(RUNTIME_MICRO_OVERRIDES.get((target["species"], target["variant"], action, idx), 0))
                dy = action_dy + override
                if abs(dy) > MAX_BODY_CORRECTION:
                    raise SystemExit(f"{key}/{action}/{idx} combined correction {dy}px exceeds ±1")
                frame["presentation_dx"] = 0
                frame["presentation_dy"] = dy
                body_corrections[action].append(dy)
                if override:
                    overrides_used.append({"action": action, "frame": idx, "dy": override})

        manifest["grounding"] = {
            "battle_vertical_authority": "G3R4B_ZERO_PLUS_RUNTIME_ACCEPTANCE_OVERRIDE",
            "g3r5c_policy": "CONSTANT_ACTION_GROUND_PLUS_RUNTIME_MICRO_OVERRIDE",
            "idle0_shadow_center": idle0,
            "shadow_white_center_deltas_to_idle0_y": raw_ground_deltas,
            "action_ground_corrections": action_ground,
            "runtime_micro_overrides": overrides_used,
            "presentation_corrections_y": body_corrections,
            "reason": "G3R5B runtime left a whole ambient action ~1px low; use PMD shadow ground metadata only as an action-level median, never as per-frame body motion",
        }
        manifest["shadow"] = {
            "included_in_body_frames": False,
            "policy": "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK_CENTERED_ON_BATTLE_X",
            "shadow_size": shadow_size,
            "g3r5c_policy": "FRAME_SYNCHRONOUS_PMDCOLLAB_SHADOW_PNG",
        }
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

        run([
            sys.executable, str(framework / "tools" / "pmd_gba_remap_host_palette.py"),
            "--frames-root", str(variant_dir),
            "--host-palette", str(host_palette),
        ])
        run([
            sys.executable, str(framework / "tools" / "emit_soulgold_g3r5b_c.py"),
            "--ir", str(manifest_path),
            "--output", str(staging / "src" / f"pmd_{target['slug']}_{target['variant']}_ambient.c"),
            "--variant", target["variant"],
            "--asset-root", f"graphics/pmd/{target['slug']}/{target['variant']}",
        ])
        copy_variant_assets(variant_dir, staging / "graphics" / "pmd" / target["slug"] / target["variant"])

        shadow_asset = emit_dynamic_shadow_c(
            staging / "src" / f"pmd_{target['slug']}_{target['variant']}_shadow.c",
            target,
            manifest,
            shadow_records,
            final_centers,
        )

        summary["targets"][key] = {
            "species": target["species"],
            "variant": target["variant"],
            "direction": target["direction"],
            "resolved_body_anchor": [anchor_x, anchor_y],
            "shadow_size": shadow_size,
            "shadow_white_center_deltas_to_idle0_y": raw_ground_deltas,
            "action_ground_corrections": action_ground,
            "body_presentation_corrections": body_corrections,
            "runtime_micro_overrides": overrides_used,
            "dynamic_shadow": shadow_asset,
        }

    cy = summary["targets"]["Cyndaquil_player"]
    # This is the source-level explanation for the remaining whole-action sink.
    if cy["action_ground_corrections"]["Nod"] != -1:
        raise SystemExit(f"Expected Cyndaquil Nod action ground correction -1, got {cy['action_ground_corrections']}")
    if cy["body_presentation_corrections"]["Idle"] != [0, -1]:
        raise SystemExit(f"Cyndaquil Idle runtime evidence lost: {cy['body_presentation_corrections']['Idle']}")
    if cy["dynamic_shadow"]["actions"]["Idle"][0]["xOffset"] != 0:
        raise SystemExit("Cyndaquil Idle0 shadow must remain centered on battle X")
    if len({tuple(x["battle_offset"]) for values in cy["dynamic_shadow"]["mask_audit"].values() for x in values}) <= 1:
        raise SystemExit("Dynamic shadow pipeline produced no per-frame positional variation")

    (out / "G3R5C_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("G3R5C source diagnosis:")
    print("  Cyndaquil raw shadow-ground deltas:", cy["shadow_white_center_deltas_to_idle0_y"])
    print("  Cyndaquil action-ground corrections:", cy["action_ground_corrections"])
    print("  Cyndaquil body corrections:", cy["body_presentation_corrections"])
    print("Prepared SoulGold G3R5C staging bundle:", staging)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
