#!/usr/bin/env python3
"""SoulGold G3R5 PMD shadow-grounding converter.

G3R4B fixed native OAM timing, but runtime review still showed one residual
~1px action-level ground shift on Cyndaquil. G3R5 keeps the G3R4 clip-safe
body canvas and derives the battlefield vertical correction from PMDCollab's
*-Shadow.png authority instead of inventing a foot/opaque-row heuristic.

PMD Shadow.png semantics:
- pure white marks the shadow/sprite center for each frame;
- green contributes the small shadow mask;
- red extends it to normal shadow size;
- blue extends it to large shadow size;
- AnimData.xml ShadowSize selects how many components are active.

The first Idle frame is the battlefield ground authority. Every ambient frame
receives only the bounded presentationY correction needed to keep the authored
PMD shadow center on that same battlefield Y after body-center normalization.
The shadow itself is rendered later as a separate PMD-owned OBJ; it is never
baked into the body frame.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

import convert_soulgold_g3r4 as g3r4
import pmd_gba_converter as base

DIRECTIONS = ["Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft"]
MAX_EXPECTED_AMBIENT_CORRECTION = 8

WHITE = (255, 255, 255, 255)
GREEN = (0, 255, 0, 255)
RED = (255, 0, 0, 255)
BLUE = (0, 0, 255, 255)
SHADOW_COMPONENTS = (WHITE, GREEN, RED, BLUE)


def parse_shadow_size(anim_xml: Path) -> int:
    root = ET.parse(anim_xml).getroot()
    text = root.findtext("ShadowSize")
    if text is None or not text.strip():
        raise ValueError(f"AnimData.xml lacks ShadowSize: {anim_xml}")
    value = int(text.strip())
    if value < 0 or value > 2:
        raise ValueError(f"Unsupported PMD ShadowSize {value}; expected 0..2")
    return value


def selected_shadow_colors(shadow_size: int) -> set[tuple[int, int, int, int]]:
    # SpriteCollab convention used by PMD tooling: white is always included,
    # then green for small, red for normal, blue for large.
    return set(SHADOW_COMPONENTS[: shadow_size + 2])


def shadow_frame_record(crop: Image.Image, shadow_size: int) -> dict[str, object]:
    rgba = crop.convert("RGBA")
    whites: list[tuple[int, int]] = []
    mask: list[tuple[int, int]] = []
    allowed = selected_shadow_colors(shadow_size)

    for y in range(rgba.height):
        for x in range(rgba.width):
            px = rgba.getpixel((x, y))
            if px == WHITE:
                whites.append((x, y))
            if px in allowed:
                mask.append((x, y))

    if not whites:
        raise ValueError("PMD Shadow frame has no pure-white center marker")
    if not mask:
        raise ValueError("PMD Shadow frame has no selected mask pixels")

    # Official/source sheets normally contain exactly one white pixel. Keep a
    # deterministic centroid fallback for multi-pixel markers instead of
    # silently choosing the first pixel.
    cx = int(round(sum(x for x, _ in whites) / len(whites)))
    cy = int(round(sum(y for _, y in whites) / len(whites)))
    xs = [x for x, _ in mask]
    ys = [y for _, y in mask]
    return {
        "center": [cx, cy],
        "white_pixel_count": len(whites),
        "mask_pixel_count": len(mask),
        "mask_bbox": [min(xs), min(ys), max(xs), max(ys)],
        "mask_pixels": [[x, y] for x, y in mask],
    }


def source_shadow_records(
    source: Path,
    direction: str,
    action_names: list[str],
) -> tuple[int, dict[str, list[dict[str, object]]]]:
    if direction not in DIRECTIONS:
        raise ValueError(f"Unsupported PMD direction: {direction}")

    row = DIRECTIONS.index(direction)
    metas = g3r4.parse_anim_data_g3r4(source / "AnimData.xml")
    shadow_size = parse_shadow_size(source / "AnimData.xml")
    out: dict[str, list[dict[str, object]]] = {}

    for action_name in action_names:
        if action_name not in metas:
            raise ValueError(f"Missing PMD action metadata: {action_name}")
        meta = metas[action_name]
        if meta.frame_width is None or meta.frame_height is None or not meta.durations:
            raise ValueError(f"PMD action lacks real geometry/durations: {action_name}")

        shadow_path = source / f"{action_name}-Shadow.png"
        if not shadow_path.is_file():
            raise ValueError(f"Missing PMD shadow authority: {shadow_path}")
        sheet = Image.open(shadow_path).convert("RGBA")
        w, h = meta.frame_width, meta.frame_height
        if sheet.width < w * len(meta.durations) or sheet.height < h * len(DIRECTIONS):
            raise ValueError(
                f"{action_name} Shadow sheet is {sheet.size}, expected at least "
                f"{w * len(meta.durations)}x{h * len(DIRECTIONS)}"
            )

        frames: list[dict[str, object]] = []
        for i in range(len(meta.durations)):
            crop = sheet.crop((i * w, row * h, (i + 1) * w, (row + 1) * h))
            rec = shadow_frame_record(crop, shadow_size)
            rec["frame_index"] = i
            frames.append(rec)
        out[action_name] = frames

    return shadow_size, out


def convert_g3r5(args) -> int:
    rc = g3r4.convert_g3r4(args)
    if args.metadata_only:
        return rc

    manifest_path = args.output.resolve() / "manifest.ir.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    action_names = list(data["actions"].keys())
    shadow_size, shadow_records = source_shadow_records(args.source.resolve(), args.direction, action_names)

    final_shadow_centers: dict[str, list[list[int]]] = {}
    for action_name in action_names:
        frames = data["actions"][action_name]["frames"]
        records = shadow_records[action_name]
        if len(frames) != len(records):
            raise ValueError(f"{action_name} shadow/frame count mismatch")
        final_shadow_centers[action_name] = []
        for frame, rec in zip(frames, records):
            sx, sy = rec["center"]
            final_shadow_centers[action_name].append([
                int(sx) + int(frame["paste_x"]),
                int(sy) + int(frame["paste_y"]),
            ])

    if "Idle" not in final_shadow_centers or not final_shadow_centers["Idle"]:
        raise ValueError("G3R5 requires Idle frame 0 as PMD shadow-ground authority")
    target_x, target_y = final_shadow_centers["Idle"][0]

    correction_values: list[int] = []
    for action_name in action_names:
        for i, frame in enumerate(data["actions"][action_name]["frames"]):
            # Horizontal body-center ownership remains G3R4. G3R5 fixes only the
            # runtime-observed vertical ground discontinuity.
            dy = target_y - final_shadow_centers[action_name][i][1]
            if abs(dy) > MAX_EXPECTED_AMBIENT_CORRECTION:
                raise ValueError(
                    f"{action_name} frame {i} requires suspicious PMD shadow-ground correction {dy}px; "
                    "refusing to hide a likely geometry/source mismatch"
                )
            frame["presentation_dx"] = 0
            frame["presentation_dy"] = dy
            correction_values.append(dy)

    data["grounding"] = {
        "body_canvas_policy": "G3R4_CLIP_SAFE_GREEN_BODY_CENTER",
        "battle_vertical_authority": "PMD_SHADOW_CENTER_BASELINE",
        "shadow_center_target": [target_x, target_y],
        "shadow_size": shadow_size,
        "source_shadow_records": shadow_records,
        "final_shadow_center_before_correction": final_shadow_centers,
        "presentation_corrections_y": {
            action: [int(f["presentation_dy"]) for f in data["actions"][action]["frames"]]
            for action in action_names
        },
        "runtime_presentation_x": 0,
        "reason": (
            "G3R4B human runtime: native OAM bobbing fixed, one residual Cyndaquil action-level ~1px "
            "ground shift remained; use PMDCollab Shadow.png center metadata as battlefield authority"
        ),
    }
    data["shadow"] = {
        "included_in_body_frames": False,
        "policy": "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK",
        "shadow_size": shadow_size,
        "component_semantics": "white center + green small + red normal + blue large per ShadowSize",
        "stable_visual_source": "Idle-Shadow.png frame 0 in selected battle direction",
        "ground_relation": "body base x/y plus authored Idle0 shadow-center offset; ignores PMD presentation x2/y2",
        "status": "G3R5_RUNTIME_OWNERSHIP",
    }
    data["g3r5_shadow_ground_correction_range"] = (
        [min(correction_values), max(correction_values)] if correction_values else [0, 0]
    )
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return rc


def main() -> int:
    base.parse_anim_data = g3r4.parse_anim_data_g3r4
    parser = base.build_parser()
    parser.description = __doc__
    args = parser.parse_args()
    try:
        return convert_g3r5(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
