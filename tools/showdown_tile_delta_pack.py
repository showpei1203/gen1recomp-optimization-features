#!/usr/bin/env python3
"""Pack converted Showdown frames as delta candidates and measure ROM cost.

Two lossless formats are measured against SoulGold's native gbagfx LZ77:

Tile-delta v1
- frame 0: full 64x64 4bpp keyframe
- later frames: changed 8x8 tiles relative to the previous frame

XOR-delta v1
- frame 0: full 64x64 4bpp keyframe
- later frames: 2048-byte XOR mask against the previous frame, then GBA LZ
- unchanged regions become long zero runs, which GBA LZ compresses efficiently

Both preserve every original Showdown frame and timing. A runtime can keep one
2KB canonical decoded frame per battler. Native battle choreography continues to
operate on the battler sprite; after a native move, the canonical frame can be
copied back exactly as in S1E ownership recovery.
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


def tile_delta_record(previous: list[bytes], current: list[bytes]) -> tuple[bytes, list[int]]:
    changed = [i for i, (a, b) in enumerate(zip(previous, current)) if a != b]
    out = bytearray([len(changed)])
    for tile_index in changed:
        out.append(tile_index)
        out.extend(current[tile_index])
    return bytes(out), changed


def xor_delta(previous: bytes, current: bytes) -> bytes:
    if len(previous) != FRAME_BYTES or len(current) != FRAME_BYTES:
        raise ValueError("XOR frames must be 2048 bytes")
    return bytes(a ^ b for a, b in zip(previous, current))


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
    frames = [full_frame(t) for t in tiles]
    base = out_dir / "frame_000.key.4bpp"
    base.write_bytes(frames[0])
    base_lz_bytes = None
    if gbagfx:
        base_lz_bytes = lz_compress(gbagfx, base).stat().st_size

    tile_raw_bytes = 0
    tile_lz_bytes = 0
    xor_lz_bytes = 0
    changed_tile_total = 0
    max_changed_tiles = 0
    empty_delta_frames = 0
    transition_rows = []

    for i in range(1, len(frames)):
        tile_record, changed = tile_delta_record(tiles[i - 1], tiles[i])
        xor_record = xor_delta(frames[i - 1], frames[i])
        changed_count = len(changed)
        changed_tile_total += changed_count
        max_changed_tiles = max(max_changed_tiles, changed_count)
        duration = int(frame_meta[i].get("duration_ticks_60hz", 1))
        item = {
            "index": i,
            "duration_ticks_60hz": duration,
            "changed_tiles": changed_count,
            "tile_raw_bytes": 0,
            "tile_gba_lz_bytes": 0,
            "xor_gba_lz_bytes": 0,
        }
        if changed_count == 0:
            empty_delta_frames += 1
        else:
            tile_path = out_dir / f"frame_{i:03d}.tile_delta"
            tile_path.write_bytes(tile_record)
            tile_raw_bytes += len(tile_record)
            xor_path = out_dir / f"frame_{i:03d}.xor_delta"
            xor_path.write_bytes(xor_record)
            item["tile_raw_bytes"] = len(tile_record)
            if gbagfx:
                tile_lz_path = lz_compress(gbagfx, tile_path)
                xor_lz_path = lz_compress(gbagfx, xor_path)
                item["tile_gba_lz_bytes"] = tile_lz_path.stat().st_size
                item["xor_gba_lz_bytes"] = xor_lz_path.stat().st_size
                tile_lz_bytes += item["tile_gba_lz_bytes"]
                xor_lz_bytes += item["xor_gba_lz_bytes"]
        transition_rows.append(item)

    frame_count = len(frames)
    average_changed = changed_tile_total / max(1, frame_count - 1)
    descriptor_bytes_estimate = frame_count * 8
    key_bytes = base_lz_bytes if gbagfx else FRAME_BYTES
    tile_raw_total = FRAME_BYTES + tile_raw_bytes + descriptor_bytes_estimate
    tile_lz_total = (key_bytes + tile_lz_bytes + descriptor_bytes_estimate) if gbagfx else None
    xor_lz_total = (key_bytes + xor_lz_bytes + descriptor_bytes_estimate) if gbagfx else None

    report = {
        "frame_count": frame_count,
        "base_raw_bytes": FRAME_BYTES,
        "base_gba_lz_bytes": base_lz_bytes,
        "descriptor_bytes_estimate": descriptor_bytes_estimate,
        "tile_delta_raw_payload_bytes": tile_raw_bytes,
        "tile_delta_gba_lz_payload_bytes": tile_lz_bytes if gbagfx else None,
        "tile_delta_raw_total_bytes": tile_raw_total,
        "tile_delta_gba_lz_total_bytes": tile_lz_total,
        "xor_delta_gba_lz_payload_bytes": xor_lz_bytes if gbagfx else None,
        "xor_delta_gba_lz_total_bytes": xor_lz_total,
        "full_frame_raw_bytes": frame_count * FRAME_BYTES,
        "changed_tile_total": changed_tile_total,
        "average_changed_tiles_per_transition": round(average_changed, 4),
        "max_changed_tiles_in_transition": max_changed_tiles,
        "empty_delta_frames": empty_delta_frames,
        "transitions": transition_rows,
    }
    (out_dir / "delta_manifest.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
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
        "xor_delta_gba_lz_total_bytes": 0,
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
            totals["xor_delta_gba_lz_total_bytes"] += report["xor_delta_gba_lz_total_bytes"] or 0
            totals["changed_tile_total"] += report["changed_tile_total"]
            totals["transitions"] += max(0, report["frame_count"] - 1)
            totals["empty_delta_frames"] += report["empty_delta_frames"]
        if lane_seen:
            totals["species"] += 1
            rows.append(species_row)

    totals["average_changed_tiles_per_transition"] = round(
        totals["changed_tile_total"] / max(1, totals["transitions"]), 4
    )
    totals["tile_raw_vs_full_raw_ratio"] = round(
        totals["tile_delta_raw_total_bytes"] / max(1, totals["full_frame_raw_bytes"]), 6
    )
    if gbagfx:
        totals["tile_lz_vs_full_raw_ratio"] = round(
            totals["tile_delta_gba_lz_total_bytes"] / max(1, totals["full_frame_raw_bytes"]), 6
        )
        totals["xor_lz_vs_full_raw_ratio"] = round(
            totals["xor_delta_gba_lz_total_bytes"] / max(1, totals["full_frame_raw_bytes"]), 6
        )
        totals["winner"] = (
            "xor_delta_gba_lz" if totals["xor_delta_gba_lz_total_bytes"] < totals["tile_delta_gba_lz_total_bytes"]
            else "tile_delta_gba_lz"
        )
    result = {"format": "showdown-delta-v2-budget", "totals": totals, "species": rows}
    args.output.mkdir(parents=True, exist_ok=True)
    (args.output / "SHOWDOWN_TILE_DELTA_BUDGET.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(totals, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
