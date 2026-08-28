#!/usr/bin/env python3
"""Audit per-action GBA-LZ77 compression of exact PMD body delta streams.

G4E showed that exact changed-byte patches are runtime-simple but occupy about
15 MiB when stored raw. G4E2 keeps the same lossless body reconstruction model,
but concatenates each action's frame patches and BIOS-LZ77 compresses that
stream. At action bind the stream can be decompressed to EWRAM, then frame
patches are applied sequentially to the 2048-byte HOME-derived body scratch.

This is storage/RAM evidence only. It activates no additional battlers.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import audit_soulgold_g4a_pmd_roster_coverage as g4a
import audit_soulgold_g4e_delta_pack as g4e

CORE_ACTIONS = g4e.CORE_ACTIONS
VIEWS = g4e.VIEWS
FRAME_DESC_BYTES = 8
ACTION_DESC_BYTES = 16  # compressed ptr, compressed bytes, raw bytes, marker/meta
PROFILE_FIXED_BYTES = g4e.PROFILE_FIXED_BYTES
PALETTE_BYTES = g4e.PALETTE_BYTES
SHADOW_FRAME_META_BYTES = g4e.SHADOW_FRAME_META_BYTES
SHADOW_SPECIES_BYTES = g4e.SHADOW_SPECIES_BYTES
SHARED_SHADOW_MASK_BYTES = g4e.SHARED_SHADOW_MASK_BYTES


def side_storage(rendered: dict, colors) -> dict:
    palette = g4e.build_palette(colors)
    color_to_index = {
        c: (palette.index(c) + 1 if c in palette else g4e.nearest(c, palette))
        for c in colors
    }
    packed = {
        action: [g4e.pack_sparse_4bpp(fr["pixels"], color_to_index) for fr in rendered[action]["frames"]]
        for action in CORE_ACTIONS
    }
    home = packed["Idle"][0]
    home_lz = g4e.gba_lz77(home)

    action_records = {}
    compressed_total = 0
    raw_total = 0
    changed_payload = 0
    max_raw_action = 0
    max_compressed_action = 0
    frame_count = 0

    for action in CORE_ACTIONS:
        previous = home
        stream = bytearray()
        offsets = []
        for current in packed[action]:
            offsets.append(len(stream))
            patch = g4e.patch_runs(previous, current)
            if g4e.apply_patch(previous, patch) != current:
                raise ValueError(f"patch reconstruction failed: {action}")
            stream.extend(patch)
            j = 0
            while j < len(patch):
                ln = patch[j + 2]
                changed_payload += ln
                j += 3 + ln
            previous = current
            frame_count += 1
        if len(stream) > 0xFFFF:
            raise ValueError(f"{action} raw patch stream exceeds u16 frame-offset range: {len(stream)}")
        compressed = g4e.gba_lz77(bytes(stream))
        raw_total += len(stream)
        compressed_total += len(compressed)
        max_raw_action = max(max_raw_action, len(stream))
        max_compressed_action = max(max_compressed_action, len(compressed))
        action_records[action] = {
            "frames": len(packed[action]),
            "raw_patch_stream_bytes": len(stream),
            "lz77_patch_stream_bytes": len(compressed),
            "frame_patch_offsets": offsets,
        }

    frame_desc = frame_count * FRAME_DESC_BYTES
    action_desc = len(CORE_ACTIONS) * ACTION_DESC_BYTES
    shadow_meta = frame_count * SHADOW_FRAME_META_BYTES + SHADOW_SPECIES_BYTES
    total = (
        len(home_lz) + compressed_total + frame_desc + action_desc
        + PROFILE_FIXED_BYTES + PALETTE_BYTES + shadow_meta
    )
    return {
        "palette_source_colors": len(colors),
        "palette_visible_colors": len(palette),
        "home_lz_bytes": len(home_lz),
        "raw_patch_stream_bytes": raw_total,
        "lz77_patch_stream_bytes": compressed_total,
        "changed_payload_bytes": changed_payload,
        "frame_count": frame_count,
        "frame_descriptor_bytes": frame_desc,
        "action_descriptor_bytes": action_desc,
        "profile_fixed_bytes": PROFILE_FIXED_BYTES,
        "palette_bytes": PALETTE_BYTES,
        "shadow_metadata_bytes": shadow_meta,
        "max_raw_action_stream_bytes": max_raw_action,
        "max_lz77_action_stream_bytes": max_compressed_action,
        "total_bytes": total,
        "actions": action_records,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--g4d-audit", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    sprite_root = args.spritecollab.resolve() / "sprite"
    gate = json.loads(args.g4d_audit.read_text(encoding="utf-8"))
    dex_names = g4a.parse_national_dex(soulgold / "include/constants/pokedex.h")
    by_dex = {int(r["national_dex"]): r for r in gate["records"]}

    totals = {
        "eligible_species": 0,
        "species_side_packs": 0,
        "frames": 0,
        "home_lz_bytes": 0,
        "raw_patch_stream_bytes": 0,
        "lz77_patch_stream_bytes": 0,
        "changed_payload_bytes": 0,
        "descriptor_bytes": 0,
        "profile_bytes": 0,
        "palette_bytes": 0,
        "shadow_metadata_bytes": SHARED_SHADOW_MASK_BYTES,
        "packed_total_bytes": SHARED_SHADOW_MASK_BYTES,
        "max_raw_action_stream_bytes": 0,
        "max_lz77_action_stream_bytes": 0,
    }
    species_records = []

    for dex, dex_name in enumerate(dex_names, 1):
        audit_rec = by_dex[dex]
        if audit_rec["eligibility"] != "LOSSLESS_SINGLE_OBJ_BOTH_SIDES":
            continue
        species_dir = sprite_root / f"{dex:04d}"
        actions = g4a.parse_anim_data_compat(species_dir / "AnimData.xml")
        rec = {
            "national_dex": dex,
            "national_dex_constant": f"NATIONAL_DEX_{dex_name}",
            "sides": {},
        }
        for side, direction in VIEWS:
            anchor = tuple(int(v) for v in audit_rec["views"][side]["common_anchor"]["selected"])
            rendered, colors = g4e.render_sparse_side(species_dir, actions, direction, anchor)
            storage = side_storage(rendered, colors)
            storage["direction"] = direction
            storage["anchor"] = list(anchor)
            rec["sides"][side] = storage

            totals["species_side_packs"] += 1
            totals["frames"] += storage["frame_count"]
            totals["home_lz_bytes"] += storage["home_lz_bytes"]
            totals["raw_patch_stream_bytes"] += storage["raw_patch_stream_bytes"]
            totals["lz77_patch_stream_bytes"] += storage["lz77_patch_stream_bytes"]
            totals["changed_payload_bytes"] += storage["changed_payload_bytes"]
            totals["descriptor_bytes"] += storage["frame_descriptor_bytes"] + storage["action_descriptor_bytes"]
            totals["profile_bytes"] += storage["profile_fixed_bytes"]
            totals["palette_bytes"] += storage["palette_bytes"]
            totals["shadow_metadata_bytes"] += storage["shadow_metadata_bytes"]
            totals["packed_total_bytes"] += storage["total_bytes"]
            totals["max_raw_action_stream_bytes"] = max(
                totals["max_raw_action_stream_bytes"], storage["max_raw_action_stream_bytes"]
            )
            totals["max_lz77_action_stream_bytes"] = max(
                totals["max_lz77_action_stream_bytes"], storage["max_lz77_action_stream_bytes"]
            )
        totals["eligible_species"] += 1
        species_records.append(rec)

    free = g4e.trailing_ff_free(args.rom.resolve())
    worst_four_battler_ewram = 4 * (g4e.FRAME_BYTES + totals["max_raw_action_stream_bytes"])
    result = {
        "phase": "G4E2_ACTION_STREAM_LZ_STORAGE_AUDIT",
        "soulgold_revision": g4e.SOULGOLD_REV,
        "spritecollab_revision": g4e.SPRITECOLLAB_REV,
        "parent": "CORRECTED_G4D_LOSSLESS_SINGLE_OBJ",
        "activation_change": "NONE_AUDIT_ONLY",
        "body_storage": "HOME_GBA_LZ77_PLUS_PER_ACTION_GBA_LZ77_EXACT_PATCH_STREAM",
        "runtime_decode": "DECOMPRESS_ACTION_STREAM_TO_EWRAM_THEN_APPLY_FRAME_PATCH_OFFSETS_SEQUENTIALLY",
        "visible_pixel_policy": "G4D_100_PERCENT_OPAQUE_PIXEL_CONSERVATION",
        "fallback": "MISSING_INVALID_OR_MULTI_OBJ_REMAINS_NATIVE_SOULGOLD",
        "multi_obj": "DEFERRED",
        "rom": {"bytes": args.rom.stat().st_size, "trailing_ff_free_bytes": free},
        "totals": totals,
        "fits_current_trailing_free_space": totals["packed_total_bytes"] <= free,
        "additional_bytes_required_beyond_current_free": max(0, totals["packed_total_bytes"] - free),
        "ewram": {
            "body_scratch_bytes_per_battler": g4e.FRAME_BYTES,
            "max_action_stream_bytes_per_battler": totals["max_raw_action_stream_bytes"],
            "worst_case_four_battler_body_plus_action_stream_bytes": worst_four_battler_ewram,
        },
        "species": species_records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("G4E2 per-action LZ77 storage audit PASS")
    print(json.dumps({
        "eligible_species": totals["eligible_species"],
        "frames": totals["frames"],
        "raw_patch_stream_bytes": totals["raw_patch_stream_bytes"],
        "lz77_patch_stream_bytes": totals["lz77_patch_stream_bytes"],
        "packed_total_bytes": totals["packed_total_bytes"],
        "rom_free_bytes": free,
        "additional_required": result["additional_bytes_required_beyond_current_free"],
        "max_raw_action_stream_bytes": totals["max_raw_action_stream_bytes"],
        "worst_four_battler_ewram": worst_four_battler_ewram,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
