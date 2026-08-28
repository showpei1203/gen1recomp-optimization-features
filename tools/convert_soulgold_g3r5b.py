#!/usr/bin/env python3
"""SoulGold G3R5B body-ground stabilizer.

G3R5 runtime proved that PMDCollab Shadow.png positions must not be used to move
the body: Cyndaquil Idle frame 1 was emitted with presentationY=+1 and visibly
stepped downward. Shadow.png describes shadow placement, not body grounding.

G3R5B therefore keeps G3R4 body-center normalization, derives a bounded visual
support baseline from the actual Anim.png body pixels, and leaves PMD shadow
metadata exclusively to the separate shadow layer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

from PIL import Image

import convert_soulgold_g3r4 as g3r4
import pmd_gba_converter as base

DIRECTIONS = ["Down", "DownRight", "Right", "UpRight", "Up", "UpLeft", "Left", "DownLeft"]
SUPPORT_MIN_PIXELS = 3
MAX_EXPECTED_AMBIENT_CORRECTION = 4


def robust_support_y(frame: Image.Image) -> int:
    rgba = frame.convert("RGBA")
    for y in range(rgba.height - 1, -1, -1):
        count = 0
        for x in range(rgba.width):
            if rgba.getpixel((x, y))[3] != 0:
                count += 1
                if count >= SUPPORT_MIN_PIXELS:
                    return y
    raise ValueError("PMD source frame has no robust opaque support row")


def source_support_rows(source: Path, direction: str, action_names: list[str]) -> dict[str, list[int]]:
    if direction not in DIRECTIONS:
        raise ValueError(f"Unsupported PMD direction: {direction}")
    row = DIRECTIONS.index(direction)
    metas = g3r4.parse_anim_data_g3r4(source / "AnimData.xml")
    out: dict[str, list[int]] = {}

    for action_name in action_names:
        meta = metas[action_name]
        if meta.frame_width is None or meta.frame_height is None or not meta.durations:
            raise ValueError(f"PMD action lacks real geometry/durations: {action_name}")
        sheet = Image.open(source / f"{action_name}-Anim.png").convert("RGBA")
        w, h = meta.frame_width, meta.frame_height
        rows = []
        for i in range(len(meta.durations)):
            crop = sheet.crop((i * w, row * h, (i + 1) * w, (row + 1) * h))
            rows.append(robust_support_y(crop))
        out[action_name] = rows
    return out


def convert_g3r5b(args) -> int:
    rc = g3r4.convert_g3r4(args)
    if args.metadata_only:
        return rc

    manifest_path = args.output.resolve() / "manifest.ir.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    action_names = list(data["actions"].keys())
    supports = source_support_rows(args.source.resolve(), args.direction, action_names)

    final_supports: dict[str, list[int]] = {}
    for action_name in action_names:
        frames = data["actions"][action_name]["frames"]
        if len(frames) != len(supports[action_name]):
            raise ValueError(f"{action_name} support/frame count mismatch")
        final_supports[action_name] = [
            supports[action_name][i] + int(frame["paste_y"])
            for i, frame in enumerate(frames)
        ]

    target_y = final_supports["Idle"][0]
    corrections: list[int] = []
    for action_name in action_names:
        for i, frame in enumerate(data["actions"][action_name]["frames"]):
            dy = target_y - final_supports[action_name][i]
            if abs(dy) > MAX_EXPECTED_AMBIENT_CORRECTION:
                raise ValueError(
                    f"{action_name} frame {i} requires suspicious body-ground correction {dy}px"
                )
            frame["presentation_dx"] = 0
            frame["presentation_dy"] = dy
            corrections.append(dy)

    data["grounding"] = {
        "body_canvas_policy": "G3R4_CLIP_SAFE_GREEN_BODY_CENTER",
        "battle_vertical_authority": "ROBUST_BODY_SUPPORT_BASELINE",
        "support_min_opaque_pixels": SUPPORT_MIN_PIXELS,
        "support_target_y": target_y,
        "support_source_rows": supports,
        "final_support_before_correction": final_supports,
        "presentation_corrections_y": {
            action: [int(f["presentation_dy"]) for f in data["actions"][action]["frames"]]
            for action in action_names
        },
        "shadow_png_may_move_body": False,
        "reason": "G3R5 runtime proved Shadow.png-derived body offsets caused Cyndaquil Idle frame 1 downward step",
    }
    data["shadow"] = {
        "included_in_body_frames": False,
        "policy": "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK_CENTERED_ON_BATTLE_X",
        "body_presentation_independent": True,
        "status": "G3R5B_RUNTIME_OWNERSHIP",
    }
    data["g3r5b_body_ground_correction_range"] = [min(corrections), max(corrections)] if corrections else [0, 0]
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return rc


def main() -> int:
    base.parse_anim_data = g3r4.parse_anim_data_g3r4
    parser = base.build_parser()
    parser.description = __doc__
    args = parser.parse_args()
    try:
        return convert_g3r5b(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
