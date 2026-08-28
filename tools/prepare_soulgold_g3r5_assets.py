#!/usr/bin/env python3
"""Prepare SoulGold G3R5 two-sided PMD shadow-grounded assets."""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
ACTIONS = ("Idle", "Walk", "Nod", "Rotate")
DIRECTIONS = ["Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft"]
DESIRED_G2_ANCHOR = (32, 44)
BODY_CANVAS = 64
SHADOW_OBJ_W = 32
SHADOW_OBJ_H = 8
SHADOW_OBJ_CENTER = (16, 4)

TARGETS = (
    {"species": "Cyndaquil", "slug": "cyndaquil", "dex": "155", "spritecollab_id": "0155", "variant": "player", "direction": "UpRight"},
    {"species": "Marill", "slug": "marill", "dex": "183", "spritecollab_id": "0183", "variant": "opponent", "direction": "DownLeft"},
)


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def require_revision(repo: Path, expected: str, label: str) -> None:
    actual = git_head(repo)
    if actual != expected:
        raise SystemExit(f"{label} revision mismatch: expected {expected}, got {actual}")


def parse_selected_geometry(anim_xml: Path) -> dict[str, tuple[int, int, int]]:
    root = ET.parse(anim_xml).getroot()
    out: dict[str, tuple[int, int, int]] = {}
    for anim in root.findall("./Anims/Anim"):
        name = anim.findtext("Name")
        if name not in ACTIONS:
            continue
        index = anim.findtext("Index")
        w = anim.findtext("FrameWidth")
        h = anim.findtext("FrameHeight")
        durations = anim.findall("./Durations/Duration")
        if index is None or w is None or h is None or not durations:
            raise SystemExit(f"Selected real action lacks Index/geometry/durations: {name} in {anim_xml}")
        out[name] = (int(w), int(h), len(durations))
    missing = [a for a in ACTIONS if a not in out]
    if missing:
        raise SystemExit(f"Missing selected directional actions {missing}: {anim_xml}")
    return out


def green_center(crop: Image.Image) -> tuple[int, int]:
    pts = []
    rgba = crop.convert("RGBA")
    px = rgba.load()
    for y in range(rgba.height):
        for x in range(rgba.width):
            r, g, b, a = px[x, y]
            if a and g >= 128 and g >= r * 1.5 and g >= b * 1.5:
                pts.append((x, y))
    if not pts:
        raise SystemExit("Directional Offsets frame has no PMD green body-center marker")
    return (
        int(round(sum(x for x, _ in pts) / len(pts))),
        int(round(sum(y for _, y in pts) / len(pts))),
    )


def audit_directional_body_source(species_dir: Path, direction: str) -> dict[str, object]:
    geometry = parse_selected_geometry(species_dir / "AnimData.xml")
    row = DIRECTIONS.index(direction)
    audit: dict[str, object] = {"direction": direction, "source_row": row, "actions": {}}
    for action in ACTIONS:
        w, h, frames = geometry[action]
        anim = Image.open(species_dir / f"{action}-Anim.png").convert("RGBA")
        offsets = Image.open(species_dir / f"{action}-Offsets.png").convert("RGBA")
        shadow = Image.open(species_dir / f"{action}-Shadow.png").convert("RGBA")
        expected_w = w * frames
        expected_h = h * len(DIRECTIONS)
        for label, image in (("body", anim), ("Offsets", offsets), ("Shadow", shadow)):
            if image.width < expected_w or image.height < expected_h:
                raise SystemExit(f"{action} {label} sheet is not a full directional sheet: {image.size} < {expected_w}x{expected_h}")
        centers = []
        for i in range(frames):
            crop = offsets.crop((i * w, row * h, (i + 1) * w, (row + 1) * h))
            centers.append(list(green_center(crop)))
        audit["actions"][action] = {
            "frame_width": w,
            "frame_height": h,
            "frame_count": frames,
            "green_body_centers": centers,
            "shadow_sheet_present": True,
        }
    return audit


def resolve_species_anchor(source_audit: dict[str, object]) -> tuple[int, int, dict[str, list[int]]]:
    x_lo, y_lo = 0, 0
    x_hi, y_hi = BODY_CANVAS, BODY_CANVAS
    for rec in source_audit["actions"].values():
        w = rec["frame_width"]
        h = rec["frame_height"]
        if w > BODY_CANVAS or h > BODY_CANVAS:
            raise SystemExit(f"Selected body frame exceeds {BODY_CANVAS}x{BODY_CANVAS}: {w}x{h}")
        for cx, cy in rec["green_body_centers"]:
            x_lo = max(x_lo, cx)
            y_lo = max(y_lo, cy)
            x_hi = min(x_hi, cx + BODY_CANVAS - w)
            y_hi = min(y_hi, cy + BODY_CANVAS - h)
    if x_lo > x_hi or y_lo > y_hi:
        raise SystemExit(f"No common body-center anchor fits all selected frames: x={x_lo}..{x_hi}, y={y_lo}..{y_hi}")
    desired_x, desired_y = DESIRED_G2_ANCHOR
    anchor_x = min(max(desired_x, x_lo), x_hi)
    anchor_y = min(max(desired_y, y_lo), y_hi)
    return anchor_x, anchor_y, {"x": [x_lo, x_hi], "y": [y_lo, y_hi]}


def copy_variant_assets(variant_dir: Path, target: Path) -> None:
    if target.exists():
        shutil.rmtree(target)
    target.mkdir(parents=True, exist_ok=True)
    for action in ACTIONS:
        shutil.copytree(variant_dir / action.lower(), target / action.lower())
    shutil.copy2(variant_dir / "manifest.ir.json", target / "manifest.ir.json")


def c_symbol(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def pack_shadow_4bpp(mask_pixels: list[list[int]], source_center: list[int]) -> tuple[list[int], list[int]]:
    canvas = [[0 for _ in range(SHADOW_OBJ_W)] for _ in range(SHADOW_OBJ_H)]
    cx, cy = source_center
    used: list[tuple[int, int]] = []
    for sx, sy in mask_pixels:
        dx = SHADOW_OBJ_CENTER[0] + int(sx) - int(cx)
        dy = SHADOW_OBJ_CENTER[1] + int(sy) - int(cy)
        if dx < 0 or dy < 0 or dx >= SHADOW_OBJ_W or dy >= SHADOW_OBJ_H:
            raise SystemExit(
                f"Authentic PMD shadow mask does not fit {SHADOW_OBJ_W}x{SHADOW_OBJ_H}: "
                f"source=({sx},{sy}) center=({cx},{cy}) -> ({dx},{dy})"
            )
        canvas[dy][dx] = 1
        used.append((dx, dy))

    if not used:
        raise SystemExit("Authentic PMD shadow mask produced no OBJ pixels")

    raw: list[int] = []
    # GBA 4bpp OBJ tiles are 8x8 tiles, 4 bytes per scanline. 32x8 = 4 tiles.
    for tile_x in range(SHADOW_OBJ_W // 8):
        for y in range(8):
            for pair in range(0, 8, 2):
                x = tile_x * 8 + pair
                lo = canvas[y][x] & 0xF
                hi = canvas[y][x + 1] & 0xF
                raw.append(lo | (hi << 4))

    if len(raw) != 0x80:
        raise SystemExit(f"Packed PMD shadow must be 0x80 bytes, got {len(raw)}")
    xs = [x for x, _ in used]
    ys = [y for _, y in used]
    return raw, [min(xs), min(ys), max(xs), max(ys)]


def emit_shadow_c(
    path: Path,
    target: dict[str, str],
    manifest: dict[str, object],
) -> dict[str, object]:
    species = target["species"]
    variant = target["variant"]
    prefix = f"Pmd{c_symbol(species)}{c_symbol(variant.title())}GroundShadow"

    idle_frame = manifest["actions"]["Idle"]["frames"][0]
    idle_shadow = manifest["grounding"]["source_shadow_records"]["Idle"][0]
    source_center = [int(v) for v in idle_shadow["center"]]
    mask_pixels = [[int(x), int(y)] for x, y in idle_shadow["mask_pixels"]]
    raw, obj_bbox = pack_shadow_4bpp(mask_pixels, source_center)

    canvas_center = [
        source_center[0] + int(idle_frame["paste_x"]),
        source_center[1] + int(idle_frame["paste_y"]),
    ]
    target_center = [int(v) for v in manifest["grounding"]["shadow_center_target"]]
    if canvas_center != target_center:
        raise SystemExit(f"{species} Idle0 PMD shadow center mismatch: {canvas_center} != {target_center}")
    if int(idle_frame.get("presentation_dy", 0)) != 0:
        raise SystemExit(f"{species} Idle0 ground authority unexpectedly has presentationY != 0")

    sprite_offset = [canvas_center[0] - BODY_CANVAS // 2, canvas_center[1] - BODY_CANVAS // 2]
    bytes_lines = []
    for i in range(0, len(raw), 16):
        bytes_lines.append("    " + ", ".join(f"0x{v:02X}" for v in raw[i:i + 16]) + ",")

    lines = [
        "/* Auto-generated authentic PMDCollab ground shadow mask. */",
        f"/* source=SpriteCollab sprite/{target['spritecollab_id']}/Idle-Shadow.png @ {SPRITECOLLAB_REV} */",
        f"/* direction={target['direction']} frame=0 ShadowSize={manifest['shadow']['shadow_size']} */",
        "/* Palette index 0 is transparent; index 1 uses SoulGold's loaded shadow palette. */",
        '#include "global.h"',
        "",
        f"const u8 g{prefix}Gfx[0x80] __attribute__((aligned(4))) =",
        "{",
        *bytes_lines,
        "};",
        f"const s8 g{prefix}XOffset = {sprite_offset[0]};",
        f"const s8 g{prefix}YOffset = {sprite_offset[1]};",
        f"const u8 g{prefix}ShadowSize = {int(manifest['shadow']['shadow_size'])};",
        "",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")

    return {
        "source_action": "Idle",
        "source_frame": 0,
        "source_center": source_center,
        "source_mask_bbox": idle_shadow["mask_bbox"],
        "source_mask_pixel_count": int(idle_shadow["mask_pixel_count"]),
        "shadow_size": int(manifest["shadow"]["shadow_size"]),
        "canvas_center": canvas_center,
        "body_sprite_base_offset": sprite_offset,
        "obj_size": [SHADOW_OBJ_W, SHADOW_OBJ_H],
        "obj_mask_bbox": obj_bbox,
        "gfx_bytes": len(raw),
        "palette_indices": [0, 1],
    }


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    spritecollab = args.spritecollab.resolve()
    soulgold = args.soulgold.resolve()
    out = args.output.resolve()
    framework = args.framework_root.resolve()
    require_revision(spritecollab, SPRITECOLLAB_REV, "SpriteCollab")
    require_revision(soulgold, SOULGOLD_REV, "SoulGold")

    if out.exists():
        shutil.rmtree(out)
    work = out / "work"
    staging = out / "staging"
    work.mkdir(parents=True)
    (staging / "src").mkdir(parents=True)

    converter = framework / "tools" / "convert_soulgold_g3r5.py"
    remapper = framework / "tools" / "pmd_gba_remap_host_palette.py"
    emitter = framework / "tools" / "emit_soulgold_g3r5_c.py"
    action_arg = ",".join(ACTIONS)

    summary: dict[str, object] = {
        "phase": "G3R5_PMD_SHADOW_GROUND_AUTHORITY",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "actions": list(ACTIONS),
        "body_canvas_policy": "G3R4_CLIP_SAFE_GREEN_BODY_CENTER",
        "battle_grounding_policy": "PMD_SHADOW_CENTER_BASELINE_TO_IDLE0",
        "shadow_policy": "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK",
        "shadow_render_policy": "Idle0 selected Shadow.png component mask packed to 32x8 4bpp OBJ",
        "targets": {},
    }

    for target in TARGETS:
        species = target["species"]
        slug = target["slug"]
        variant = target["variant"]
        direction = target["direction"]
        species_dir = spritecollab / "sprite" / target["spritecollab_id"]
        host_palette = soulgold / "graphics" / "pokemon" / slug / "normal.pal"
        source_audit = audit_directional_body_source(species_dir, direction)
        anchor_x, anchor_y, legal_anchor = resolve_species_anchor(source_audit)
        variant_dir = work / f"{slug}_{variant}"

        run([
            sys.executable, str(converter),
            "--source", str(species_dir),
            "--species", species,
            "--national-dex", target["dex"],
            "--actions", action_arg,
            "--direction", direction,
            "--anchor-x", str(anchor_x),
            "--anchor-y", str(anchor_y),
            "--source-revision", SPRITECOLLAB_REV,
            "--source-repo-path", f"sprite/{target['spritecollab_id']}",
            "--output", str(variant_dir),
            "--host-asset-root", f"graphics/pmd/{slug}/{variant}",
        ])
        run([sys.executable, str(remapper), "--frames-root", str(variant_dir), "--host-palette", str(host_palette)])

        generated_c = staging / "src" / f"pmd_{slug}_{variant}_ambient.c"
        run([
            sys.executable, str(emitter),
            "--ir", str(variant_dir / "manifest.ir.json"),
            "--output", str(generated_c),
            "--variant", variant,
            "--asset-root", f"graphics/pmd/{slug}/{variant}",
        ])
        copy_variant_assets(variant_dir, staging / "graphics" / "pmd" / slug / variant)

        manifest = json.loads((variant_dir / "manifest.ir.json").read_text(encoding="utf-8"))
        if manifest["grounding"]["battle_vertical_authority"] != "PMD_SHADOW_CENTER_BASELINE":
            raise SystemExit(f"{species} lost PMD shadow-center grounding authority")
        if manifest["shadow"]["policy"] != "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK":
            raise SystemExit(f"{species} lost authentic PMD shadow contract")

        target_y = int(manifest["grounding"]["shadow_center_target"][1])
        after: list[int] = []
        for action in ACTIONS:
            centers = manifest["grounding"]["final_shadow_center_before_correction"][action]
            frames = manifest["actions"][action]["frames"]
            for center, frame in zip(centers, frames):
                after.append(int(center[1]) + int(frame["presentation_dy"]))
        if not all(v == target_y for v in after):
            raise SystemExit(f"{species} PMD shadow-ground stabilization invariant failed: {after} vs {target_y}")

        shadow_c = staging / "src" / f"pmd_{slug}_{variant}_shadow.c"
        shadow_asset = emit_shadow_c(shadow_c, target, manifest)

        summary["targets"][f"{species}_{variant}"] = {
            "species": species,
            "variant": variant,
            "direction": direction,
            "resolved_body_anchor": [anchor_x, anchor_y],
            "legal_anchor_intersection": legal_anchor,
            "shadow_center_target": manifest["grounding"]["shadow_center_target"],
            "shadow_ground_correction_range": manifest["g3r5_shadow_ground_correction_range"],
            "shadow_ground_corrections": manifest["grounding"]["presentation_corrections_y"],
            "shadow_asset": shadow_asset,
            "source_audit": source_audit,
        }

    (out / "G3R5_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared SoulGold G3R5 PMD shadow-ground staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
