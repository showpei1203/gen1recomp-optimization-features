#!/usr/bin/env python3
"""Audit raw Showdown GIF alpha geometry before GBA conversion.

The report intentionally measures the composited GIF frames consumed by
showdown_sprites_ingest.py. It does not modify animation geometry.
"""
from __future__ import annotations

import argparse
import io
import json
import zipfile
from pathlib import Path, PurePosixPath

from PIL import Image


def find_member(zf: zipfile.ZipFile, lane_dir: str, species: str) -> str:
    target = f"{species}.gif".lower()
    lane = lane_dir.lower()
    matches = []
    for name in zf.namelist():
        parts = PurePosixPath(name).parts
        if len(parts) >= 2 and parts[-2].lower() == lane and parts[-1].lower() == target:
            matches.append(name)
    if len(matches) != 1:
        raise SystemExit(f"Expected one {lane_dir}/{species}.gif, got {matches}")
    return matches[0]


def frame_record(index: int, rgba: Image.Image) -> dict:
    alpha = rgba.getchannel("A")
    bbox = alpha.getbbox()
    if bbox is None:
        return {"index": index, "bbox": None, "opaque_pixels": 0, "bottom_y": None, "centroid_y": None}

    x0, y0, x1, y1 = bbox
    total = 0
    weighted_y = 0
    opaque = 0
    for y in range(rgba.height):
        for a in alpha.crop((0, y, rgba.width, y + 1)).getdata():
            if a >= 128:
                opaque += 1
                total += 1
                weighted_y += y
    centroid_y = (weighted_y / total) if total else None
    return {
        "index": index,
        "bbox": [x0, y0, x1, y1],
        "opaque_pixels": opaque,
        "bottom_y": y1 - 1,
        "centroid_y": round(centroid_y, 4) if centroid_y is not None else None,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--zip", type=Path, required=True)
    ap.add_argument("--lane-dir", required=True)
    ap.add_argument("--species", required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    with zipfile.ZipFile(args.zip) as zf:
        member = find_member(zf, args.lane_dir, args.species)
        data = zf.read(member)

    records = []
    durations = []
    with Image.open(io.BytesIO(data)) as im:
        canvas = list(im.size)
        for i in range(getattr(im, "n_frames", 1)):
            im.seek(i)
            rgba = im.convert("RGBA").copy()
            rec = frame_record(i, rgba)
            rec["duration_ms"] = int(im.info.get("duration", 100) or 100)
            durations.append(rec["duration_ms"])
            records.append(rec)

    bottoms = [r["bottom_y"] for r in records if r["bottom_y"] is not None]
    centroids = [r["centroid_y"] for r in records if r["centroid_y"] is not None]
    report = {
        "species": args.species,
        "lane_dir": args.lane_dir,
        "source_member": member,
        "source_canvas": canvas,
        "frame_count": len(records),
        "bottom_y_min": min(bottoms) if bottoms else None,
        "bottom_y_max": max(bottoms) if bottoms else None,
        "bottom_y_span": (max(bottoms) - min(bottoms)) if bottoms else None,
        "centroid_y_min": min(centroids) if centroids else None,
        "centroid_y_max": max(centroids) if centroids else None,
        "centroid_y_span": round(max(centroids) - min(centroids), 4) if centroids else None,
        "distinct_bottom_y": sorted(set(bottoms)),
        "durations_ms": sorted(set(durations)),
        "frames": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in (
        "species", "lane_dir", "source_canvas", "frame_count",
        "bottom_y_min", "bottom_y_max", "bottom_y_span",
        "centroid_y_span", "distinct_bottom_y")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
