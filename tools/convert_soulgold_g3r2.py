#!/usr/bin/env python3
"""SoulGold G3R2 PMD converter: directional body + authentic shadow + grounded tile-space.

G3/G3R1 incorrectly normalized every frame from the green body-center marker in
Offsets.png. PMD's own preview/render semantics keep body and shadow in one tile
coordinate system; a body-center change inside an animation is not permission
to move the whole tile. Per-frame normalization therefore created artificial
vertical/horizontal drift and made the shadow feel detached from the ground.

G3R2 rules for grounded battle ambient actions:
- composite the authentic PMD Shadow.png underneath the body;
- preserve all body/shadow geometry inside the raw PMD frame tile;
- derive one translation per ACTION from its frame-0 shadow ground anchor;
- use the exact same translation for every frame of that action;
- align every action's shadow center/bottom to the HOME (Idle frame 0) ground
  position that the previously accepted 32,44 profile produced;
- Offsets.png body-center data remains metadata only and never drives a
  per-frame presentation translation.

This wrapper leaves the sealed generic GBA converter unchanged.
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

import pmd_gba_converter as base

_original_open_rgba = base._open_rgba
_original_normalize_frame = base.normalize_frame
_shadow_size_cache: dict[Path, int] = {}
_action_sequence: list[str] = []
_action_translations: dict[str, tuple[int, int]] = {}
_alignment_meta: dict[str, object] = {}
_normalize_call_index = 0
_include_shadow = True


def shadow_size_for_species(source_dir: Path) -> int:
    source_dir = source_dir.resolve()
    if source_dir in _shadow_size_cache:
        return _shadow_size_cache[source_dir]
    root = ET.parse(source_dir / "AnimData.xml").getroot()
    node = root.find("ShadowSize")
    if node is None or node.text is None:
        raise ValueError(f"ShadowSize missing in {source_dir / 'AnimData.xml'}")
    value = int(node.text)
    if value < 0 or value > 2:
        raise ValueError(f"Invalid PMD ShadowSize={value}")
    _shadow_size_cache[source_dir] = value
    return value


def build_shadow_mask(shadow: Image.Image, shadow_size: int) -> Image.Image:
    src = shadow.convert("RGBA")
    out = Image.new("RGBA", src.size, (0, 0, 0, 0))
    spx = src.load()
    dpx = out.load()
    for y in range(src.height):
        for x in range(src.width):
            r, g, b, a = spx[x, y]
            if a != 255:
                continue
            active = g == 255 or (r == 255 and shadow_size > 0) or (b == 255 and shadow_size > 1)
            if active:
                dpx[x, y] = (0, 0, 0, 255)
    return out


def active_shadow_bbox(shadow_crop: Image.Image, shadow_size: int) -> tuple[int, int, int, int]:
    mask = build_shadow_mask(shadow_crop, shadow_size)
    pts = [
        (x, y)
        for y in range(mask.height)
        for x in range(mask.width)
        if mask.getpixel((x, y))[3] > 0
    ]
    if not pts:
        raise ValueError("PMD shadow frame has no active marker pixels for configured ShadowSize")
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def open_rgba_g3r2(path: Path) -> Image.Image:
    body = _original_open_rgba(path)
    if not _include_shadow or not path.name.endswith("-Anim.png"):
        return body
    shadow_path = path.with_name(path.name.replace("-Anim.png", "-Shadow.png"))
    if not shadow_path.is_file():
        raise FileNotFoundError(f"Missing PMD shadow sheet for battle asset: {shadow_path}")
    shadow = _original_open_rgba(shadow_path)
    if shadow.size != body.size:
        raise ValueError(f"PMD shadow/body layout mismatch: body={body.size}, shadow={shadow.size}")
    mask = build_shadow_mask(shadow, shadow_size_for_species(path.parent))
    combined = Image.new("RGBA", body.size, (0, 0, 0, 0))
    combined.alpha_composite(mask)
    combined.alpha_composite(body)
    return combined


def _round_half_pixel(delta2: int) -> int:
    # Bboxes may have half-pixel centers. Pick the deterministic nearest integer,
    # with halves away from zero. The chosen value is action-constant.
    if delta2 >= 0:
        return (delta2 + 1) // 2
    return -((-delta2 + 1) // 2)


def prepare_ground_alignment(args) -> None:
    global _action_sequence, _action_translations, _alignment_meta, _normalize_call_index

    source = args.source.resolve()
    actions = base.parse_anim_data(source / "AnimData.xml")
    wanted = [x.strip() for x in args.actions.split(",") if x.strip()]
    resolved = [base.resolve_action(name, actions) for name in wanted]
    if not resolved:
        raise ValueError("No actions selected")

    home = next((a for a in resolved if a.requested_name == "Idle"), resolved[0])
    direction = args.direction
    shadow_size = shadow_size_for_species(source)

    # Preserve the accepted HOME world placement, but only as a ONE-TIME ground
    # reference. The old body-center translation must never be recomputed for
    # later HOME frames.
    home_offsets_sheet = _original_open_rgba(source / f"{home.source_action}-Offsets.png")
    home_offsets = base.crop_direction_frame(home_offsets_sheet, home, direction, 0)
    home_center = base.body_center_from_offsets(home_offsets)
    home_old_dx = args.anchor_x - home_center[0]
    home_old_dy = args.anchor_y - home_center[1]

    home_shadow_sheet = _original_open_rgba(source / f"{home.source_action}-Shadow.png")
    home_shadow = base.crop_direction_frame(home_shadow_sheet, home, direction, 0)
    hx0, hy0, hx1, hy1 = active_shadow_bbox(home_shadow, shadow_size)
    target_center_x2 = hx0 + hx1 + 2 * home_old_dx
    target_ground_y = hy1 + home_old_dy

    sequence: list[str] = []
    translations: dict[str, tuple[int, int]] = {}
    action_meta: dict[str, object] = {}

    for action in resolved:
        shadow_sheet = _original_open_rgba(source / f"{action.source_action}-Shadow.png")
        shadow0 = base.crop_direction_frame(shadow_sheet, action, direction, 0)
        sx0, sy0, sx1, sy1 = active_shadow_bbox(shadow0, shadow_size)
        dx = _round_half_pixel(target_center_x2 - (sx0 + sx1))
        dy = target_ground_y - sy1

        if dx < 0 or dy < 0 or dx + action.frame_width > base.CANVAS_W or dy + action.frame_height > base.CANVAS_H:
            raise ValueError(
                f"G3R2 action ground placement clips {action.requested_name}: "
                f"frame={action.frame_width}x{action.frame_height}, paste=({dx},{dy})"
            )

        translations[action.requested_name] = (dx, dy)
        sequence.extend([action.requested_name] * len(action.durations))
        action_meta[action.requested_name] = {
            "frame0_shadow_bbox": [sx0, sy0, sx1, sy1],
            "paste_x": dx,
            "paste_y": dy,
            "translation_scope": "ACTION_CONSTANT",
        }

    _action_sequence = sequence
    _action_translations = translations
    _normalize_call_index = 0
    _alignment_meta = {
        "policy": "PMD_TILE_SPACE_ACTION_CONSTANT_SHADOW_GROUND_ANCHOR",
        "body_center_controls_translation": False,
        "home_action": home.requested_name,
        "home_frame": 0,
        "legacy_home_anchor_target": [args.anchor_x, args.anchor_y],
        "legacy_home_body_center": [home_center[0], home_center[1]],
        "target_shadow_center_x2": target_center_x2,
        "target_shadow_ground_y": target_ground_y,
        "actions": action_meta,
    }


def normalize_frame_action_constant(frame: Image.Image, body_center, anchor_target):
    del body_center, anchor_target
    global _normalize_call_index
    if _normalize_call_index >= len(_action_sequence):
        raise ValueError("G3R2 normalize call count exceeded prepared action sequence")
    action_name = _action_sequence[_normalize_call_index]
    _normalize_call_index += 1
    dx, dy = _action_translations[action_name]
    if frame.width > base.CANVAS_W or frame.height > base.CANVAS_H:
        raise ValueError(f"Source frame {frame.size} exceeds GBA single-OBJ canvas")
    if dx < 0 or dy < 0 or dx + frame.width > base.CANVAS_W or dy + frame.height > base.CANVAS_H:
        raise ValueError(f"G3R2 fixed placement clips {action_name}: frame={frame.size}, paste=({dx},{dy})")
    canvas = Image.new("RGBA", (base.CANVAS_W, base.CANVAS_H), (0, 0, 0, 0))
    canvas.alpha_composite(frame, (dx, dy))
    return canvas, dx, dy


def convert_g3r2(args) -> int:
    global _include_shadow
    _include_shadow = not args.no_shadow
    prepare_ground_alignment(args)
    base._open_rgba = open_rgba_g3r2
    base.normalize_frame = normalize_frame_action_constant
    rc = base.convert(args)
    if args.metadata_only:
        return rc

    manifest = args.output.resolve() / "manifest.ir.json"
    data = json.loads(manifest.read_text(encoding="utf-8"))
    data["grounding"] = _alignment_meta
    data["shadow"] = {
        "source": "PMDCollab per-action *-Shadow.png",
        "shadow_size": shadow_size_for_species(args.source.resolve()),
        "render_policy": "SpriteBot marker mask; raw PMD body/shadow tile geometry preserved",
        "included_in_frames": _include_shadow,
        "separate_obj": False,
        "body_shadow_frame_sync": "atomic_same_frame",
    }
    manifest.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
    return rc


def main() -> int:
    parser = base.build_parser()
    parser.description = __doc__
    parser.add_argument("--no-shadow", action="store_true", help="emit body-only frames using identical G3R2 ground translations")
    args = parser.parse_args()
    try:
        return convert_g3r2(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
