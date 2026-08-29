#!/usr/bin/env python3
"""Convert one deterministic batch of SoulGold-compatible Showdown species.

Input is the full catalog produced by showdown_bulk_catalog.py. Each selected
species gets normal front/back animation converted with its existing SoulGold
normal palette, copied into install-ready graphics staging, and emitted as a C
descriptor source file.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path

SOULGOLD_REV = "77ec3fc6275bb94dd703f4c1976f1457cc44a60b"


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()


def copy_lane(ingest: Path, staging: Path, species: str, lane: str) -> int:
    src_lane = ingest / species / lane
    dst_lane = staging / "graphics" / "showdown" / species / lane
    dst_lane.mkdir(parents=True, exist_ok=True)
    count = 0
    for png in sorted(src_lane.glob("frame_*.png")):
        shutil.copy2(png, dst_lane / png.name)
        count += 1
    shutil.copy2(src_lane / "manifest.json", dst_lane / "manifest.json")
    return count


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--sprites-zip", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    ap.add_argument("--batch-index", type=int, required=True, help="0-based batch index")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    if args.batch_index < 0 or args.batch_size <= 0:
        raise SystemExit("batch-index must be >=0 and batch-size >0")

    soulgold = args.soulgold.resolve()
    framework = args.framework_root.resolve()
    out = args.output.resolve()
    if git_head(soulgold) != SOULGOLD_REV:
        raise SystemExit(f"SoulGold revision mismatch; expected {SOULGOLD_REV}")

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    candidates = []
    skipped_overflow = []
    for row in catalog["rows"]:
        if not row.get("runtime_exact_candidate"):
            continue
        max_frames = max(int(row.get("front_frames", 0)), int(row.get("back_frames", 0)))
        if max_frames > 255:
            skipped_overflow.append({"slug": row["slug"], "max_frames": max_frames})
            continue
        candidates.append(row)
    candidates.sort(key=lambda r: r["slug"])

    start = args.batch_index * args.batch_size
    end = min(len(candidates), start + args.batch_size)
    selected = candidates[start:end]
    if not selected:
        raise SystemExit(f"Empty batch {args.batch_index}; candidates={len(candidates)}, batch_size={args.batch_size}")

    if out.exists():
        shutil.rmtree(out)
    ingest = out / "ingest"
    staging = out / "staging"
    src = staging / "src"
    src.mkdir(parents=True, exist_ok=True)

    converted = []
    first = True
    for row in selected:
        species = row["slug"]
        host_palette = soulgold / "graphics" / "pokemon" / species / "normal.pal"
        cmd = [
            sys.executable, str(framework / "tools" / "showdown_sprites_ingest.py"),
            "--zip", str(args.sprites_zip),
            "--output", str(ingest),
            "--species", species,
            "--lanes", "front", "back",
            "--host-palette", str(host_palette),
        ]
        if not first:
            cmd.append("--force")
        run(cmd)
        first = False

        front_pngs = copy_lane(ingest, staging, species, "front")
        back_pngs = copy_lane(ingest, staging, species, "back")
        c_path = src / f"showdown_{species}_idle.c"
        run([
            sys.executable, str(framework / "tools" / "emit_soulgold_showdown_s1_c.py"),
            "--ingest-root", str(ingest),
            "--species", species,
            "--lanes", "front", "back",
            "--asset-root", f"graphics/showdown/{species}",
            "--output", str(c_path),
        ])
        converted.append({
            "slug": species,
            "species_constant": row["species_constant"],
            "front_frames": row["front_frames"],
            "back_frames": row["back_frames"],
            "front_pngs": front_pngs,
            "back_pngs": back_pngs,
            "descriptor": str(c_path.relative_to(staging)),
        })

    summary = {
        "format": "soulgold-showdown-bulk-batch-v1",
        "soulgold_revision": SOULGOLD_REV,
        "candidate_count": len(candidates),
        "batch_index": args.batch_index,
        "batch_size": args.batch_size,
        "slice_start": start,
        "slice_end_exclusive": end,
        "converted_count": len(converted),
        "converted": converted,
        "skipped_over_255_frame_lanes": skipped_overflow,
        "runtime_status": "ASSET_CONVERSION_ONLY_NOT_YET_LINKED",
        "ownership_reference": "SHOWDOWN_S1E_OWNERSHIP_AND_PMD_PORT_RULES_20260829.md",
    }
    (out / f"SHOWDOWN_BULK_BATCH_{args.batch_index:03d}_SUMMARY.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    print(json.dumps({
        "candidate_count": len(candidates),
        "batch_index": args.batch_index,
        "converted_count": len(converted),
        "first": converted[0]["slug"],
        "last": converted[-1]["slug"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
