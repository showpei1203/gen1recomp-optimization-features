#!/usr/bin/env python3
"""Compute safely reclaimable SoulGold battler graphics from actual SpeciesInfo pointers.

The candidate catalog and native ELF symbol sizes come from already-recorded Actions
artifacts. Graphic symbols are counted once globally and are reclaimable only when
all SpeciesInfo users of that symbol are migration candidates.
"""
from __future__ import annotations

import argparse
import json
import re
from collections import defaultdict
from pathlib import Path

ENTRY_RE = re.compile(r"^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{", re.M)
FRONT_RE = re.compile(r"\.frontPic\s*=\s*(gMonFrontPic_[A-Za-z0-9_]+)")
BACK_RE = re.compile(r"\.backPic\s*=\s*(gMonBackPic_[A-Za-z0-9_]+)")


def parse_species_info(root: Path):
    exact = {}
    ambiguous = {}
    possible_users = defaultdict(set)
    files = sorted(p for p in root.glob("src/data/pokemon/species_info/*.h") if "families" in p.name)
    if not files:
        raise SystemExit("no species_info family files found")

    mappings = defaultdict(set)
    for path in files:
        text = path.read_text(encoding="utf-8")
        starts = list(ENTRY_RE.finditer(text))
        for i, m in enumerate(starts):
            species = m.group(1)
            end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
            block = text[m.start():end]
            fronts = sorted(set(FRONT_RE.findall(block)))
            backs = sorted(set(BACK_RE.findall(block)))
            for symbol in fronts + backs:
                possible_users[symbol].add(species)
            if len(fronts) == 1 and len(backs) == 1:
                mappings[species].add((fronts[0], backs[0]))
            else:
                ambiguous[species] = {"front": fronts, "back": backs}

    for species, values in mappings.items():
        if len(values) == 1:
            exact[species] = next(iter(values))
        else:
            ambiguous[species] = {
                "front": sorted({x[0] for x in values}),
                "back": sorted({x[1] for x in values}),
            }
    for species in ambiguous:
        exact.pop(species, None)
    return exact, ambiguous, possible_users, files


def load_symbol_sizes(path: Path):
    data = json.loads(path.read_text(encoding="utf-8"))
    sizes = {}
    for row in data.get("symbols", []):
        name = row.get("name", "")
        if name.startswith("gMonFrontPic_") or name.startswith("gMonBackPic_"):
            size = int(row["bytes"])
            if name in sizes and sizes[name] != size:
                raise SystemExit(f"conflicting recorded size for {name}")
            sizes[name] = size
    if len(sizes) < 2000:
        raise SystemExit(f"native symbol evidence unexpectedly small: {len(sizes)}")
    return sizes, data


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--budget-baseline", type=Path, required=True)
    ap.add_argument("--native-budget-json", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    baseline = json.loads(args.budget_baseline.read_text(encoding="utf-8"))
    symbol_sizes, native_evidence = load_symbol_sizes(args.native_budget_json)
    rows = [r for r in catalog["rows"] if r.get("runtime_candidate", False)]
    candidates = {r["species_constant"] for r in rows}
    if len(candidates) != 1002 or len(candidates) != len(rows):
        raise SystemExit(f"candidate set mismatch: {len(candidates)} / {len(rows)}")

    exact, ambiguous, users, source_files = parse_species_info(args.soulgold)
    mapped = {s: exact[s] for s in candidates if s in exact}
    missing = sorted(candidates - set(exact) - set(ambiguous))
    candidate_ambiguous = [
        {"species": s, **ambiguous[s]} for s in sorted(candidates & set(ambiguous))
    ]

    requested = {symbol for pair in mapped.values() for symbol in pair}
    reclaimable = []
    blocked_shared = []
    missing_symbol = []
    for symbol in sorted(requested):
        symbol_users = users.get(symbol, set())
        outside = sorted(symbol_users - candidates)
        if outside:
            blocked_shared.append({
                "symbol": symbol,
                "size": symbol_sizes.get(symbol),
                "users": sorted(symbol_users),
                "outside_candidate_users": outside,
            })
            continue
        size = symbol_sizes.get(symbol)
        if size is None:
            missing_symbol.append({"symbol": symbol, "users": sorted(symbol_users)})
            continue
        reclaimable.append({"symbol": symbol, "size": size, "users": sorted(symbol_users)})

    safe_reclaim = sum(x["size"] for x in reclaimable)
    budgets = {}
    for k, incremental in baseline["sampled_incremental_bytes"].items():
        projected = (
            int(baseline["clean_used_bytes"]) - safe_reclaim
            + int(baseline["showdown_frame0_bytes"]) + int(incremental)
            + int(baseline["registry_bytes"]) + int(baseline["runtime_reserve_bytes"])
        )
        headroom = int(baseline["rom_limit_bytes"]) - projected
        budgets[str(k)] = {
            "projected_used_bytes": projected,
            "projected_used_mib": round(projected / 1048576, 4),
            "headroom_bytes": headroom,
            "headroom_mib": round(headroom / 1048576, 4),
            "fits_32mib": headroom >= 0,
        }

    report = {
        "format": "soulgold-showdown-native-reclaim-species-info-v2",
        "soulgold_revision": baseline["soulgold_revision"],
        "source_full_budget_run_id": baseline["source_run_id"],
        "source_full_budget_artifact_id": baseline["source_artifact_id"],
        "native_symbol_evidence": {
            "rom_bytes": native_evidence["rom_bytes"],
            "linked_front_symbol_count": native_evidence["linked_front_symbol_count"],
            "linked_back_symbol_count": native_evidence["linked_back_symbol_count"],
            "linked_front_back_payload_bytes": native_evidence["linked_front_back_payload_bytes"],
        },
        "runtime_candidate_count": len(candidates),
        "species_info_source_files": [str(p.relative_to(args.soulgold)) for p in source_files],
        "species_info_exact_mapping_count": len(exact),
        "candidate_exact_mapping_count": len(mapped),
        "candidate_missing_count": len(missing),
        "candidate_missing": missing,
        "candidate_ambiguous_count": len(candidate_ambiguous),
        "candidate_ambiguous": candidate_ambiguous,
        "requested_unique_graphic_symbol_count": len(requested),
        "reclaimable_unique_graphic_symbol_count": len(reclaimable),
        "blocked_shared_symbol_count": len(blocked_shared),
        "missing_recorded_symbol_count": len(missing_symbol),
        "safe_native_reclaim_bytes": safe_reclaim,
        "safe_native_reclaim_mib": round(safe_reclaim / 1048576, 4),
        "previous_name_guess_native_reclaim_bytes": baseline["previous_name_guess_native_reclaim_bytes"],
        "reclaim_delta_vs_previous_bytes": safe_reclaim - int(baseline["previous_name_guess_native_reclaim_bytes"]),
        "reclaimable_symbols": reclaimable,
        "blocked_shared_symbols": blocked_shared,
        "missing_recorded_symbols": missing_symbol,
        "budgets": budgets,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "runtime_candidate_count": len(candidates),
        "candidate_exact_mapping_count": len(mapped),
        "candidate_missing_count": len(missing),
        "candidate_ambiguous_count": len(candidate_ambiguous),
        "reclaimable_unique_graphic_symbol_count": len(reclaimable),
        "blocked_shared_symbol_count": len(blocked_shared),
        "missing_recorded_symbol_count": len(missing_symbol),
        "safe_native_reclaim_bytes": safe_reclaim,
        "safe_native_reclaim_mib": round(safe_reclaim / 1048576, 4),
        "reclaim_delta_vs_previous_bytes": report["reclaim_delta_vs_previous_bytes"],
        "budgets": budgets,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
