#!/usr/bin/env python3
"""SoulGold G3R4 regression-recovery PMD body converter.

G3R4 deliberately restores the visually accepted G2 body geometry while
preserving the later strict directional/species work:
- selected battle actions must come from real eight-direction PMD sheets;
- body frames use PMD Offsets.png green body-center normalization per frame;
- PMD Shadow.png is NOT composited into the body OBJ;
- runtime presentation offsets stay zero;
- SpriteCollab CopyOf aliases may legally omit Index, while real actions may not.

The rejected G3R2/G3R3 experiment anchored the whole body+shadow tile to the PMD
shadow origin. Runtime evidence showed that this exposed raw internal vertical
body movement as battlefield bobbing. Ground shadow will return as an
independent layer after the body renderer is stable again.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

import pmd_gba_converter as base


def parse_anim_data_g3r4(path: Path):
    root = ET.parse(path).getroot()
    actions = {}
    for anim in root.findall("./Anims/Anim"):
        name_node = anim.find("Name")
        if name_node is None or name_node.text is None or not name_node.text.strip():
            raise ValueError("AnimData.xml contains an Anim without Name")
        name = name_node.text.strip()
        copy_node = anim.find("CopyOf")
        copy_of = copy_node.text.strip() if copy_node is not None and copy_node.text and copy_node.text.strip() else None
        index_node = anim.find("Index")
        if index_node is None or index_node.text is None or not index_node.text.strip():
            if copy_of is None:
                raise ValueError(f"AnimData.xml action {name} has neither Index nor CopyOf")
            index = -1
        else:
            index = int(index_node.text.strip())

        durations = tuple(
            int(n.text.strip())
            for n in anim.findall("./Durations/Duration")
            if n.text and n.text.strip()
        )
        actions[name] = base.ActionMeta(
            name=name,
            index=index,
            copy_of=copy_of,
            frame_width=base._text_int(anim, "FrameWidth"),
            frame_height=base._text_int(anim, "FrameHeight"),
            durations=durations,
            rush_frame=base._text_int(anim, "RushFrame"),
            hit_frame=base._text_int(anim, "HitFrame"),
            return_frame=base._text_int(anim, "ReturnFrame"),
        )
    if not actions:
        raise ValueError(f"No animations found in {path}")
    return actions


def convert_g3r4(args) -> int:
    rc = base.convert(args)
    if args.metadata_only:
        return rc

    manifest_path = args.output.resolve() / "manifest.ir.json"
    data = json.loads(manifest_path.read_text(encoding="utf-8"))
    anchor = data["body_profile"]["anchor_target"]

    for action_name, action in data["actions"].items():
        for frame in action["frames"]:
            if frame["source_center_x"] + frame["paste_x"] != anchor["x"]:
                raise ValueError(f"{action_name} frame {frame['index']} lost body-center X authority")
            if frame["source_center_y"] + frame["paste_y"] != anchor["y"]:
                raise ValueError(f"{action_name} frame {frame['index']} lost body-center Y authority")
            if frame["presentation_dx"] != 0 or frame["presentation_dy"] != 0:
                raise ValueError(f"{action_name} frame {frame['index']} has nonzero runtime offset")

    data["grounding"] = {
        "body_anchor_policy": "PMD_BODY_CENTER_PER_FRAME_G2_RESTORED",
        "body_center_source": "PMDCollab per-action *-Offsets.png green marker",
        "runtime_presentation_offset": [0, 0],
        "reason": "G3R3 runtime rejection: fixed whole-tile shadow-origin anchoring produced visible body bobbing",
    }
    data["shadow"] = {
        "included_in_body_frames": False,
        "policy": "SEPARATE_GROUND_LAYER_REQUIRED_AFTER_BODY_RECOVERY",
        "status": "DEFERRED_FROM_G3R4_REGRESSION_RECOVERY",
    }
    manifest_path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return rc


def main() -> int:
    base.parse_anim_data = parse_anim_data_g3r4
    parser = base.build_parser()
    parser.description = __doc__
    args = parser.parse_args()
    try:
        return convert_g3r4(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
