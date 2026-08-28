#!/usr/bin/env python3
"""SoulGold G3R5 PMD battle-grounding converter.

G3R4 proved that PMD green body-center normalization is not the same thing as
battlefield grounding: Cyndaquil still visibly bobbed while Marill remained
stable.  G3R5 keeps the clip-safe G3R4 body canvas but adds a battle-specific
vertical presentation stabilizer derived from the opaque support row of every
source frame.

The first Idle frame is the authority.  Every ambient frame receives only the
small presentationY correction needed to keep its robust body support baseline
on that same battlefield Y.  The body pixels are not re-authored and runtime
ownership remains unchanged.  Shadow is a separate OBJ owned by the adapter.
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
MAX_EXPECTED_AMBIENT_CORRECTION = 8


def robust_support_y(frame: Image.Image) -> int:
    """Return the lowest visually meaningful opaque row.

    Requiring at least three opaque pixels rejects one-pixel flame/tail noise
    while still tracking small Pokémon feet.  This is intentionally a battle
    presentation metric, not a replacement for PMDCollab's authored offsets.
    """
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
        if action_name not in metas:
            raise ValueError(f"Missing PMD action metadata: {action_name}")
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


def convert_g3r5(args) -> int:
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
            supports[action_name][i] + frame["paste_y"]
            for i, frame in enumerate(frames)
        ]

    if "Idle" not in final_supports or not final_supports["Idle"]:
        raise ValueError("G3R5 requires Idle frame 0 as support-baseline authority")
    target_support_y = final_supports["Idle"][0]

    correction_values = []
    for action_name in action_names:
        for i, frame in enumerate(data["actions"][action_name]["frames"]):
            dy = target_support_y - final_supports[action_name][i]
            if abs(dy) > MAX_EXPECTED_AMBIENT_CORRECTION:
                raise ValueError(
                    f"{action_name} frame {i} requires suspicious support correction {dy}px; "
                    "refusing to hide a likely geometry bug"
                )
            frame["presentation_dy"] = dy
            correction_values.append(dy)

    data["grounding"] = {
        "body_canvas_policy": "G3R4_CLIP_SAFE_GREEN_BODY_CENTER",
        "battle_vertical_authority": "ROBUST_OPAQUE_SUPPORT_BASELINE",
        "support_min_opaque_pixels": SUPPORT_MIN_PIXELS,
        "support_target_y": target_support_y,
        "support_source_rows": supports,
        "final_support_before_correction": final_supports,
        "presentation_corrections_y": {
            action: [f["presentation_dy"] for f in data["actions"][action]["frames"]]
            for action in action_names
        },
        "runtime_presentation_x": 0,
        "reason": "G3R4 human runtime video: player Cyndaquil visibly bobbed while opponent Marill did not",
    }
    data["shadow"] = {
        "included_in_body_frames": False,
        "policy": "SEPARATE_PMD_OWNED_32X8_GROUND_OBJ",
        "status": "G3R5_RUNTIME_OWNERSHIP",
        "ground_relation": "shadow follows battler base x/y, not animated presentation x2/y2",
    }
    data["g3r5_support_correction_range"] = [min(correction_values), max(correction_values)] if correction_values else [0, 0]
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
