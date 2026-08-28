#!/usr/bin/env python3
"""PMD SpriteCollab -> portable GBA battle-animation assets.

Phase-1 goals:
- preserve SpriteCollab animation semantics/timing/provenance;
- extract one battle-facing direction at a time;
- normalize source frames onto a 64x64 GBA canvas using the PMD body-center
  marker from *-Offsets.png rather than naive image centering;
- build one shared 15-visible-color + transparent palette for the selected set;
- emit indexed PNG frame sources, JASC palette, portable IR JSON and a tiny C
  INCBIN descriptor include.

The SoulGold / pokeemerald-expansion build system remains responsible for:
PNG -> 4bpp -> LZ and PAL -> gbapal. This tool intentionally does not own GBA
compression.

This is a prototype converter, not yet formal authority. Large (>64px) PMD
source actions are rejected by default rather than silently scaled.
"""

from __future__ import annotations

import argparse
import json
import math
import sys
import xml.etree.ElementTree as ET
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

try:
    from PIL import Image
except ImportError as exc:  # pragma: no cover - runtime environment dependent
    raise SystemExit("Pillow is required: python -m pip install Pillow") from exc

DIRECTIONS = [
    "Down", "DownRight", "Right", "UpRight",
    "Up", "UpLeft", "Left", "DownLeft",
]
DIRECTION_TO_ROW = {name: i for i, name in enumerate(DIRECTIONS)}

CANVAS_W = 64
CANVAS_H = 64
MAX_VISIBLE_COLORS = 15


@dataclass(frozen=True)
class ActionMeta:
    name: str
    index: int
    copy_of: Optional[str]
    frame_width: Optional[int]
    frame_height: Optional[int]
    durations: Tuple[int, ...]
    rush_frame: Optional[int]
    hit_frame: Optional[int]
    return_frame: Optional[int]

    @property
    def frame_count(self) -> int:
        return len(self.durations)


@dataclass(frozen=True)
class ResolvedAction:
    requested_name: str
    source_action: str
    index: int
    frame_width: int
    frame_height: int
    durations: Tuple[int, ...]
    rush_frame: Optional[int]
    hit_frame: Optional[int]
    return_frame: Optional[int]

    @property
    def frame_count(self) -> int:
        return len(self.durations)

    @property
    def gba_safe_single_obj(self) -> bool:
        return self.frame_width <= CANVAS_W and self.frame_height <= CANVAS_H


def _text_int(parent: ET.Element, tag: str) -> Optional[int]:
    node = parent.find(tag)
    if node is None or node.text is None or not node.text.strip():
        return None
    return int(node.text.strip())


def parse_anim_data(path: Path) -> Dict[str, ActionMeta]:
    root = ET.parse(path).getroot()
    actions: Dict[str, ActionMeta] = {}
    for anim in root.findall("./Anims/Anim"):
        name_node = anim.find("Name")
        index_node = anim.find("Index")
        if name_node is None or name_node.text is None or index_node is None or index_node.text is None:
            raise ValueError("AnimData.xml contains an Anim without Name/Index")
        name = name_node.text.strip()
        copy_node = anim.find("CopyOf")
        durations = tuple(
            int(n.text.strip())
            for n in anim.findall("./Durations/Duration")
            if n.text and n.text.strip()
        )
        actions[name] = ActionMeta(
            name=name,
            index=int(index_node.text.strip()),
            copy_of=(copy_node.text.strip() if copy_node is not None and copy_node.text else None),
            frame_width=_text_int(anim, "FrameWidth"),
            frame_height=_text_int(anim, "FrameHeight"),
            durations=durations,
            rush_frame=_text_int(anim, "RushFrame"),
            hit_frame=_text_int(anim, "HitFrame"),
            return_frame=_text_int(anim, "ReturnFrame"),
        )
    if not actions:
        raise ValueError(f"No animations found in {path}")
    return actions


def resolve_action(name: str, actions: Dict[str, ActionMeta]) -> ResolvedAction:
    if name not in actions:
        raise KeyError(f"Unknown PMD action: {name}")
    seen = set()
    requested = actions[name]
    cur = requested
    while cur.copy_of:
        if cur.name in seen:
            raise ValueError(f"CopyOf cycle while resolving {name}: {sorted(seen)}")
        seen.add(cur.name)
        if cur.copy_of not in actions:
            raise KeyError(f"{cur.name} CopyOf references missing action {cur.copy_of}")
        cur = actions[cur.copy_of]
    if cur.frame_width is None or cur.frame_height is None or not cur.durations:
        raise ValueError(f"Resolved PMD action {cur.name} lacks dimensions/durations")
    # CopyOf aliases use the source action's actual timeline markers. If an alias
    # ever gains an explicit marker, prefer it without duplicating image data.
    return ResolvedAction(
        requested_name=name,
        source_action=cur.name,
        index=requested.index,
        frame_width=cur.frame_width,
        frame_height=cur.frame_height,
        durations=cur.durations,
        rush_frame=requested.rush_frame if requested.rush_frame is not None else cur.rush_frame,
        hit_frame=requested.hit_frame if requested.hit_frame is not None else cur.hit_frame,
        return_frame=requested.return_frame if requested.return_frame is not None else cur.return_frame,
    )


def _open_rgba(path: Path) -> Image.Image:
    if not path.exists():
        raise FileNotFoundError(path)
    return Image.open(path).convert("RGBA")


def crop_direction_frame(sheet: Image.Image, action: ResolvedAction, direction: str, frame_index: int) -> Image.Image:
    if direction not in DIRECTION_TO_ROW:
        raise ValueError(f"Unknown direction {direction}; use one of {DIRECTIONS}")
    if frame_index < 0 or frame_index >= action.frame_count:
        raise IndexError(frame_index)
    expected_w = action.frame_width * action.frame_count
    min_h = action.frame_height * len(DIRECTIONS)
    if sheet.width < expected_w or sheet.height < min_h:
        raise ValueError(
            f"{action.source_action} sheet is {sheet.size}, expected at least "
            f"{expected_w}x{min_h} for {action.frame_count} frames x 8 directions"
        )
    x0 = frame_index * action.frame_width
    y0 = DIRECTION_TO_ROW[direction] * action.frame_height
    return sheet.crop((x0, y0, x0 + action.frame_width, y0 + action.frame_height))


def _body_center_candidates(offset_crop: Image.Image) -> List[Tuple[int, int]]:
    """Return PMD body-center marker candidates.

    SpriteCollab offset images conventionally encode the body center in green.
    Use a tolerant channel classifier so minor file encoding differences do not
    turn a one-pixel marker into an invisible failure. We intentionally do NOT
    fall back to image-center alignment.
    """
    px = offset_crop.load()
    out: List[Tuple[int, int]] = []
    for y in range(offset_crop.height):
        for x in range(offset_crop.width):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if g >= 128 and g >= r * 1.5 and g >= b * 1.5:
                out.append((x, y))
    return out


def body_center_from_offsets(offset_crop: Image.Image) -> Tuple[int, int]:
    pts = _body_center_candidates(offset_crop)
    if not pts:
        raise ValueError(
            "No PMD green body-center marker found in Offsets frame. "
            "Refusing naive center alignment; inspect source metadata instead."
        )
    # Markers may be several adjacent pixels. Use their centroid.
    x = int(round(sum(p[0] for p in pts) / len(pts)))
    y = int(round(sum(p[1] for p in pts) / len(pts)))
    return x, y


def normalize_frame(
    frame: Image.Image,
    body_center: Tuple[int, int],
    anchor_target: Tuple[int, int],
) -> Tuple[Image.Image, int, int]:
    if frame.width > CANVAS_W or frame.height > CANVAS_H:
        raise ValueError(
            f"Source frame {frame.size} exceeds single-OBJ {CANVAS_W}x{CANVAS_H}; "
            "large-action strategy is a later gate."
        )
    dx = anchor_target[0] - body_center[0]
    dy = anchor_target[1] - body_center[1]
    if dx < 0 or dy < 0 or dx + frame.width > CANVAS_W or dy + frame.height > CANVAS_H:
        raise ValueError(
            f"Anchor placement would clip frame {frame.size}: paste=({dx},{dy}), "
            f"target={anchor_target}, source_center={body_center}. "
            "Tune the species anchor profile; clipping is forbidden."
        )
    canvas = Image.new("RGBA", (CANVAS_W, CANVAS_H), (0, 0, 0, 0))
    canvas.alpha_composite(frame, (dx, dy))
    return canvas, dx, dy


def collect_opaque_colors(images: Iterable[Image.Image]) -> List[Tuple[int, int, int]]:
    colors = set()
    for image in images:
        for r, g, b, a in image.getdata():
            if a:
                colors.add((r, g, b))
    return sorted(colors)


def quantized_palette(images: Sequence[Image.Image]) -> List[Tuple[int, int, int]]:
    colors = collect_opaque_colors(images)
    if len(colors) <= MAX_VISIBLE_COLORS:
        return colors

    # Build one species/action-set palette, never a different palette per frame.
    # No dithering is used. The image is not resized, so pixel geometry remains
    # exact even when color count is reduced.
    total_pixels = sum(img.width * img.height for img in images)
    side = int(math.ceil(math.sqrt(total_pixels)))
    atlas = Image.new("RGB", (side, side), (0, 0, 0))
    cursor = 0
    for image in images:
        for r, g, b, a in image.getdata():
            if not a:
                continue
            x = cursor % side
            y = cursor // side
            atlas.putpixel((x, y), (r, g, b))
            cursor += 1
    crop_h = max(1, int(math.ceil(cursor / side)))
    atlas = atlas.crop((0, 0, side, crop_h))
    q = atlas.quantize(colors=MAX_VISIBLE_COLORS, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    raw = q.getpalette()[: MAX_VISIBLE_COLORS * 3]
    pal = [tuple(raw[i : i + 3]) for i in range(0, len(raw), 3)]
    # Pillow may leave duplicates. Preserve deterministic first occurrence.
    dedup: List[Tuple[int, int, int]] = []
    for c in pal:
        if c not in dedup:
            dedup.append(c)
    return dedup[:MAX_VISIBLE_COLORS]


def nearest_color_index(rgb: Tuple[int, int, int], palette: Sequence[Tuple[int, int, int]]) -> int:
    best_i = 0
    best_d = None
    for i, p in enumerate(palette):
        d = sum((rgb[c] - p[c]) ** 2 for c in range(3))
        if best_d is None or d < best_d:
            best_i, best_d = i, d
    return best_i


def to_indexed_gba(image: Image.Image, visible_palette: Sequence[Tuple[int, int, int]]) -> Image.Image:
    if len(visible_palette) > MAX_VISIBLE_COLORS:
        raise ValueError("visible palette exceeds 15 colors")
    out = Image.new("P", image.size, 0)
    # Index 0 is transparent. Opaque colors begin at index 1.
    flat = [0, 0, 0]
    for color in visible_palette:
        flat.extend(color)
    flat.extend([0] * (768 - len(flat)))
    out.putpalette(flat)
    src = image.load()
    dst = out.load()
    for y in range(image.height):
        for x in range(image.width):
            r, g, b, a = src[x, y]
            if not a:
                dst[x, y] = 0
            else:
                dst[x, y] = nearest_color_index((r, g, b), visible_palette) + 1
    out.info["transparency"] = 0
    return out


def write_jasc_palette(path: Path, visible_palette: Sequence[Tuple[int, int, int]]) -> None:
    entries = [(0, 0, 0)] + list(visible_palette)
    while len(entries) < 16:
        entries.append((0, 0, 0))
    lines = ["JASC-PAL", "0100", "16"] + [f"{r} {g} {b}" for r, g, b in entries[:16]]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def c_symbol(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def emit_c_assets(path: Path, species: str, action_records: Sequence[dict], asset_root: str) -> None:
    species_sym = c_symbol(species)
    lines = [
        "/* Auto-generated by tools/pmd_gba_converter.py. */",
        "/* Source PNGs are converted by the host's normal .4bpp.lz Make rules. */",
        "",
    ]
    for action in action_records:
        action_sym = c_symbol(action["name"])
        for frame in action["frames"]:
            idx = frame["index"]
            symbol = f"gPmd{species_sym}{action_sym}Frame{idx:02d}"
            rel = f"{asset_root}/{action['name'].lower()}/frame_{idx:02d}.4bpp.lz"
            lines.append(f'const u32 {symbol}[] = INCBIN_U32("{rel}");')
        lines.append("")
    path.write_text("\n".join(lines), encoding="utf-8")


def convert(args: argparse.Namespace) -> int:
    source_dir = args.source.resolve()
    anim_xml = source_dir / "AnimData.xml"
    actions = parse_anim_data(anim_xml)
    wanted = [x.strip() for x in args.actions.split(",") if x.strip()]
    if not wanted:
        raise ValueError("--actions must select at least one action")
    resolved = [resolve_action(name, actions) for name in wanted]

    out_dir = args.output.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    direction = args.direction
    anchor_target = (args.anchor_x, args.anchor_y)

    normalized: List[Image.Image] = []
    pending: List[Tuple[ResolvedAction, int, Image.Image, dict]] = []
    ir_actions: List[dict] = []

    for action in resolved:
        action_rec = {
            "name": action.requested_name,
            "source_action": action.source_action,
            "semantic_role": "ambient",
            "rush_frame": action.rush_frame,
            "hit_frame": action.hit_frame,
            "return_frame": action.return_frame,
            "direction": direction,
            "source_row": DIRECTION_TO_ROW[direction],
            "source_frame_width": action.frame_width,
            "source_frame_height": action.frame_height,
            "gba_safe_single_obj": action.gba_safe_single_obj,
            "frames": [],
        }
        if not action.gba_safe_single_obj and not args.metadata_only:
            raise ValueError(
                f"{action.requested_name} is {action.frame_width}x{action.frame_height}; "
                "large actions are intentionally deferred."
            )

        if args.metadata_only:
            for i, duration in enumerate(action.durations):
                action_rec["frames"].append({"index": i, "duration": duration})
            ir_actions.append(action_rec)
            continue

        anim_path = source_dir / f"{action.source_action}-Anim.png"
        offsets_path = source_dir / f"{action.source_action}-Offsets.png"
        anim_sheet = _open_rgba(anim_path)
        offsets_sheet = _open_rgba(offsets_path)

        for i, duration in enumerate(action.durations):
            frame = crop_direction_frame(anim_sheet, action, direction, i)
            offsets = crop_direction_frame(offsets_sheet, action, direction, i)
            source_center = body_center_from_offsets(offsets)
            canvas, paste_x, paste_y = normalize_frame(frame, source_center, anchor_target)
            frame_meta = {
                "index": i,
                "duration": duration,
                "canvas_w": CANVAS_W,
                "canvas_h": CANVAS_H,
                "anchor_x": anchor_target[0],
                "anchor_y": anchor_target[1],
                "source_center_x": source_center[0],
                "source_center_y": source_center[1],
                "paste_x": paste_x,
                "paste_y": paste_y,
                "presentation_dx": 0,
                "presentation_dy": 0,
                "gba_safe_single_obj": True,
                "asset": f"{action.requested_name.lower()}/frame_{i:02d}.png",
            }
            action_rec["frames"].append(frame_meta)
            normalized.append(canvas)
            pending.append((action, i, canvas, frame_meta))
        ir_actions.append(action_rec)

    ir = {
        "schema_version": 1,
        "species": {"name": args.species, "national_dex": args.national_dex, "form": None},
        "source": {
            "repository": "PMDCollab/SpriteCollab",
            "revision": args.source_revision,
            "path": args.source_repo_path,
            "license_reference": args.license_reference,
        },
        "body_profile": {
            "body_class": args.body_class,
            "ambient_style": args.ambient_style,
            "logical_position_locked": True,
            "anchor_target": {"x": args.anchor_x, "y": args.anchor_y},
        },
        "ambient": {
            "home_action": "Idle",
            "pattern": wanted,
            "restart_from_home_after_combat": True,
        },
        "actions": {rec["name"]: rec for rec in ir_actions},
    }

    if not args.metadata_only:
        visible_palette = quantized_palette(normalized)
        write_jasc_palette(out_dir / "normal.pal", visible_palette)
        for action, idx, canvas, frame_meta in pending:
            action_dir = out_dir / action.requested_name.lower()
            action_dir.mkdir(parents=True, exist_ok=True)
            indexed = to_indexed_gba(canvas, visible_palette)
            indexed.save(action_dir / f"frame_{idx:02d}.png", optimize=False)
        emit_c_assets(
            out_dir / "pmd_assets.inc.c",
            args.species,
            ir_actions,
            args.host_asset_root.rstrip("/"),
        )
        ir["palette"] = {
            "visible_color_count": len(visible_palette),
            "transparent_index": 0,
            "file": "normal.pal",
        }

    (out_dir / "manifest.ir.json").write_text(json.dumps(ir, indent=2) + "\n", encoding="utf-8")
    print(f"Wrote PMD GBA IR: {out_dir / 'manifest.ir.json'}")
    if not args.metadata_only:
        print(f"Wrote {len(pending)} normalized 64x64 frame PNGs; palette <= 15 visible colors")
    return 0


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--source", type=Path, required=True, help="SpriteCollab species directory containing AnimData.xml")
    p.add_argument("--output", type=Path, required=True)
    p.add_argument("--species", default="Cyndaquil")
    p.add_argument("--national-dex", type=int, default=155)
    p.add_argument("--actions", default="Idle,Walk,LookUp,DeepBreath,Rotate")
    p.add_argument("--direction", choices=DIRECTIONS, default="UpRight", help="player-side default; opponent benchmark can use DownLeft")
    p.add_argument("--anchor-x", type=int, default=32)
    p.add_argument("--anchor-y", type=int, default=44, help="provisional species profile anchor; must be visually validated")
    p.add_argument("--body-class", default="small_quadruped")
    p.add_argument("--ambient-style", default="active_prowl")
    p.add_argument("--source-revision", default="4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7")
    p.add_argument("--source-repo-path", default="sprite/0155")
    p.add_argument("--license-reference", default="PMDCollab/SpriteCollab repository credits/license authority")
    p.add_argument("--host-asset-root", default="graphics/pmd/cyndaquil")
    p.add_argument("--metadata-only", action="store_true", help="parse/emit IR without requiring PNG assets/Pillow processing")
    return p


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return convert(args)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
