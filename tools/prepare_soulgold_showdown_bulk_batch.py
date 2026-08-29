#!/usr/bin/env python3
"""Convert one deterministic batch of SoulGold-compatible Showdown species.

Input is the full catalog produced by showdown_bulk_catalog.py. Exact filename
matches and unique normalized aliases are both supported. Output paths and C
symbols always use the SoulGold host slug; Showdown source slugs are recorded
separately so alias handling remains explicit and reproducible.
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


def copy_lane(ingest: Path, staging: Path, source_slug: str, host_slug: str, lane: str) -> int:
    src_lane = ingest / source_slug / lane
    dst_lane = staging / "graphics" / "showdown" / host_slug / lane
    dst_lane.mkdir(parents=True, exist_ok=True)
    count = 0
    for png in sorted(src_lane.glob("frame_*.png")):
        shutil.copy2(png, dst_lane / png.name)
        count += 1
    manifest = json.loads((src_lane / "manifest.json").read_text(encoding="utf-8"))
    manifest["soulgold_host_slug"] = host_slug
    manifest["showdown_source_slug"] = source_slug
    (dst_lane / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return count


def mirror_ingest_for_emitter(ingest: Path, source_slug: str, host_slug: str) -> None:
    if source_slug == host_slug:
        return
    host_dir = ingest / host_slug
    if host_dir.exists():
        shutil.rmtree(host_dir)
    shutil.copytree(ingest / source_slug, host_dir)
    for lane in ("front", "back"):
        manifest_path = host_dir / lane / "manifest.json"
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest["species"] = host_slug
        manifest["soulgold_host_slug"] = host_slug
        manifest["showdown_source_slug"] = source_slug
        manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


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
    skipped_source_mismatch = []
    for row in catalog["rows"]:
        if not row.get("runtime_candidate", row.get("runtime_exact_candidate", False)):
            continue
        source_front = row.get("front_source_slug") or row["slug"]
        source_back = row.get("back_source_slug") or row["slug"]
        if source_front != source_back:
            skipped_source_mismatch.append({
                "slug": row["slug"],
                "front_source_slug": source_front,
                "back_source_slug": source_back,
            })
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
        host_slug = row["slug"]
        source_slug = row.get("front_source_slug") or host_slug
        host_palette = soulgold / "graphics" / "pokemon" / host_slug / "normal.pal"
        cmd = [
            sys.executable, str(framework / "tools" / "showdown_sprites_ingest.py"),
            "--zip", str(args.sprites_zip),
            "--output", str(ingest),
            "--species", source_slug,
            "--lanes", "front", "back",
            "--host-palette", str(host_palette),
        ]
        if not first:
            cmd.append("--force")
        run(cmd)
        first = False

        front_pngs = copy_lane(ingest, staging, source_slug, host_slug, "front")
        back_pngs = copy_lane(ingest, staging, source_slug, host_slug, "back")
        mirror_ingest_for_emitter(ingest, source_slug, host_slug)
        c_path = src / f"showdown_{host_slug}_idle.c"
        run([
            sys.executable, str(framework / "tools" / "emit_soulgold_showdown_s1_c.py"),
            "--ingest-root", str(ingest),
            "--species", host_slug,
            "--lanes", "front", "back",
            "--asset-root", f"graphics/showdown/{host_slug}",
            "--output", str(c_path),
        ])
        converted.append({
            "slug": host_slug,
            "showdown_source_slug": source_slug,
            "match_kind": row.get("front_match_kind", "exact"),
            "species_constant": row["species_constant"],
            "front_frames": row["front_frames"],
            "back_frames": row["back_frames"],
            "front_pngs": front_pngs,
            "back_pngs": back_pngs,
            "descriptor": str(c_path.relative_to(staging)),
        })

    summary = {
        "format": "soulgold-showdown-bulk-batch-v2",
        "soulgold_revision": SOULGOLD_REV,
        "candidate_count": len(candidates),
        "batch_index": args.batch_index,
        "batch_size": args.batch_size,
        "slice_start": start,
        "slice_end_exclusive": end,
        "converted_count": len(converted),
        "converted": converted,
        "skipped_over_255_frame_lanes": skipped_overflow,
        "skipped_front_back_source_slug_mismatch": skipped_source_mismatch,
        "runtime_status": "ASSET_CONVERSION_ONLY_NOT_YET_LINKED",
        "ownership_reference": "authority/SHOWDOWN_S1E_OWNERSHIP_AND_PMD_PORT_RULES_20260829.md",
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
