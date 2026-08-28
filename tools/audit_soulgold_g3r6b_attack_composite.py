#!/usr/bin/env python3
"""Audit PMDCollab Attack for a lossless SoulGold multi-OBJ renderer.

This stage deliberately does NOT wire Attack into move ownership yet. It answers
one narrower question first: can the pinned PMDCollab Attack frames be preserved
pixel-for-pixel on GBA without cropping/scaling, and what composite OBJ geometry
is actually required after body-center normalization?

The audit works in body-local coordinates. Every opaque source pixel is measured
relative to the PMDCollab green body-center marker from Attack-Offsets.png. It
then computes the minimal 32x32 chunk grid needed to cover the union of all
Attack frames for the selected battle direction. 32x32 is intentional: it is a
native GBA OBJ size and avoids inventing illegal 64x8/64x16 strip shapes.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import convert_soulgold_g3r4 as g3r4
import pmd_gba_converter as base

SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
CHUNK = 32
MAX_COMPOSITE_CHUNKS = 12

TARGETS = (
    {"species":"Cyndaquil","id":"0155","direction":"UpRight"},
    {"species":"Marill","id":"0183","direction":"DownLeft"},
)


def opaque_bbox_local(frame, center):
    px = frame.load()
    xs = []
    ys = []
    cx, cy = center
    count = 0
    for y in range(frame.height):
        for x in range(frame.width):
            if px[x, y][3]:
                xs.append(x - cx)
                ys.append(y - cy)
                count += 1
    if not xs:
        return None, 0
    return [min(xs), min(ys), max(xs), max(ys)], count


def floor_chunk(v):
    return math.floor(v / CHUNK) * CHUNK


def ceil_chunk_exclusive(v):
    return math.ceil(v / CHUNK) * CHUNK


def occupied_chunks(frame, center, grid_min_x, grid_min_y):
    px = frame.load()
    cx, cy = center
    used = set()
    for y in range(frame.height):
        for x in range(frame.width):
            if not px[x, y][3]:
                continue
            lx = x - cx
            ly = y - cy
            col = (lx - grid_min_x) // CHUNK
            row = (ly - grid_min_y) // CHUNK
            used.add((int(col), int(row)))
    return sorted(used, key=lambda p:(p[1],p[0]))


def audit_target(spritecollab: Path, target: dict) -> dict:
    species_dir = spritecollab / "sprite" / target["id"]
    actions = g3r4.parse_anim_data_g3r4(species_dir / "AnimData.xml")
    attack = base.resolve_action("Attack", actions)
    anim = base._open_rgba(species_dir / "Attack-Anim.png")
    offsets = base._open_rgba(species_dir / "Attack-Offsets.png")

    frames = []
    union = None
    total_opaque = 0
    for i, duration in enumerate(attack.durations):
        body = base.crop_direction_frame(anim, attack, target["direction"], i)
        off = base.crop_direction_frame(offsets, attack, target["direction"], i)
        center = base.body_center_from_offsets(off)
        bbox, opaque = opaque_bbox_local(body, center)
        if bbox is None:
            raise SystemExit(f"{target['species']} Attack frame {i} has no opaque body pixels")
        total_opaque += opaque
        if union is None:
            union = bbox[:]
        else:
            union[0] = min(union[0], bbox[0])
            union[1] = min(union[1], bbox[1])
            union[2] = max(union[2], bbox[2])
            union[3] = max(union[3], bbox[3])
        frames.append({
            "index": i,
            "duration": int(duration),
            "body_center": [int(center[0]), int(center[1])],
            "opaque_bbox_body_local": bbox,
            "opaque_pixels": opaque,
        })

    grid_min_x = floor_chunk(union[0])
    grid_min_y = floor_chunk(union[1])
    grid_max_x = ceil_chunk_exclusive(union[2] + 1)
    grid_max_y = ceil_chunk_exclusive(union[3] + 1)
    cols = (grid_max_x - grid_min_x) // CHUNK
    rows = (grid_max_y - grid_min_y) // CHUNK
    capacity = cols * rows
    if capacity > MAX_COMPOSITE_CHUNKS:
        raise SystemExit(
            f"{target['species']} Attack requires {capacity} 32x32 grid chunks; "
            f"prototype cap is {MAX_COMPOSITE_CHUNKS}"
        )

    max_used = 0
    all_used = set()
    for frame_rec, i in zip(frames, range(len(frames))):
        body = base.crop_direction_frame(anim, attack, target["direction"], i)
        off = base.crop_direction_frame(offsets, attack, target["direction"], i)
        center = base.body_center_from_offsets(off)
        used = occupied_chunks(body, center, grid_min_x, grid_min_y)
        frame_rec["occupied_chunks"] = [list(p) for p in used]
        frame_rec["occupied_chunk_count"] = len(used)
        max_used = max(max_used, len(used))
        all_used.update(used)

    return {
        "species": target["species"],
        "spritecollab_id": target["id"],
        "direction": target["direction"],
        "source_frame_size": [attack.frame_width, attack.frame_height],
        "frame_count": attack.frame_count,
        "durations": list(attack.durations),
        "rush_frame": attack.rush_frame,
        "hit_frame": attack.hit_frame,
        "return_frame": attack.return_frame,
        "single_obj_safe_by_source_dimensions": attack.gba_safe_single_obj,
        "opaque_union_body_local": union,
        "composite_grid": {
            "chunk_size": [CHUNK, CHUNK],
            "origin_body_local": [grid_min_x, grid_min_y],
            "cols": cols,
            "rows": rows,
            "capacity_chunks": capacity,
            "ever_occupied_chunks": [list(p) for p in sorted(all_used, key=lambda p:(p[1],p[0]))],
            "max_occupied_chunks_in_one_frame": max_used,
        },
        "total_opaque_pixels_across_timeline": total_opaque,
        "frames": frames,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    root = args.spritecollab.resolve()
    out = args.output.resolve()
    result = {
        "phase": "G3R6B_ATTACK_COMPOSITE_AUDIT",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "renderer_policy": "LOSSLESS_BODY_LOCAL_32X32_SUBSPRITE_GRID",
        "cropping": False,
        "scaling": False,
        "semantic_move_ownership": "NOT_YET_WIRED",
        "targets": {},
    }
    for target in TARGETS:
        rec = audit_target(root, target)
        result["targets"][target["species"]] = rec
        print(
            target["species"],
            "source", rec["source_frame_size"],
            "union", rec["opaque_union_body_local"],
            "grid", rec["composite_grid"],
            "markers", (rec["rush_frame"],rec["hit_frame"],rec["return_frame"]),
        )

    cy = result["targets"]["Cyndaquil"]
    ma = result["targets"]["Marill"]
    if cy["durations"] != [2,4,1,1,1,2,2,2,2,2]:
        raise SystemExit(f"Unexpected pinned Cyndaquil Attack durations: {cy['durations']}")
    if ma["durations"] != [2,4,1,1,1,2,2,2,2,2,2]:
        raise SystemExit(f"Unexpected pinned Marill Attack durations: {ma['durations']}")
    for rec in (cy, ma):
        if (rec["rush_frame"], rec["hit_frame"], rec["return_frame"]) != (1,3,6):
            raise SystemExit(f"Unexpected Attack markers for {rec['species']}: {rec['rush_frame'],rec['hit_frame'],rec['return_frame']}")
        if rec["composite_grid"]["capacity_chunks"] > MAX_COMPOSITE_CHUNKS:
            raise SystemExit("Composite capacity escaped audit cap")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Wrote", out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
