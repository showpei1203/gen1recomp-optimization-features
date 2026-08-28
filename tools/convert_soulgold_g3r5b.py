#!/usr/bin/env python3
"""SoulGold G3R5B runtime-proven residual body-ground correction.

G3R4B already removed native OAM bobbing with all PMD body presentation offsets
at zero. Human runtime then isolated one residual defect: Cyndaquil UpRight Idle
frame 1 appears 1 px too low. G3R5 incorrectly tried to use Shadow.png positions
to solve body grounding and emitted +1 for that same frame.

G3R5B stops using Shadow.png to move the body. It restores the G3R4B zero-offset
body baseline for every ambient frame and applies exactly one evidence-backed
visual override: Cyndaquil/UpRight/Idle/frame1 = -1 px. PMD Shadow.png remains
exclusive authority for the separate shadow layer.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import convert_soulgold_g3r4 as g3r4
import pmd_gba_converter as base


def convert_g3r5b(args) -> int:
    rc = g3r4.convert_g3r4(args)
    if args.metadata_only:
        return rc

    manifest_path = args.output.resolve() / "manifest.ir.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))

    # G3R4B body presentation was structurally stable: no runtime x2/y2 offsets.
    # Keep that baseline rather than conflating Shadow.png movement with body movement.
    for action in data["actions"].values():
        for frame in action["frames"]:
            frame["presentation_dx"] = 0
            frame["presentation_dy"] = 0

    overrides = []
    if data["species"]["name"] == "Cyndaquil" and args.direction == "UpRight":
        idle = data["actions"].get("Idle")
        if idle is None or len(idle["frames"]) < 2:
            raise ValueError("Cyndaquil G3R5B requires Idle frame 1")
        idle["frames"][1]["presentation_dy"] = -1
        overrides.append({
            "action": "Idle",
            "frame": 1,
            "presentation_dy": -1,
            "evidence": "2026-08-28 G3R4B/G3R5 human runtime: Idle second frame appears 1 px low",
        })

    corrections = {
        name: [int(f["presentation_dy"]) for f in rec["frames"]]
        for name, rec in data["actions"].items()
    }
    all_values = [v for values in corrections.values() for v in values]

    data["grounding"] = {
        "body_canvas_policy": "G3R4_CLIP_SAFE_GREEN_BODY_CENTER",
        "battle_vertical_authority": "G3R4B_ZERO_PLUS_RUNTIME_ACCEPTANCE_OVERRIDE",
        "shadow_png_may_move_body": False,
        "presentation_corrections_y": corrections,
        "runtime_acceptance_overrides": overrides,
        "reason": (
            "G3R5 runtime proved PMD Shadow.png is shadow-placement metadata, not body-ground motion authority; "
            "restore G3R4B zero body offsets and correct only the human-observed Cyndaquil Idle1 residual"
        ),
    }
    data["shadow"] = {
        "included_in_body_frames": False,
        "policy": "SEPARATE_AUTHENTIC_PMD_SHADOW_MASK_CENTERED_ON_BATTLE_X",
        "body_presentation_independent": True,
        "status": "G3R5B_RUNTIME_OWNERSHIP",
    }
    data["g3r5b_body_ground_correction_range"] = [min(all_values), max(all_values)] if all_values else [0, 0]
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
