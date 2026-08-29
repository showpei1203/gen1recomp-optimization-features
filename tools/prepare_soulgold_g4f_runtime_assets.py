#!/usr/bin/env python3
"""Build the first runtime-consumable G4E3-style Attack packs for SoulGold.

G4F is deliberately narrow: it changes storage for the two already activated
prototype profiles only (Cyndaquil/player and Marill/opponent).  It does not
activate any new species and it does not alter battle semantics.

The source of truth is the already prepared G3R11/G4B staging tree.  Therefore
G4F cannot silently change palette mapping, body geometry, durations, markers,
or shadows while proving the runtime codec.  Each 64x64 indexed Attack PNG is
packed byte-for-byte to GBA 4bpp tile order, then encoded as:

  BIOS-LZ77 tile dictionary + raw HOME tile map +
  BIOS-LZ77 per-Attack changed-tile command stream.

The generated C descriptors replace only Attack frame gfx pointers.  Ambient,
Hurt, Sleep, Wake, dynamic shadow metadata, and native fallback remain the
parent implementation.
"""
from __future__ import annotations

import argparse
import json
import shutil
from pathlib import Path

from PIL import Image

import audit_soulgold_g4e_delta_pack as g4e

FRAME_BYTES = 0x800
TILE_BYTES = 32
TILES_PER_FRAME = 64
MAX_DICTIONARY_BYTES = 4096
MAX_COMMAND_BYTES = 512
ZERO_TILE = bytes(TILE_BYTES)

TARGETS = (
    {"species": "Cyndaquil", "slug": "cyndaquil", "variant": "player"},
    {"species": "Marill", "slug": "marill", "variant": "opponent"},
)


def symbol(text: str) -> str:
    return "".join(ch if ch.isalnum() else "_" for ch in text)


def pack_indexed_png(path: Path) -> bytes:
    image = Image.open(path)
    if image.size != (64, 64):
        raise ValueError(f"{path}: expected 64x64, got {image.size}")
    if image.mode != "P":
        raise ValueError(f"{path}: expected indexed P-mode PNG after host-palette remap, got {image.mode}")
    pixels = list(image.getdata())
    if any(int(v) < 0 or int(v) > 15 for v in pixels):
        raise ValueError(f"{path}: palette index outside 4bpp range")

    out = bytearray()
    for tile_y in range(8):
        for tile_x in range(8):
            for y in range(8):
                row = (tile_y * 8 + y) * 64 + tile_x * 8
                for x in range(0, 8, 2):
                    lo = int(pixels[row + x])
                    hi = int(pixels[row + x + 1])
                    out.append(lo | (hi << 4))
    if len(out) != FRAME_BYTES:
        raise AssertionError(len(out))
    return bytes(out)


def split_tiles(frame: bytes) -> tuple[bytes, ...]:
    if len(frame) != FRAME_BYTES:
        raise ValueError(len(frame))
    return tuple(frame[i:i + TILE_BYTES] for i in range(0, FRAME_BYTES, TILE_BYTES))


def gba_lz77_decode(data: bytes) -> bytes:
    if len(data) < 4 or data[0] != 0x10:
        raise ValueError("not GBA LZ77 0x10 data")
    size = data[1] | (data[2] << 8) | (data[3] << 16)
    src = 4
    out = bytearray()
    while len(out) < size:
        if src >= len(data):
            raise ValueError("truncated LZ77 flags")
        flags = data[src]
        src += 1
        for bit in range(7, -1, -1):
            if len(out) >= size:
                break
            if flags & (1 << bit):
                if src + 1 >= len(data):
                    raise ValueError("truncated LZ77 copy")
                a, b = data[src], data[src + 1]
                src += 2
                length = (a >> 4) + 3
                disp = ((a & 0x0F) << 8) | b
                back = disp + 1
                if back > len(out):
                    raise ValueError("invalid LZ77 backreference")
                for _ in range(length):
                    out.append(out[-back])
                    if len(out) >= size:
                        break
            else:
                if src >= len(data):
                    raise ValueError("truncated LZ77 literal")
                out.append(data[src])
                src += 1
    return bytes(out)


def build_pack(home: bytes, frames: list[bytes]) -> dict:
    all_tiles = set(t for t in split_tiles(home) if t != ZERO_TILE)
    for frame in frames:
        all_tiles.update(t for t in split_tiles(frame) if t != ZERO_TILE)
    dictionary = sorted(all_tiles)
    if len(dictionary) > 255:
        raise ValueError(f"G4F pilot requires u8 tile dictionary, got {len(dictionary)} entries")
    tile_to_index = {tile: i + 1 for i, tile in enumerate(dictionary)}
    dictionary_raw = b"".join(dictionary)
    if len(dictionary_raw) > MAX_DICTIONARY_BYTES:
        raise ValueError(f"dictionary {len(dictionary_raw)} > G4F pilot max {MAX_DICTIONARY_BYTES}")

    home_tiles = split_tiles(home)
    home_map = bytes(0 if t == ZERO_TILE else tile_to_index[t] for t in home_tiles)
    stream = bytearray()
    offsets: list[int] = []
    previous = home_tiles
    max_changed = 0
    for frame in frames:
        current = split_tiles(frame)
        changed = [(pos, tile) for pos, (old, tile) in enumerate(zip(previous, current)) if old != tile]
        offsets.append(len(stream))
        stream.append(len(changed))
        max_changed = max(max_changed, len(changed))
        for pos, tile in changed:
            stream.append(pos)
            stream.append(0 if tile == ZERO_TILE else tile_to_index[tile])
        previous = current
    commands_raw = bytes(stream)
    if len(commands_raw) > MAX_COMMAND_BYTES:
        raise ValueError(f"commands {len(commands_raw)} > G4F pilot max {MAX_COMMAND_BYTES}")

    dictionary_lz = g4e.gba_lz77(dictionary_raw)
    commands_lz = g4e.gba_lz77(commands_raw)
    if gba_lz77_decode(dictionary_lz) != dictionary_raw:
        raise ValueError("dictionary LZ77 round-trip failed")
    if gba_lz77_decode(commands_lz) != commands_raw:
        raise ValueError("command LZ77 round-trip failed")

    # Full independent decoder proof from the exact emitted blobs.
    decoded_dict_raw = gba_lz77_decode(dictionary_lz)
    decoded_dictionary = [decoded_dict_raw[i:i + TILE_BYTES] for i in range(0, len(decoded_dict_raw), TILE_BYTES)]
    decoded_commands = gba_lz77_decode(commands_lz)
    scratch = [ZERO_TILE if idx == 0 else decoded_dictionary[idx - 1] for idx in home_map]
    reconstructed: list[bytes] = []
    for frame_index, offset in enumerate(offsets):
        cursor = offset
        count = decoded_commands[cursor]
        cursor += 1
        for _ in range(count):
            tile_pos = decoded_commands[cursor]
            tile_idx = decoded_commands[cursor + 1]
            cursor += 2
            scratch[tile_pos] = ZERO_TILE if tile_idx == 0 else decoded_dictionary[tile_idx - 1]
        rebuilt = b"".join(scratch)
        if rebuilt != frames[frame_index]:
            raise ValueError(f"frame {frame_index} byte reconstruction mismatch")
        reconstructed.append(rebuilt)

    legacy_frame_lz = [g4e.gba_lz77(frame) for frame in frames]
    return {
        "dictionary_raw": dictionary_raw,
        "dictionary_lz": dictionary_lz,
        "home_map": home_map,
        "commands_raw": commands_raw,
        "commands_lz": commands_lz,
        "offsets": offsets,
        "dictionary_entries": len(dictionary),
        "max_changed_tiles": max_changed,
        "legacy_per_frame_lz_bytes": sum(len(x) for x in legacy_frame_lz),
        "packed_bytes": len(dictionary_lz) + len(home_map) + len(commands_lz) + 2 * len(offsets),
        "byte_exact": all(a == b for a, b in zip(reconstructed, frames)),
    }


def patch_attack_source(path: Path, species: str, variant: str, frame_count: int) -> str:
    text = path.read_text(encoding="utf-8")
    species_sym = symbol(species)
    variant_sym = symbol(variant.title())
    prefix = f"Pmd{species_sym}{variant_sym}Attack"

    lines = text.splitlines()
    kept = []
    removed = 0
    for line in lines:
        if line.startswith(f"const u32 g{prefix}Frame") and ".4bpp.lz" in line:
            removed += 1
            continue
        kept.append(line)
    if removed != frame_count:
        raise ValueError(f"{path}: expected {frame_count} legacy Attack frame blobs, removed {removed}")
    text = "\n".join(kept) + "\n"
    include = '#include "pmd_g4f_codec.h"\n'
    anchor = '#include "pmd_gba_runtime.h"\n'
    if include not in text:
        if anchor not in text:
            raise ValueError(f"{path}: runtime include anchor missing")
        text = text.replace(anchor, anchor + include, 1)
    extern = f"extern const struct PmdG4fPackedFrame g{prefix}PackedFrames[{frame_count}];\n"
    if extern not in text:
        text = text.replace(include, include + extern, 1)

    for i in range(frame_count):
        old = f"{{ .gfx = g{prefix}Frame{i:02d}, .duration = "
        if old not in text:
            raise ValueError(f"{path}: frame {i} descriptor anchor missing")
        text = text.replace(old, f"{{ .gfx = NULL, .packed = &g{prefix}PackedFrames[{i}], .duration = ", 1)
    if ".4bpp.lz" in text:
        raise ValueError(f"{path}: legacy Attack INCBIN survived G4F patch")
    path.write_text(text, encoding="utf-8")
    return prefix


def emit_pack_c(path: Path, target: dict, prefix: str, pack: dict, asset_root: str, frame_count: int) -> None:
    offsets = ", ".join(str(v) for v in pack["offsets"])
    lines = [
        "/* Auto-generated G4F runtime tile-delta Attack pack. */",
        '#include "global.h"',
        '#include "pmd_g4f_codec.h"',
        "",
        f'const u32 g{prefix}DictionaryLz[] = INCBIN_U32("{asset_root}/g4f/attack_dictionary.bin.lz");',
        f'const u8 g{prefix}HomeMap[] = INCBIN_U8("{asset_root}/g4f/attack_home_map.bin");',
        f'const u32 g{prefix}CommandsLz[] = INCBIN_U32("{asset_root}/g4f/attack_commands.bin.lz");',
        f"static const u16 s{prefix}FrameOffsets[{frame_count}] = {{ {offsets} }};",
        "",
        f"static const struct PmdG4fPackedAction s{prefix}PackedAction =",
        "{",
        f"    .dictionaryLz = g{prefix}DictionaryLz,",
        f"    .dictionaryBytes = {len(pack['dictionary_raw'])},",
        f"    .homeMap = g{prefix}HomeMap,",
        f"    .commandsLz = g{prefix}CommandsLz,",
        f"    .commandBytes = {len(pack['commands_raw'])},",
        f"    .frameOffsets = s{prefix}FrameOffsets,",
        "    .indexWidth = 1,",
        f"    .frameCount = {frame_count},",
        "};",
        "",
        f"const struct PmdG4fPackedFrame g{prefix}PackedFrames[{frame_count}] =",
        "{",
    ]
    for i in range(frame_count):
        lines.append(f"    {{ .action = &s{prefix}PackedAction, .frameIndex = {i} }},")
    lines += ["};", ""]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--parent-staging", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    parent = args.parent_staging.resolve()
    out = args.output.resolve()
    staging = out / "staging"
    if out.exists():
        shutil.rmtree(out)
    shutil.copytree(parent, staging)

    summary = {
        "phase": "G4F_RUNTIME_TILE_DELTA_ATTACK_PILOT",
        "parent": "G4B_G3R11",
        "activation_change": "NONE_TWO_EXISTING_PROFILES_ONLY",
        "codec": "LZ77_TILE_DICTIONARY_PLUS_HOME_MAP_PLUS_LZ77_CHANGED_TILE_COMMANDS",
        "decode_timing": "PREPARE_BEFORE_ANIMATE_SPRITES_NOT_OAM_CRITICAL_TICK",
        "native_battle_semantics": "UNCHANGED",
        "known_ambient_1px_defect": "DEFERRED_ROOT_CAUSE_UNRESOLVED",
        "targets": {},
    }

    for target in TARGETS:
        root = staging / "graphics" / "pmd" / target["slug"] / target["variant"]
        home_path = root / "idle" / "frame_00.png"
        attack_paths = sorted((root / "attack").glob("frame_*.png"))
        if not home_path.is_file() or not attack_paths:
            raise SystemExit(f"missing parent PNGs for {target}")
        home = pack_indexed_png(home_path)
        frames = [pack_indexed_png(path) for path in attack_paths]
        pack = build_pack(home, frames)
        if not pack["byte_exact"]:
            raise SystemExit(f"{target}: codec byte-exact proof failed")

        g4f_dir = root / "g4f"
        g4f_dir.mkdir(parents=True, exist_ok=True)
        (g4f_dir / "attack_dictionary.bin.lz").write_bytes(pack["dictionary_lz"])
        (g4f_dir / "attack_home_map.bin").write_bytes(pack["home_map"])
        (g4f_dir / "attack_commands.bin.lz").write_bytes(pack["commands_lz"])

        attack_c = staging / "src" / f"pmd_{target['slug']}_{target['variant']}_attack.c"
        prefix = patch_attack_source(attack_c, target["species"], target["variant"], len(frames))
        asset_root = f"graphics/pmd/{target['slug']}/{target['variant']}"
        pack_c = staging / "src" / f"pmd_{target['slug']}_{target['variant']}_g4f_pack.c"
        emit_pack_c(pack_c, target, prefix, pack, asset_root, len(frames))

        key = f"{target['species']}_{target['variant']}"
        summary["targets"][key] = {
            "species": target["species"],
            "variant": target["variant"],
            "attack_frames": len(frames),
            "raw_frame_bytes": len(frames) * FRAME_BYTES,
            "dictionary_entries": pack["dictionary_entries"],
            "dictionary_raw_bytes": len(pack["dictionary_raw"]),
            "dictionary_lz77_bytes": len(pack["dictionary_lz"]),
            "command_raw_bytes": len(pack["commands_raw"]),
            "command_lz77_bytes": len(pack["commands_lz"]),
            "home_map_bytes": len(pack["home_map"]),
            "frame_offset_bytes": 2 * len(pack["offsets"]),
            "max_changed_tiles": pack["max_changed_tiles"],
            "legacy_per_frame_lz77_bytes": pack["legacy_per_frame_lz_bytes"],
            "g4f_packed_bytes": pack["packed_bytes"],
            "byte_exact_reconstruction": True,
            "legacy_attack_blob_removed": True,
        }
        if pack["packed_bytes"] >= pack["legacy_per_frame_lz_bytes"]:
            raise SystemExit(f"{key}: G4F pilot does not beat per-frame LZ77 storage")

    out.mkdir(parents=True, exist_ok=True)
    (out / "G4F_ASSET_SUMMARY.json").write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, indent=2))
    print("G4F runtime Attack asset preparation PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
