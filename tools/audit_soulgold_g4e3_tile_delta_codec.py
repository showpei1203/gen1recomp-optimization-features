#!/usr/bin/env python3
"""Audit a lossless tile-dictionary + delta-command PMD body codec.

A 64x64 4bpp GBA battler frame is exactly 64 tiles of 32 bytes. Instead of
storing changed pixel bytes, G4E3 stores each distinct non-transparent tile once
per species+side, then each animation frame records only tile positions that
changed from HOME/the preceding frame. The dictionary and each action command
stream are independently BIOS-LZ77 compressed.

Runtime model:
1. decompress active species-side tile dictionary into EWRAM;
2. rebuild HOME from a compact 64-entry tile-index map;
3. on action bind, decompress that action's delta command stream;
4. clear/copy only changed 8x8 tiles into the 2048-byte body scratch;
5. hand the reconstructed frame to the existing two-slot PMD presenter.

The audit reconstructs every packed frame byte-for-byte. It activates no new
species. Missing/invalid PMD and valid geometry requiring multi-OBJ stay native.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

import audit_soulgold_g4a_pmd_roster_coverage as g4a
import audit_soulgold_g4e_delta_pack as g4e

CORE_ACTIONS = g4e.CORE_ACTIONS
VIEWS = g4e.VIEWS
TILE_BYTES = 32
TILES_PER_FRAME = 64
FRAME_DESC_BYTES = 8
ACTION_DESC_BYTES = 16
PROFILE_FIXED_BYTES = g4e.PROFILE_FIXED_BYTES
PALETTE_BYTES = g4e.PALETTE_BYTES
SHADOW_FRAME_META_BYTES = g4e.SHADOW_FRAME_META_BYTES
SHADOW_SPECIES_BYTES = g4e.SHADOW_SPECIES_BYTES
SHARED_SHADOW_MASK_BYTES = g4e.SHARED_SHADOW_MASK_BYTES
ZERO_TILE = bytes(TILE_BYTES)


def split_tiles(frame: bytes) -> tuple[bytes, ...]:
    if len(frame) != g4e.FRAME_BYTES:
        raise ValueError(len(frame))
    return tuple(frame[i:i + TILE_BYTES] for i in range(0, len(frame), TILE_BYTES))


def encode_index(value: int, width: int) -> bytes:
    if width == 1:
        if not 0 <= value <= 0xFF:
            raise ValueError(value)
        return bytes((value,))
    if width == 2:
        if not 0 <= value <= 0xFFFF:
            raise ValueError(value)
        return bytes((value & 0xFF, value >> 8))
    raise ValueError(width)


def decode_index(data: bytes, pos: int, width: int) -> tuple[int, int]:
    if width == 1:
        return data[pos], pos + 1
    return data[pos] | (data[pos + 1] << 8), pos + 2


def build_packed(rendered: dict, colors):
    palette = g4e.build_palette(colors)
    color_to_index = {
        c: (palette.index(c) + 1 if c in palette else g4e.nearest(c, palette))
        for c in colors
    }
    packed = {
        action: [g4e.pack_sparse_4bpp(fr["pixels"], color_to_index) for fr in rendered[action]["frames"]]
        for action in CORE_ACTIONS
    }
    return palette, packed


def side_storage(rendered: dict, colors) -> dict:
    palette, packed = build_packed(rendered, colors)
    all_tiles = set()
    for action in CORE_ACTIONS:
        for frame in packed[action]:
            all_tiles.update(t for t in split_tiles(frame) if t != ZERO_TILE)
    dictionary = sorted(all_tiles)
    if len(dictionary) <= 255:
        index_width = 1
    elif len(dictionary) <= 65535:
        index_width = 2
    else:
        raise ValueError(f"tile dictionary too large: {len(dictionary)}")
    tile_to_index = {tile: i + 1 for i, tile in enumerate(dictionary)}  # 0 means transparent tile
    dictionary_raw = b"".join(dictionary)
    dictionary_lz = g4e.gba_lz77(dictionary_raw)

    home_tiles = split_tiles(packed["Idle"][0])
    home_map = b"".join(encode_index(0 if t == ZERO_TILE else tile_to_index[t], index_width) for t in home_tiles)

    action_records = {}
    raw_commands_total = 0
    lz_commands_total = 0
    frame_count = 0
    max_raw_action = 0
    max_lz_action = 0
    max_changed_tiles = 0

    for action in CORE_ACTIONS:
        previous = home_tiles
        stream = bytearray()
        frame_offsets = []
        for frame in packed[action]:
            current = split_tiles(frame)
            changed = [(pos, tile) for pos, (old, tile) in enumerate(zip(previous, current)) if old != tile]
            if len(changed) > 64:
                raise ValueError("impossible changed tile count")
            max_changed_tiles = max(max_changed_tiles, len(changed))
            frame_offsets.append(len(stream))
            stream.append(len(changed))
            for pos, tile in changed:
                stream.append(pos)
                idx = 0 if tile == ZERO_TILE else tile_to_index[tile]
                stream.extend(encode_index(idx, index_width))

            # Decoder proof: reconstruct from previous using the emitted command.
            test = list(previous)
            cursor = frame_offsets[-1]
            count = stream[cursor]
            cursor += 1
            for _ in range(count):
                tile_pos = stream[cursor]
                cursor += 1
                idx, cursor = decode_index(stream, cursor, index_width)
                test[tile_pos] = ZERO_TILE if idx == 0 else dictionary[idx - 1]
            if b"".join(test) != frame:
                raise ValueError(f"tile-delta reconstruction failed: {action}")
            previous = current
            frame_count += 1

        if len(stream) > 0xFFFF:
            raise ValueError(f"{action} command stream exceeds u16 offsets: {len(stream)}")
        compressed = g4e.gba_lz77(bytes(stream))
        raw_commands_total += len(stream)
        lz_commands_total += len(compressed)
        max_raw_action = max(max_raw_action, len(stream))
        max_lz_action = max(max_lz_action, len(compressed))
        action_records[action] = {
            "frames": len(packed[action]),
            "raw_command_bytes": len(stream),
            "lz77_command_bytes": len(compressed),
            "frame_offsets": frame_offsets,
        }

    frame_desc = frame_count * FRAME_DESC_BYTES
    action_desc = len(CORE_ACTIONS) * ACTION_DESC_BYTES
    shadow_meta = frame_count * SHADOW_FRAME_META_BYTES + SHADOW_SPECIES_BYTES
    total_compressed_dict = (
        len(dictionary_lz) + len(home_map) + lz_commands_total + frame_desc + action_desc
        + PROFILE_FIXED_BYTES + PALETTE_BYTES + shadow_meta
    )
    total_raw_dict = (
        len(dictionary_raw) + len(home_map) + lz_commands_total + frame_desc + action_desc
        + PROFILE_FIXED_BYTES + PALETTE_BYTES + shadow_meta
    )
    return {
        "palette_source_colors": len(colors),
        "palette_visible_colors": len(palette),
        "tile_dictionary_entries": len(dictionary),
        "tile_index_width": index_width,
        "tile_dictionary_raw_bytes": len(dictionary_raw),
        "tile_dictionary_lz77_bytes": len(dictionary_lz),
        "home_map_bytes": len(home_map),
        "raw_command_bytes": raw_commands_total,
        "lz77_command_bytes": lz_commands_total,
        "frame_count": frame_count,
        "frame_descriptor_bytes": frame_desc,
        "action_descriptor_bytes": action_desc,
        "profile_fixed_bytes": PROFILE_FIXED_BYTES,
        "palette_bytes": PALETTE_BYTES,
        "shadow_metadata_bytes": shadow_meta,
        "max_raw_action_command_bytes": max_raw_action,
        "max_lz77_action_command_bytes": max_lz_action,
        "max_changed_tiles_in_frame": max_changed_tiles,
        "total_bytes_compressed_dictionary": total_compressed_dict,
        "total_bytes_raw_dictionary": total_raw_dict,
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
        "dictionary_entries": 0,
        "dictionary_raw_bytes": 0,
        "dictionary_lz77_bytes": 0,
        "home_map_bytes": 0,
        "raw_command_bytes": 0,
        "lz77_command_bytes": 0,
        "descriptor_bytes": 0,
        "profile_bytes": 0,
        "palette_bytes": 0,
        "shadow_metadata_bytes": SHARED_SHADOW_MASK_BYTES,
        "packed_total_bytes_compressed_dictionary": SHARED_SHADOW_MASK_BYTES,
        "packed_total_bytes_raw_dictionary": SHARED_SHADOW_MASK_BYTES,
        "max_dictionary_raw_bytes_per_battler": 0,
        "max_raw_action_command_bytes_per_battler": 0,
        "max_changed_tiles_in_frame": 0,
        "u8_dictionary_side_packs": 0,
        "u16_dictionary_side_packs": 0,
    }
    species_records = []

    for dex, dex_name in enumerate(dex_names, 1):
        audit_rec = by_dex[dex]
        if audit_rec["eligibility"] != "LOSSLESS_SINGLE_OBJ_BOTH_SIDES":
            continue
        species_dir = sprite_root / f"{dex:04d}"
        actions = g4a.parse_anim_data_compat(species_dir / "AnimData.xml")
        rec = {"national_dex": dex, "national_dex_constant": f"NATIONAL_DEX_{dex_name}", "sides": {}}
        for side, direction in VIEWS:
            anchor = tuple(int(v) for v in audit_rec["views"][side]["common_anchor"]["selected"])
            rendered, colors = g4e.render_sparse_side(species_dir, actions, direction, anchor)
            storage = side_storage(rendered, colors)
            storage["direction"] = direction
            storage["anchor"] = list(anchor)
            rec["sides"][side] = storage

            totals["species_side_packs"] += 1
            totals["frames"] += storage["frame_count"]
            totals["dictionary_entries"] += storage["tile_dictionary_entries"]
            totals["dictionary_raw_bytes"] += storage["tile_dictionary_raw_bytes"]
            totals["dictionary_lz77_bytes"] += storage["tile_dictionary_lz77_bytes"]
            totals["home_map_bytes"] += storage["home_map_bytes"]
            totals["raw_command_bytes"] += storage["raw_command_bytes"]
            totals["lz77_command_bytes"] += storage["lz77_command_bytes"]
            totals["descriptor_bytes"] += storage["frame_descriptor_bytes"] + storage["action_descriptor_bytes"]
            totals["profile_bytes"] += storage["profile_fixed_bytes"]
            totals["palette_bytes"] += storage["palette_bytes"]
            totals["shadow_metadata_bytes"] += storage["shadow_metadata_bytes"]
            totals["packed_total_bytes_compressed_dictionary"] += storage["total_bytes_compressed_dictionary"]
            totals["packed_total_bytes_raw_dictionary"] += storage["total_bytes_raw_dictionary"]
            totals["max_dictionary_raw_bytes_per_battler"] = max(
                totals["max_dictionary_raw_bytes_per_battler"], storage["tile_dictionary_raw_bytes"]
            )
            totals["max_raw_action_command_bytes_per_battler"] = max(
                totals["max_raw_action_command_bytes_per_battler"], storage["max_raw_action_command_bytes"]
            )
            totals["max_changed_tiles_in_frame"] = max(
                totals["max_changed_tiles_in_frame"], storage["max_changed_tiles_in_frame"]
            )
            totals["u8_dictionary_side_packs" if storage["tile_index_width"] == 1 else "u16_dictionary_side_packs"] += 1
        totals["eligible_species"] += 1
        species_records.append(rec)

    free = g4e.trailing_ff_free(args.rom.resolve())
    max_per_battler = (
        g4e.FRAME_BYTES
        + totals["max_dictionary_raw_bytes_per_battler"]
        + totals["max_raw_action_command_bytes_per_battler"]
    )
    worst_four = 4 * max_per_battler
    result = {
        "phase": "G4E3_TILE_DICTIONARY_DELTA_CODEC_AUDIT",
        "parent": "CORRECTED_G4D_LOSSLESS_SINGLE_OBJ",
        "activation_change": "NONE_AUDIT_ONLY",
        "body_storage": "PER_SPECIES_SIDE_LZ77_TILE_DICTIONARY_PLUS_HOME_TILEMAP_PLUS_PER_ACTION_LZ77_CHANGED_TILE_COMMANDS",
        "reconstruction": "BYTE_EXACT_2048_BYTE_4BPP_FRAME_VERIFIED_FOR_EVERY_FRAME",
        "visible_pixel_policy": "G4D_100_PERCENT_OPAQUE_PIXEL_CONSERVATION",
        "fallback": "MISSING_INVALID_OR_MULTI_OBJ_REMAINS_NATIVE_SOULGOLD",
        "rom": {"bytes": args.rom.stat().st_size, "trailing_ff_free_bytes": free},
        "totals": totals,
        "fits_current_trailing_free_space": totals["packed_total_bytes_compressed_dictionary"] <= free,
        "additional_bytes_required_beyond_current_free": max(
            0, totals["packed_total_bytes_compressed_dictionary"] - free
        ),
        "ewram": {
            "body_scratch_bytes_per_battler": g4e.FRAME_BYTES,
            "max_dictionary_raw_bytes_per_battler": totals["max_dictionary_raw_bytes_per_battler"],
            "max_action_command_bytes_per_battler": totals["max_raw_action_command_bytes_per_battler"],
            "worst_case_four_battler_bytes": worst_four,
        },
        "species": species_records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("G4E3 tile dictionary delta codec audit PASS")
    print(json.dumps({
        "eligible_species": totals["eligible_species"],
        "frames": totals["frames"],
        "dictionary_lz77_bytes": totals["dictionary_lz77_bytes"],
        "lz77_command_bytes": totals["lz77_command_bytes"],
        "packed_total_bytes": totals["packed_total_bytes_compressed_dictionary"],
        "rom_free_bytes": free,
        "additional_required": result["additional_bytes_required_beyond_current_free"],
        "u8_dictionary_side_packs": totals["u8_dictionary_side_packs"],
        "u16_dictionary_side_packs": totals["u16_dictionary_side_packs"],
        "worst_four_battler_ewram": worst_four,
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
