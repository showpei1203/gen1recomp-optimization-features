#!/usr/bin/env python3
"""Compute safely reclaimable SoulGold native battler graphics from SpeciesInfo.

This audit deliberately does not infer graphic symbols from Showdown/host slugs.
It parses the actual `.frontPic` / `.backPic` assignments in SoulGold species_info,
then counts an ELF graphic symbol at most once. A shared symbol is reclaimable only
when every SpeciesInfo entry that can reference it is in the migration candidate set.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from collections import defaultdict
from pathlib import Path

SPECIES_ENTRY_RE = re.compile(r"^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*\{", re.M)
FRONT_RE = re.compile(r"\.frontPic\s*=\s*(gMonFrontPic_[A-Za-z0-9_]+)")
BACK_RE = re.compile(r"\.backPic\s*=\s*(gMonBackPic_[A-Za-z0-9_]+)")
NM_RE = re.compile(r"^[0-9A-Fa-f]+\s+([0-9A-Fa-f]+)\s+\S\s+(gMon(?:Front|Back)Pic_[A-Za-z0-9_]+)$")


def parse_species_info(root: Path):
    """Return exact mappings plus every possible symbol user seen in source."""
    exact: dict[str, tuple[str, str]] = {}
    ambiguous: dict[str, dict[str, list[str]]] = {}
    possible_users: dict[str, set[str]] = defaultdict(set)
    source_files = sorted(root.glob("src/data/pokemon/species_info/*.h"))
    source_files = [p for p in source_files if "families" in p.name]
    if not source_files:
        raise SystemExit("no species_info family files found")

    duplicate_exact: dict[str, set[tuple[str, str]]] = defaultdict(set)
    for path in source_files:
        text = path.read_text(encoding="utf-8")
        starts = list(SPECIES_ENTRY_RE.finditer(text))
        for i, m in enumerate(starts):
            species = m.group(1)
            end = starts[i + 1].start() if i + 1 < len(starts) else len(text)
            block = text[m.start():end]
            fronts = sorted(set(FRONT_RE.findall(block)))
            backs = sorted(set(BACK_RE.findall(block)))
            for symbol in fronts + backs:
                possible_users[symbol].add(species)
            if len(fronts) == 1 and len(backs) == 1:
                duplicate_exact[species].add((fronts[0], backs[0]))
            else:
                ambiguous.setdefault(species, {"front": [], "back": []})
                ambiguous[species]["front"] = sorted(set(ambiguous[species]["front"]) | set(fronts))
                ambiguous[species]["back"] = sorted(set(ambiguous[species]["back"]) | set(backs))

    duplicate_conflicts = {}
    for species, mappings in duplicate_exact.items():
        if len(mappings) == 1:
            exact[species] = next(iter(mappings))
        else:
            duplicate_conflicts[species] = [list(x) for x in sorted(mappings)]
            exact.pop(species, None)
    for species in duplicate_conflicts:
        ambiguous[species] = {
            "front": sorted({x[0] for x in duplicate_exact[species]}),
            "back": sorted({x[1] for x in duplicate_exact[species]}),
        }
    return exact, ambiguous, possible_users, source_files


def parse_nm(elf: Path, nm: str) -> dict[str, int]:
    text = subprocess.check_output([nm, "-S", "--defined-only", str(elf)], text=True, errors="replace")
    sizes: dict[str, int] = {}
    duplicate_conflicts = {}
    for line in text.splitlines():
        m = NM_RE.match(line.strip())
        if not m:
            continue
        size = int(m.group(1), 16)
        symbol = m.group(2)
        if symbol in sizes and sizes[symbol] != size:
            duplicate_conflicts.setdefault(symbol, {sizes[symbol]}).add(size)
        sizes[symbol] = size
    if duplicate_conflicts:
        raise SystemExit(f"conflicting nm symbol sizes: {duplicate_conflicts}")
    return sizes


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--budget-baseline", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--elf", type=Path, required=True)
    ap.add_argument("--nm", default="arm-none-eabi-nm")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    authority = json.loads(args.budget_baseline.read_text(encoding="utf-8"))
    candidate_rows = [r for r in catalog["rows"] if r.get("runtime_candidate", False)]
    candidate_set = {r["species_constant"] for r in candidate_rows}
    if len(candidate_set) != len(candidate_rows):
        raise SystemExit("duplicate runtime candidate constants")

    exact, ambiguous, possible_users, source_files = parse_species_info(args.soulgold)
    nm_sizes = parse_nm(args.elf, args.nm)

    candidate_missing = []
    candidate_ambiguous = []
    candidate_mapped: dict[str, tuple[str, str]] = {}
    for species in sorted(candidate_set):
        mapping = exact.get(species)
        if mapping is not None:
            candidate_mapped[species] = mapping
        elif species in ambiguous:
            candidate_ambiguous.append({"species": species, **ambiguous[species]})
        else:
            candidate_missing.append(species)

    requested_symbols = set()
    for front, back in candidate_mapped.values():
        requested_symbols.add(front)
        requested_symbols.add(back)

    reclaimable = []
    blocked_shared = []
    missing_nm = []
    no_users = []
    for symbol in sorted(requested_symbols):
        users = possible_users.get(symbol, set())
        if not users:
            no_users.append(symbol)
            continue
        outside = sorted(users - candidate_set)
        if outside:
            blocked_shared.append({
                "symbol": symbol,
                "users": sorted(users),
                "outside_candidate_users": outside,
                "size": nm_sizes.get(symbol),
            })
            continue
        size = nm_sizes.get(symbol)
        if size is None:
            missing_nm.append({"symbol": symbol, "users": sorted(users)})
            continue
        reclaimable.append({"symbol": symbol, "size": size, "users": sorted(users)})

    safe_reclaim = sum(x["size"] for x in reclaimable)
    old_reclaim = int(authority["previous_name_guess_native_reclaim_bytes"])
    budgets = {}
    for k, incremental in authority["sampled_incremental_bytes"].items():
        projected = (
            int(authority["clean_used_bytes"])
            - safe_reclaim
            + int(authority["showdown_frame0_bytes"])
            + int(incremental)
            + int(authority["registry_bytes"])
            + int(authority["runtime_reserve_bytes"])
        )
        budgets[str(k)] = {
            "projected_used_bytes": projected,
            "projected_used_mib": round(projected / 1048576, 4),
            "headroom_bytes": int(authority["rom_limit_bytes"]) - projected,
            "headroom_mib": round((int(authority["rom_limit_bytes"]) - projected) / 1048576, 4),
            "fits_32mib": projected <= int(authority["rom_limit_bytes"]),
        }

    report = {
        "format": "soulgold-showdown-native-reclaim-species-info-v1",
        "soulgold_revision": authority["soulgold_revision"],
        "source_run_id": authority["source_run_id"],
        "source_artifact_id": authority["source_artifact_id"],
        "runtime_candidate_count": len(candidate_set),
        "species_info_source_files": [str(p.relative_to(args.soulgold)) for p in source_files],
        "species_info_exact_mapping_count": len(exact),
        "species_info_ambiguous_count": len(ambiguous),
        "candidate_exact_mapping_count": len(candidate_mapped),
        "candidate_missing_count": len(candidate_missing),
        "candidate_missing": candidate_missing,
        "candidate_ambiguous_count": len(candidate_ambiguous),
        "candidate_ambiguous": candidate_ambiguous,
        "requested_unique_graphic_symbols": len(requested_symbols),
        "reclaimable_unique_graphic_symbol_count": len(reclaimable),
        "blocked_shared_symbol_count": len(blocked_shared),
        "missing_nm_symbol_count": len(missing_nm),
        "no_user_symbol_count": len(no_users),
        "safe_native_reclaim_bytes": safe_reclaim,
        "safe_native_reclaim_mib": round(safe_reclaim / 1048576, 4),
        "previous_name_guess_native_reclaim_bytes": old_reclaim,
        "reclaim_delta_vs_previous_bytes": safe_reclaim - old_reclaim,
        "reclaimable_symbols": reclaimable,
        "blocked_shared_symbols": blocked_shared,
        "missing_nm_symbols": missing_nm,
        "no_user_symbols": no_users,
        "budgets": budgets,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")

    print(json.dumps({
        "runtime_candidate_count": len(candidate_set),
        "candidate_exact_mapping_count": len(candidate_mapped),
        "candidate_missing_count": len(candidate_missing),
        "candidate_ambiguous_count": len(candidate_ambiguous),
        "reclaimable_unique_graphic_symbol_count": len(reclaimable),
        "blocked_shared_symbol_count": len(blocked_shared),
        "missing_nm_symbol_count": len(missing_nm),
        "safe_native_reclaim_bytes": safe_reclaim,
        "safe_native_reclaim_mib": round(safe_reclaim / 1048576, 4),
        "reclaim_delta_vs_previous_bytes": safe_reclaim - old_reclaim,
        "budgets": budgets,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
