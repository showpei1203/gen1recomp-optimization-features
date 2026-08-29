#!/usr/bin/env python3
"""Inventory all SoulGold species against official Pokemon Showdown animated GIFs.

Exact final-directory filename matches are preferred. When SoulGold uses an
underscore/punctuation spelling that differs from Showdown (mr_mime vs mrmime,
ho_oh vs hooh, brute_bonnet vs brute-bonnet), a unique punctuation-insensitive
match is accepted and recorded explicitly. Ambiguous aliases are never guessed.
"""
from __future__ import annotations

import argparse
import csv
import io
import json
import re
import zipfile
from collections import Counter, defaultdict
from pathlib import Path, PurePosixPath

from PIL import Image

SOULGOLD_REV = "77ec3fc6275bb94dd703f4c1976f1457cc44a60b"
LANE_DIRS = {
    "front": "ani",
    "back": "ani-back",
    "front-shiny": "ani-shiny",
    "back-shiny": "ani-back-shiny",
}
RAW_FRAME_BYTES = 64 * 64 // 2


def parse_species_constants(path: Path) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(r"\bSPECIES_[A-Z0-9_]+\b", text))


def slug_constant(slug: str) -> str:
    return "SPECIES_" + re.sub(r"[^A-Z0-9]+", "_", slug.upper()).strip("_")


def normalize_slug(slug: str) -> str:
    return re.sub(r"[^a-z0-9]", "", slug.lower())


def zip_lane_index(zf: zipfile.ZipFile):
    exact = {lane: {} for lane in LANE_DIRS}
    normalized = {lane: defaultdict(list) for lane in LANE_DIRS}
    dir_to_lane = {v.lower(): k for k, v in LANE_DIRS.items()}
    for name in zf.namelist():
        parts = PurePosixPath(name).parts
        if len(parts) < 2 or not parts[-1].lower().endswith(".gif"):
            continue
        lane = dir_to_lane.get(parts[-2].lower())
        if lane is None:
            continue
        stem = parts[-1][:-4].lower()
        if stem not in exact[lane]:
            exact[lane][stem] = name
            normalized[lane][normalize_slug(stem)].append((stem, name))
    return exact, normalized


def resolve_member(exact, normalized, lane: str, host_slug: str):
    member = exact[lane].get(host_slug)
    if member is not None:
        return host_slug, member, "exact"
    matches = normalized[lane].get(normalize_slug(host_slug), [])
    if len(matches) == 1:
        stem, member = matches[0]
        return stem, member, "normalized_unique_alias"
    if len(matches) > 1:
        return None, None, "ambiguous_alias"
    return None, None, "missing"


def gif_meta(zf: zipfile.ZipFile, member: str) -> tuple[int, int, int]:
    with Image.open(io.BytesIO(zf.read(member))) as im:
        return int(getattr(im, "n_frames", 1)), int(im.size[0]), int(im.size[1])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--sprites-zip", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output-json", type=Path, required=True)
    ap.add_argument("--output-csv", type=Path, required=True)
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    graphics = soulgold / "graphics" / "pokemon"
    constants = parse_species_constants(soulgold / "include" / "constants" / "species.h")
    host_species = sorted(p.name for p in graphics.iterdir() if p.is_dir() and (p / "normal.pal").is_file())
    rows: list[dict] = []
    lane_resolved_totals = Counter()
    lane_exact_totals = Counter()
    lane_alias_totals = Counter()
    raw_total = 0

    with zipfile.ZipFile(args.sprites_zip) as zf:
        exact, normalized = zip_lane_index(zf)
        for slug in host_species:
            constant = slug_constant(slug)
            row: dict[str, object] = {
                "slug": slug,
                "species_constant": constant,
                "species_constant_exists": constant in constants,
                "normal_palette": True,
                "shiny_palette": (graphics / slug / "shiny.pal").is_file(),
            }
            species_raw = 0
            for lane in LANE_DIRS:
                source_slug, member, match_kind = resolve_member(exact, normalized, lane, slug)
                present = member is not None
                row[f"{lane}_present"] = present
                row[f"{lane}_source_slug"] = source_slug or ""
                row[f"{lane}_match_kind"] = match_kind
                row[f"{lane}_frames"] = 0
                row[f"{lane}_source_w"] = 0
                row[f"{lane}_source_h"] = 0
                row[f"{lane}_raw_4bpp_bytes"] = 0
                if present:
                    frames, w, h = gif_meta(zf, member)
                    raw = frames * RAW_FRAME_BYTES
                    row[f"{lane}_frames"] = frames
                    row[f"{lane}_source_w"] = w
                    row[f"{lane}_source_h"] = h
                    row[f"{lane}_raw_4bpp_bytes"] = raw
                    species_raw += raw
                    lane_resolved_totals[lane] += 1
                    if match_kind == "exact":
                        lane_exact_totals[lane] += 1
                    elif match_kind == "normalized_unique_alias":
                        lane_alias_totals[lane] += 1
            row["normal_pair"] = bool(row["front_present"] and row["back_present"])
            row["normal_pair_same_source_slug"] = bool(
                row["normal_pair"] and row["front_source_slug"] == row["back_source_slug"]
            )
            row["shiny_pair"] = bool(row["front-shiny_present"] and row["back-shiny_present"] and row["shiny_palette"])
            row["runtime_candidate"] = bool(
                row["normal_pair"] and row["normal_pair_same_source_slug"] and row["species_constant_exists"]
            )
            row["runtime_exact_candidate"] = bool(
                row["runtime_candidate"]
                and row["front_match_kind"] == "exact"
                and row["back_match_kind"] == "exact"
            )
            row["raw_4bpp_bytes_all_present_lanes"] = species_raw
            raw_total += species_raw
            rows.append(row)

    candidates = [r for r in rows if r["runtime_candidate"]]
    exact_candidates = [r for r in rows if r["runtime_exact_candidate"]]
    alias_candidates = [r for r in candidates if not r["runtime_exact_candidate"]]
    missing_pair = [r["slug"] for r in rows if not r["normal_pair"]]
    ambiguous = [
        {"slug": r["slug"], "lane": lane}
        for r in rows for lane in LANE_DIRS if r[f"{lane}_match_kind"] == "ambiguous_alias"
    ]
    constant_mismatch = [r["slug"] for r in rows if r["normal_pair"] and not r["species_constant_exists"]]
    over_255 = []
    for r in rows:
        for lane in LANE_DIRS:
            if int(r[f"{lane}_frames"]) > 255:
                over_255.append({"slug": r["slug"], "lane": lane, "frames": r[f"{lane}_frames"]})

    report = {
        "format": "soulgold-showdown-bulk-catalog-v2",
        "soulgold_revision": SOULGOLD_REV,
        "host_species_with_normal_palette": len(rows),
        "runtime_candidates_normal_front_back": len(candidates),
        "runtime_exact_candidates_normal_front_back": len(exact_candidates),
        "runtime_alias_candidates_normal_front_back": len(alias_candidates),
        "normal_pair_missing_count": len(missing_pair),
        "ambiguous_alias_count": len(ambiguous),
        "species_constant_mismatch_count": len(constant_mismatch),
        "lane_resolved_species_counts": dict(lane_resolved_totals),
        "lane_exact_species_counts": dict(lane_exact_totals),
        "lane_alias_species_counts": dict(lane_alias_totals),
        "raw_4bpp_bytes_all_present_lanes": raw_total,
        "raw_4bpp_mib_all_present_lanes": round(raw_total / 1048576, 3),
        "frame_count_over_255": over_255,
        "normal_pair_missing": missing_pair,
        "ambiguous_aliases": ambiguous,
        "species_constant_mismatch": constant_mismatch,
        "alias_candidates": [
            {
                "slug": r["slug"],
                "showdown_source_slug": r["front_source_slug"],
                "front_match_kind": r["front_match_kind"],
                "back_match_kind": r["back_match_kind"],
            }
            for r in alias_candidates
        ],
        "rows": rows,
    }

    args.output_json.parent.mkdir(parents=True, exist_ok=True)
    args.output_json.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    fields = list(rows[0].keys()) if rows else ["slug"]
    with args.output_csv.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)

    print(json.dumps({k: report[k] for k in (
        "host_species_with_normal_palette",
        "runtime_candidates_normal_front_back",
        "runtime_exact_candidates_normal_front_back",
        "runtime_alias_candidates_normal_front_back",
        "normal_pair_missing_count",
        "ambiguous_alias_count",
        "species_constant_mismatch_count",
        "lane_resolved_species_counts",
        "lane_alias_species_counts",
        "raw_4bpp_mib_all_present_lanes",
    )}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
