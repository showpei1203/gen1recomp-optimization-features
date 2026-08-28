#!/usr/bin/env python3
"""Prepare SoulGold G3R5 two-sided grounded PMD assets."""

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
CANVAS = 64

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
        if anim.width < w * frames or anim.height < h * len(DIRECTIONS):
            raise SystemExit(f"{action} body sheet is not a full directional sheet")
        centers = []
        for i in range(frames):
            crop = offsets.crop((i * w, row * h, (i + 1) * w, (row + 1) * h))
            centers.append(list(green_center(crop)))
        audit["actions"][action] = {
            "frame_width": w,
            "frame_height": h,
            "frame_count": frames,
            "green_body_centers": centers,
        }
    return audit


def resolve_species_anchor(source_audit: dict[str, object]) -> tuple[int, int, dict[str, list[int]]]:
    x_lo, y_lo = 0, 0
    x_hi, y_hi = CANVAS, CANVAS
    for rec in source_audit["actions"].values():
        w = rec["frame_width"]
        h = rec["frame_height"]
        if w > CANVAS or h > CANVAS:
            raise SystemExit(f"Selected body frame exceeds {CANVAS}x{CANVAS}: {w}x{h}")
        for cx, cy in rec["green_body_centers"]:
            x_lo = max(x_lo, cx)
            y_lo = max(y_lo, cy)
            x_hi = min(x_hi, cx + CANVAS - w)
            y_hi = min(y_hi, cy + CANVAS - h)
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
        "phase": "G3R5_GROUND_CONTACT_SHADOW_OWNERSHIP",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "actions": list(ACTIONS),
        "body_canvas_policy": "G3R4_CLIP_SAFE_GREEN_BODY_CENTER",
        "battle_grounding_policy": "ROBUST_OPAQUE_SUPPORT_BASELINE_TO_IDLE0",
        "shadow_policy": "SEPARATE_PMD_OWNED_32X8_GROUND_OBJ",
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
        if manifest["grounding"]["battle_vertical_authority"] != "ROBUST_OPAQUE_SUPPORT_BASELINE":
            raise SystemExit(f"{species} lost G3R5 support-baseline authority")
        if manifest["shadow"]["policy"] != "SEPARATE_PMD_OWNED_32X8_GROUND_OBJ":
            raise SystemExit(f"{species} lost G3R5 shadow contract")
        all_after = []
        target_y = manifest["grounding"]["support_target_y"]
        for action in ACTIONS:
            for before, frame in zip(
                manifest["grounding"]["final_support_before_correction"][action],
                manifest["actions"][action]["frames"],
            ):
                all_after.append(before + frame["presentation_dy"])
        if not all(v == target_y for v in all_after):
            raise SystemExit(f"{species} support stabilization invariant failed: {all_after} vs {target_y}")

        summary["targets"][f"{species}_{variant}"] = {
            "species": species,
            "variant": variant,
            "direction": direction,
            "resolved_body_anchor": [anchor_x, anchor_y],
            "legal_anchor_intersection": legal_anchor,
            "support_target_y": target_y,
            "support_correction_range": manifest["g3r5_support_correction_range"],
            "support_corrections": manifest["grounding"]["presentation_corrections_y"],
            "source_audit": source_audit,
        }

    (out / "G3R5_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"Prepared SoulGold G3R5 grounded staging bundle: {staging}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
