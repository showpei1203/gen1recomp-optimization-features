#!/usr/bin/env python3
"""Quantify whether the current PMD frame-storage model can scale to the roster.

The prototype currently stages a 64x64 4bpp body frame (2048 bytes) plus a
32x8 4bpp PMD shadow frame (128 bytes) for each animation frame. That geometry
is excellent for proving ownership but very expensive for a nearly-full 32 MiB
GBA ROM.

This gate compares the actual trailing 0xFF budget of a built SoulGold ROM with:
1. the current fixed-64x64 representation;
2. a tile-aligned source-rectangle lower geometry estimate, before compression.

It does not claim compressed size. Its job is to decide whether batch-converting
hundreds of species with the prototype representation is architecturally sane.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

BODY_FIXED_BYTES = 64 * 64 // 2
SHADOW_FIXED_BYTES = 32 * 8 // 2
SIDES = 2


def trailing_ff(path: Path) -> tuple[int, int]:
    data = path.read_bytes()
    idx = len(data) - 1
    while idx >= 0 and data[idx] == 0xFF:
        idx -= 1
    return idx + 1, len(data) - (idx + 1)


def tiled_body_bytes(frame_size: list[int]) -> int:
    w, h = frame_size
    return math.ceil(w / 8) * math.ceil(h / 8) * 32


def estimate(records: list[dict], actions: tuple[str, ...]) -> dict:
    eligible = []
    fixed = 0
    tiled = 0
    frame_total = 0
    missing_action_species = 0
    for rec in records:
        ars = rec.get("actions", {})
        selected = []
        complete = True
        for action in actions:
            ar = ars.get(action)
            if not ar or not ar.get("available"):
                complete = False
                break
            selected.append(ar)
        if not complete:
            missing_action_species += 1
            continue
        eligible.append(rec["national_dex"])
        for ar in selected:
            frames = int(ar["frame_count"])
            frame_total += frames * SIDES
            fixed += frames * SIDES * (BODY_FIXED_BYTES + SHADOW_FIXED_BYTES)
            tiled += frames * SIDES * (tiled_body_bytes(ar["frame_size"]) + SHADOW_FIXED_BYTES)
    return {
        "actions": list(actions),
        "species_with_complete_action_set": len(eligible),
        "species_missing_one_or_more_actions": missing_action_species,
        "side_frame_instances": frame_total,
        "current_fixed_bytes_uncompressed": fixed,
        "source_tile_rect_bytes_uncompressed": tiled,
        "eligible_national_dex": eligible,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--coverage", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    coverage = json.loads(args.coverage.read_text(encoding="utf-8"))
    used, free = trailing_ff(args.rom)
    rom_size = args.rom.stat().st_size
    if rom_size != 32 * 1024 * 1024:
        raise SystemExit(f"expected 32 MiB GBA ROM, got {rom_size}")

    estimates = {
        "ambient_minimum": estimate(coverage["records"], ("Idle", "Walk")),
        "combat_core": estimate(coverage["records"], ("Idle", "Walk", "Hurt", "Attack", "Shoot")),
        "prototype_full_capability": estimate(
            coverage["records"],
            ("Idle", "Walk", "Hurt", "Attack", "Shoot", "Nod", "Rotate", "Sleep", "EventSleep", "Wake"),
        ),
    }
    for item in estimates.values():
        item["fixed_vs_free_ratio"] = round(item["current_fixed_bytes_uncompressed"] / free, 3) if free else None
        item["tiled_vs_free_ratio"] = round(item["source_tile_rect_bytes_uncompressed"] / free, 3) if free else None

    current_core = estimates["combat_core"]["current_fixed_bytes_uncompressed"]
    decision = (
        "PACKED_FRAME_ARCHITECTURE_REQUIRED_BEFORE_LARGE_BATCH"
        if current_core > free
        else "CURRENT_FRAME_ARCHITECTURE_HAS_NOMINAL_RAW_BUDGET"
    )
    out = {
        "phase": "G4C_ROM_STORAGE_BUDGET",
        "rom_bytes": rom_size,
        "last_non_ff_plus_one": used,
        "trailing_ff_free_bytes": free,
        "free_mib": round(free / (1024 * 1024), 3),
        "current_body_frame_bytes": BODY_FIXED_BYTES,
        "current_shadow_frame_bytes": SHADOW_FIXED_BYTES,
        "sides_per_species": SIDES,
        "coverage_phase": coverage.get("phase"),
        "coverage_counts": coverage.get("counts"),
        "estimates": estimates,
        "decision": decision,
        "required_next": (
            "Use variable/tight tile payloads plus frame/tile dedup or deltas; "
            "do not blindly emit a 64x64 body blob per frame for the National Dex."
        ),
        "hard_fallback": "Any species/action not safely packed remains SoulGold-native.",
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: out[k] for k in ("trailing_ff_free_bytes", "free_mib", "decision")}, indent=2))
    for name, rec in estimates.items():
        print(name, rec["species_with_complete_action_set"], rec["current_fixed_bytes_uncompressed"], rec["source_tile_rect_bytes_uncompressed"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
