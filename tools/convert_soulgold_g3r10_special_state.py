#!/usr/bin/env python3
"""Convert one PMDCollab special-state action for SoulGold G3R10.

G3R9 established that special states do not share one view rule. Each action
resolves its own Anim / Offsets / Shadow geometry. Directionless source art is
kept directionless; an 8-row source uses the requested battle-facing row.

This converter preserves every visible source pixel on a 64x64 GBA body canvas,
uses the authored green body-center marker, and records the source-view contract
in IR. Combat/status authority is not part of conversion.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from PIL import Image

import convert_soulgold_g3r4 as g3r4
import convert_soulgold_g3r6b_attack as lossless
import convert_soulgold_g3r8_sleep as view
import pmd_gba_converter as base

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
FORMAT = "PMD_GBA_SOULGOLD_G3R10_SPECIAL_STATE_IR"
SUPPORTED_ACTIONS = ("Sleep", "EventSleep", "Wake")
FOLDERS = {"Sleep": "sleep", "EventSleep": "event_sleep", "Wake": "wake"}
SEMANTIC_ROLES = {
    "Sleep": "persistent_sleep_status_body",
    "EventSleep": "sleep_entry_transition_body",
    "Wake": "wake_transition_body_source_ready",
}


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--source", type=Path, required=True)
    ap.add_argument("--species", required=True)
    ap.add_argument("--national-dex", required=True)
    ap.add_argument("--action", required=True, choices=SUPPORTED_ACTIONS)
    ap.add_argument("--direction", required=True, choices=base.DIRECTIONS)
    ap.add_argument("--anchor-x", type=int, required=True)
    ap.add_argument("--anchor-y", type=int, required=True)
    ap.add_argument("--source-revision", default=SPRITECOLLAB_REV)
    ap.add_argument("--source-repo-path", required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--host-asset-root", required=True)
    args = ap.parse_args()

    source = args.source.resolve()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=True)

    metas = g3r4.parse_anim_data_g3r4(source / "AnimData.xml")
    action = base.resolve_action(args.action, metas)
    anim = base._open_rgba(source / f"{action.source_action}-Anim.png")
    offsets = base._open_rgba(source / f"{action.source_action}-Offsets.png")
    resolved = view.resolve_sleep_layout(source, action, args.direction)
    anchor = (args.anchor_x, args.anchor_y)

    normalized = []
    records = []
    for i, duration in enumerate(action.durations):
        frame = view.crop_resolved_frame(anim, action, resolved, i)
        off = view.crop_resolved_frame(offsets, action, resolved, i)
        center = base.body_center_from_offsets(off)
        canvas, audit = lossless.normalize_visible_pixels(frame, center, anchor)
        normalized.append(canvas)
        records.append({
            "index": i,
            "duration": int(duration),
            "source_center_x": int(center[0]),
            "source_center_y": int(center[1]),
            "paste_x": int(audit["paste_x"]),
            "paste_y": int(audit["paste_y"]),
            "presentation_dx": 0,
            "presentation_dy": 0,
            "opaque_source_pixels": int(audit["opaque_source_pixels"]),
            "opaque_copied_pixels": int(audit["opaque_copied_pixels"]),
            "opaque_destination_bbox": audit["opaque_destination_bbox"],
            "transparent_source_pixels_outside_destination": int(audit["transparent_source_pixels_outside_destination"]),
            "visible_pixel_conservation": True,
        })

    palette = base.quantized_palette(normalized)
    folder = FOLDERS[args.action]
    action_dir = out / folder
    action_dir.mkdir(exist_ok=True)
    for i, canvas in enumerate(normalized):
        base.to_indexed_gba(canvas, palette).save(action_dir / f"frame_{i:02d}.png", optimize=False)
    base.write_jasc_palette(out / "palette.pal", palette)

    manifest = {
        "format": FORMAT,
        "species": {"name": args.species, "national_dex": int(args.national_dex)},
        "source": {
            "revision": args.source_revision,
            "repo_path": args.source_repo_path,
            "action": args.action,
            "source_action": action.source_action,
        },
        "body_profile": {
            "anchor_target": {"x": anchor[0], "y": anchor[1]},
            "policy": "PMDCOLLAB_GREEN_BODY_CENTER_VISIBLE_PIXELS_100_PERCENT_CONSERVED",
        },
        "special_state_view": resolved,
        "actions": {
            args.action: {
                "name": args.action,
                "source_action": action.source_action,
                "semantic_role": SEMANTIC_ROLES[args.action],
                "direction": resolved["applied_source_direction"],
                "requested_battle_direction": args.direction,
                "source_layout": resolved["layout"],
                "source_row": int(resolved["row"]),
                "view_policy": resolved["view_policy"],
                "source_frame_width": action.frame_width,
                "source_frame_height": action.frame_height,
                "folder": folder,
                "loop": args.action == "Sleep",
                "rush_frame": action.rush_frame,
                "hit_frame": action.hit_frame,
                "return_frame": action.return_frame,
                "frames": records,
            }
        },
        "conversion": {
            "destination_canvas": [64, 64],
            "cropped_visible_pixels": 0,
            "scaled": False,
            "resampled": False,
            "visible_pixel_conservation_required": True,
        },
        "host_asset_root": args.host_asset_root,
    }
    (out / "manifest.ir.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")

    if any(r["opaque_source_pixels"] != r["opaque_copied_pixels"] for r in records):
        raise SystemExit(f"{args.species}/{args.action}: visible pixel conservation failed")
    print(
        f"G3R10 {args.action} {args.species}: {action.frame_width}x{action.frame_height}, "
        f"frames={len(records)}, durations={[int(x) for x in action.durations]}"
    )
    print(
        "layout", resolved["layout"], "requested", args.direction,
        "applied", resolved["applied_source_direction"], "row", resolved["row"]
    )
    print("visible pixel conservation PASS")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
