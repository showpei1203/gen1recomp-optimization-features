#!/usr/bin/env python3
"""Pack converted Showdown frames as 8x8 tile deltas and measure ROM cost.

Format v1 is intentionally simple enough for an ARM7TDMI runtime:
- frame 0: one complete 64x64 4bpp keyframe (2048 bytes before LZ)
- frame N>0: one delta record relative to frame N-1
  byte 0 = changed tile count (0..64)
  then repeated: byte tile_index + 32 bytes raw 4bpp tile
- duration remains in the action descriptor/manifest

The script writes raw records and, when --gbagfx is supplied, SoulGold-native
GBA LZ77 versions. Empty deltas need no ROM payload. This keeps every original
Showdown frame and timing while avoiding 2048-byte full-frame storage for tiny
idle movements.
"""
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path

from PIL import Image

TILE_BYTES = 32
TILES_PER_FRAME = 64
FRAME_BYTES = 2048


def png_to_4bpp_tiles(path: Path) -> list[bytes]:
    with Image.open(path) as im:
        if im.size != (64, 64):
            raise ValueError(f"{path}: expected 64x64, got {im.size}")
        if im.mode != "P":
            im = im.convert("P")
        px = list(im.getdata())
    if max(px, default=0) > 15:
        raise ValueError(f"{path}: palette index exceeds 4bpp range")

    tiles: list[bytes] = []
    for ty in range(8):
        for tx in range(8):
            out = bytearray()
            for y in range(8):
                row = (ty * 8 + y) * 64 + tx * 8
                for x in range(0, 8, 2):
                    lo = px[row + x] & 0xF
                    hi = px[row + x + 1] & 0xF
                    out.append(lo | (hi << 4))
            if len(out) != TILE_BYTES:
                raise AssertionError(len(out))
            tiles.append(bytes(out))
    if len(tiles) != TILES_PER_FRAME:
        raise AssertionError(len(tiles))
    return tiles


def full_frame(tiles: list[bytes]) -> bytes:
    data = b"".join(tiles)
    if len(data) != FRAME_BYTES:
        raise AssertionError(len(data))
    return data


def delta_record(previous: list[bytes], current: list[bytes]) -> tuple[bytes, list[int]]:
    changed = [i for i, (a, b) in enumerate(zip(previous, current)) if a != b]
    if len(changed) > 64:
        raise AssertionError(len(changed))
    out = bytearray([len(changed)])
    for tile_index in changed:
        out.append(tile_index)
        out.extend(current[tile_index])
    return bytes(out), changed


def lz_compress(gbagfx: Path, src: Path) -> Path:
    dst = src.with_suffix(src.suffix + ".lz")
    subprocess.run([str(gbagfx), str(src), str(dst)], check=True, stdout=subprocess.DEVNULL)
    return dst


def process_lane(lane_dir: Path, out_dir: Path, gbagfx: Path | None) -> dict:
    manifest = json.loads((lane_dir / "manifest.json").read_text(encoding="utf-8"))
    frame_meta = manifest.get("frames", [])
    pngs = sorted(lane_dir.glob("frame_*.png"))
    if not pngs or len(pngs) != len(frame_meta):
        raise ValueError(f"{lane_dir}: PNG/manifest frame count mismatch {len(pngs)} != {len(frame_meta)}")

    out_dir.mkdir(parents=True, exist_ok=True)
    tiles = [png_to_4bpp_tiles(p) for p in pngs]
    base = out_dir / "frame_000.key.4bpp"
    base.write_bytes(full_frame(tiles[0]))
    base_lz_bytes = None
    if gbagfx:
        base_lz_bytes = lz_compress(gbagfx, base).stat().st_size

    raw_delta_bytes = 0
    lz_delta_bytes = 0
    changed_tile_total = 0
    max_changed_tiles = 0
    empty_delta_frames = 0
    delta_frames = []

    for i in range(1, len(tiles)):
        record, changed = delta_record(tiles[i - 1], tiles[i])
        changed_count = len(changed)
        changed_tile_total += changed_count
        max_changed_tiles = max(max_changed_tiles, changed_count)
        duration = int(frame_meta[i].get("duration_ticks_60hz", 1))
        item = {
            "index": i,
            "duration_ticks_60hz": duration,
            "changed_tiles": changed_count,
            "raw_delta_bytes": 0,
            "gba_lz_bytes": 0,
        }
        if changed_count == 0:
            empty_delta_frames += 1
        else:
            path = out_dir / f"frame_{i:03d}.delta"
            path.write_bytes(record)
            raw_delta_bytes += len(record)
            item["raw_delta_bytes"] = len(record)
            if gbagfx:
                lz_path = lz_compress(gbagfx, path)
                item["gba_lz_bytes"] = lz_path.stat().st_size
                lz_delta_bytes += lz_path.stat().st_size
        delta_frames.append(item)

    frame_count = len(tiles)
    average_changed = changed_tile_total / max(1, frame_count - 1)
    # Runtime metadata estimate: pointer/offset + u16 duration + flags/count,
    # conservatively 8 bytes per source frame. This is intentionally included
    # in budget so the format is not judged only by payload bytes.
    descriptor_bytes_estimate = frame_count * 8
    raw_total = FRAME_BYTES + raw_delta_bytes + descriptor_bytes_estimate
    lz_payload = (base_lz_bytes or FRAME_BYTES) + (lz_delta_bytes if gbagfx else raw_delta_bytes)
    lz_total = lz_payload + descriptor_bytes_estimate

    report = {
        "frame_count": frame_count,
        "base_raw_bytes": FRAME_BYTES,
        "base_gba_lz_bytes": base_lz_bytes,
        "delta_raw_bytes": raw_delta_bytes,
        "delta_gba_lz_bytes": lz_delta_bytes if gbagfx else None,
        "descriptor_bytes_estimate": descriptor_bytes_estimate,
        "tile_delta_raw_total_bytes": raw_total,
        "tile_delta_gba_lz_total_bytes": lz_total if gbagfx else None,
        "full_frame_raw_bytes": frame_count * FRAME_BYTES,
        "changed_tile_total": changed_tile_total,
        "average_changed_tiles_per_transition": round(average_changed, 4),
        "max_changed_tiles_in_transition": max_changed_tiles,
        "empty_delta_frames": empty_delta_frames,
        "frames": delta_frames,
    }
    (out_dir / "tile_delta_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--graphics-root", type=Path, required=True, help="staging/graphics/showdown")
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--gbagfx", type=Path)
    args = ap.parse_args()

    gbagfx = args.gbagfx.resolve() if args.gbagfx else None
    if gbagfx and not gbagfx.is_file():
        raise SystemExit(f"gbagfx not found: {gbagfx}")

    rows = []
    totals = {
        "species": 0,
        "lanes": 0,
        "frames": 0,
        "full_frame_raw_bytes": 0,
        "tile_delta_raw_total_bytes": 0,
        "tile_delta_gba_lz_total_bytes": 0,
        "changed_tile_total": 0,
        "transitions": 0,
        "empty_delta_frames": 0,
    }
    species_dirs = sorted(p for p in args.graphics_root.iterdir() if p.is_dir())
    for species_dir in species_dirs:
        species_row = {"species": species_dir.name, "lanes": {}}
        lane_seen = 0
        for lane in ("front", "back"):
            lane_dir = species_dir / lane
            if not lane_dir.is_dir():
                continue
            report = process_lane(lane_dir, args.output / species_dir.name / lane, gbagfx)
            species_row["lanes"][lane] = report
            lane_seen += 1
            totals["lanes"] += 1
            totals["frames"] += report["frame_count"]
            totals["full_frame_raw_bytes"] += report["full_frame_raw_bytes"]
            totals["tile_delta_raw_total_bytes"] += report["tile_delta_raw_total_bytes"]
            totals["tile_delta_gba_lz_total_bytes"] += report["tile_delta_gba_lz_total_bytes"] or 0
            totals["changed_tile_total"] += report["changed_tile_total"]
            totals["transitions"] += max(0, report["frame_count"] - 1)
            totals["empty_delta_frames"] += report["empty_delta_frames"]
        if lane_seen:
            totals["species"] += 1
            rows.append(species_row)

    totals["average_changed_tiles_per_transition"] = round(
        totals["changed_tile_total"] / max(1, totals["transitions"]), 4
    )
    totals["raw_delta_vs_full_raw_ratio"] = round(
        totals["tile_delta_raw_total_bytes"] / max(1, totals["full_frame_raw_bytes"]), 6
    )
    if gbagfx:
        totals["lz_delta_vs_full_raw_ratio"] = round(
            totals["tile_delta_gba_lz_total_bytes"] / max(1, totals["full_frame_raw_bytes"]), 6
        )
    result = {"format": "showdown-tile-delta-v1-budget", "totals": totals, "species": rows}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "SHOWDOWN_TILE_DELTA_BUDGET.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(totals, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
