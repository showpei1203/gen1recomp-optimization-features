#!/usr/bin/env python3
"""Audit a ROM-oriented PMD body pack for full-roster SoulGold scaling.

G4D proved that 901 National Dex base species can preserve all visible pixels of
Idle/Walk/Hurt/Attack/Shoot in one 64x64 battler OBJ on both battle sides. The
remaining blocker is ROM space: storing a full 2048-byte 4bpp body frame for
thousands of animation frames cannot fit the 32 MiB GBA cartridge address space.

G4E measures a runtime-feasible delta architecture instead of hand-waving about
compression ratios:

* one 64x64 HOME keyframe per species+side, compressed with GBA BIOS LZ77;
* every action begins from HOME and subsequent frames are byte-run patches from
  the preceding frame, preserving every 4bpp pixel exactly;
* one shared palette per species+side, matching the existing portable converter
  model (15 visible colors + transparent index 0);
* shadow art is not duplicated per frame: PMDCollab Shadow.png remains the
  authority for center/size semantics while frame storage is metadata-only;
* registry/profile metadata is included in the estimate.

This is an audit only. It does not activate new species. Missing/invalid PMD
metadata remains native SoulGold, and G4D multi-OBJ species remain deferred.
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict, deque
from pathlib import Path

from PIL import Image

import audit_soulgold_g4a_pmd_roster_coverage as g4a
import audit_soulgold_g4d_lossless_single_obj as g4d
import pmd_gba_converter as pmd

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
CORE_ACTIONS = ("Idle", "Walk", "Hurt", "Attack", "Shoot")
VIEWS = (("player", "UpRight"), ("opponent", "DownLeft"))
CANVAS = 64
FRAME_BYTES = 2048

FRAME_DESC_BYTES = 8
ACTION_DESC_BYTES = 12
PROFILE_FIXED_BYTES = 80
SHADOW_FRAME_META_BYTES = 2
SHADOW_SPECIES_BYTES = 4
SHARED_SHADOW_MASK_BYTES = 3 * 0x80
PALETTE_BYTES = 32


def place_visible(frame: Image.Image, center: tuple[int, int], anchor: tuple[int, int]) -> Image.Image:
    dx = anchor[0] - center[0]
    dy = anchor[1] - center[1]
    out = Image.new("RGBA", (CANVAS, CANVAS), (0, 0, 0, 0))
    src = frame.load()
    dst = out.load()
    copied = 0
    source = 0
    for y in range(frame.height):
        for x in range(frame.width):
            px = src[x, y]
            if px[3] == 0:
                continue
            source += 1
            tx, ty = x + dx, y + dy
            if not (0 <= tx < CANVAS and 0 <= ty < CANVAS):
                raise ValueError(f"opaque pixel escaped G4D anchor: src=({x},{y}) dst=({tx},{ty})")
            dst[tx, ty] = px
            copied += 1
    if copied != source:
        raise ValueError(f"visible pixel conservation mismatch {copied}/{source}")
    return out


def pack_4bpp_tiles(indexed: Image.Image) -> bytes:
    if indexed.size != (CANVAS, CANVAS):
        raise ValueError(indexed.size)
    px = indexed.load()
    out = bytearray()
    for tile_y in range(0, CANVAS, 8):
        for tile_x in range(0, CANVAS, 8):
            for y in range(8):
                for x in range(0, 8, 2):
                    lo = int(px[tile_x + x, tile_y + y])
                    hi = int(px[tile_x + x + 1, tile_y + y])
                    if not (0 <= lo < 16 and 0 <= hi < 16):
                        raise ValueError("indexed pixel outside 4bpp")
                    out.append(lo | (hi << 4))
    if len(out) != FRAME_BYTES:
        raise ValueError(len(out))
    return bytes(out)


def patch_runs(previous: bytes, current: bytes) -> bytes:
    if len(previous) != FRAME_BYTES or len(current) != FRAME_BYTES:
        raise ValueError("frame byte size mismatch")
    out = bytearray()
    i = 0
    while i < FRAME_BYTES:
        if previous[i] == current[i]:
            i += 1
            continue
        start = i
        chunk = bytearray()
        while i < FRAME_BYTES and previous[i] != current[i] and len(chunk) < 255:
            chunk.append(current[i])
            i += 1
        out.extend((start & 0xFF, (start >> 8) & 0xFF, len(chunk)))
        out.extend(chunk)
    return bytes(out)


def apply_patch(previous: bytes, patch: bytes) -> bytes:
    out = bytearray(previous)
    i = 0
    while i < len(patch):
        if i + 3 > len(patch):
            raise ValueError("truncated patch header")
        off = patch[i] | (patch[i + 1] << 8)
        length = patch[i + 2]
        i += 3
        if length == 0 or i + length > len(patch) or off + length > FRAME_BYTES:
            raise ValueError("invalid patch run")
        out[off:off + length] = patch[i:i + length]
        i += length
    return bytes(out)


def gba_lz77(data: bytes) -> bytes:
    """Produce a valid GBA BIOS LZ77 (0x10) stream using greedy 3-byte buckets."""
    n = len(data)
    out = bytearray((0x10, n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF))
    buckets: dict[bytes, deque[int]] = defaultdict(deque)

    def add_pos(pos: int) -> None:
        if pos + 2 >= n:
            return
        key = data[pos:pos + 3]
        q = buckets[key]
        q.append(pos)
        while q and pos - q[0] > 4096:
            q.popleft()
        while len(q) > 96:
            q.popleft()

    i = 0
    while i < n:
        flag_index = len(out)
        out.append(0)
        flags = 0
        for token in range(8):
            if i >= n:
                break
            best_len = 0
            best_disp = 0
            if i + 2 < n:
                candidates = buckets.get(data[i:i + 3])
                if candidates:
                    for pos in reversed(candidates):
                        disp = i - pos
                        if disp <= 0 or disp > 4096:
                            continue
                        length = 3
                        max_len = min(18, n - i)
                        while length < max_len and data[pos + length] == data[i + length]:
                            length += 1
                        if length > best_len:
                            best_len, best_disp = length, disp
                            if best_len == max_len:
                                break
            if best_len >= 3:
                flags |= 1 << (7 - token)
                d = best_disp - 1
                out.append(((best_len - 3) << 4) | ((d >> 8) & 0xF))
                out.append(d & 0xFF)
                old = i
                i += best_len
                for pos in range(old, i):
                    add_pos(pos)
            else:
                out.append(data[i])
                add_pos(i)
                i += 1
        out[flag_index] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def render_side(species_dir: Path, actions: dict, direction: str, anchor: tuple[int, int]) -> tuple[dict, list[Image.Image]]:
    rendered: dict[str, dict] = {}
    all_canvases: list[Image.Image] = []
    for action_name in CORE_ACTIONS:
        action = g4a.resolve_action_compat(action_name, actions)
        anim = Image.open(species_dir / f"{action.source_action}-Anim.png").convert("RGBA")
        offsets = Image.open(species_dir / f"{action.source_action}-Offsets.png").convert("RGBA")
        if anim.size != offsets.size:
            raise ValueError(f"{action_name} anim/offset mismatch")
        frames = []
        for i, duration in enumerate(action.durations):
            body = g4d.crop_frame(anim, action, direction, i)
            off = g4d.crop_frame(offsets, action, direction, i)
            center = pmd.body_center_from_offsets(off)
            canvas = place_visible(body, center, anchor)
            frames.append({"duration": int(duration), "canvas": canvas})
            all_canvases.append(canvas)
        rendered[action_name] = {
            "frames": frames,
            "rush": action.rush_frame,
            "hit": action.hit_frame,
            "return": action.return_frame,
        }
    return rendered, all_canvases


def side_storage(rendered: dict, canvases: list[Image.Image]) -> dict:
    palette = pmd.quantized_palette(canvases)
    packed_by_action: dict[str, list[bytes]] = {}
    for action_name in CORE_ACTIONS:
        packed_by_action[action_name] = [
            pack_4bpp_tiles(pmd.to_indexed_gba(fr["canvas"], palette))
            for fr in rendered[action_name]["frames"]
        ]

    home = packed_by_action["Idle"][0]
    home_lz = gba_lz77(home)
    patch_bytes = 0
    changed_payload_bytes = 0
    frame_count = 0
    max_patch = 0
    per_action = {}
    for action_name in CORE_ACTIONS:
        previous = home
        action_patch = 0
        action_frames = packed_by_action[action_name]
        for cur in action_frames:
            patch = patch_runs(previous, cur)
            if apply_patch(previous, patch) != cur:
                raise ValueError(f"patch reconstruction failed for {action_name}")
            patch_bytes += len(patch)
            action_patch += len(patch)
            frame_count += 1
            max_patch = max(max_patch, len(patch))
            j = 0
            while j < len(patch):
                ln = patch[j + 2]
                changed_payload_bytes += ln
                j += 3 + ln
            previous = cur
        per_action[action_name] = {"frames": len(action_frames), "patch_bytes": action_patch}

    descriptors = frame_count * FRAME_DESC_BYTES + len(CORE_ACTIONS) * ACTION_DESC_BYTES
    shadow_meta = frame_count * SHADOW_FRAME_META_BYTES + SHADOW_SPECIES_BYTES
    total = len(home_lz) + patch_bytes + descriptors + shadow_meta + PALETTE_BYTES + PROFILE_FIXED_BYTES
    return {
        "palette_visible_colors": len(palette),
        "home_lz_bytes": len(home_lz),
        "patch_bytes": patch_bytes,
        "changed_payload_bytes": changed_payload_bytes,
        "frame_count": frame_count,
        "frame_descriptor_bytes": frame_count * FRAME_DESC_BYTES,
        "action_descriptor_bytes": len(CORE_ACTIONS) * ACTION_DESC_BYTES,
        "profile_fixed_bytes": PROFILE_FIXED_BYTES,
        "palette_bytes": PALETTE_BYTES,
        "shadow_metadata_bytes": shadow_meta,
        "total_bytes": total,
        "max_single_patch_bytes": max_patch,
        "per_action": per_action,
    }


def trailing_ff_free(path: Path) -> int:
    data = path.read_bytes()
    i = len(data)
    while i > 0 and data[i - 1] == 0xFF:
        i -= 1
    return len(data) - i


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
    audit = json.loads(args.g4d_audit.read_text(encoding="utf-8"))
    dex_names = g4a.parse_national_dex(soulgold / "include/constants/pokedex.h")
    records_by_dex = {int(r["national_dex"]): r for r in audit["records"]}

    totals = {
        "eligible_species": 0,
        "species_side_packs": 0,
        "frames": 0,
        "home_lz_bytes": 0,
        "patch_bytes": 0,
        "changed_payload_bytes": 0,
        "descriptor_bytes": 0,
        "profile_bytes": 0,
        "palette_bytes": 0,
        "shadow_metadata_bytes": SHARED_SHADOW_MASK_BYTES,
        "packed_total_bytes": SHARED_SHADOW_MASK_BYTES,
    }
    species_records = []

    for dex, dex_name in enumerate(dex_names, 1):
        gate = records_by_dex[dex]
        if gate["eligibility"] != "LOSSLESS_SINGLE_OBJ_BOTH_SIDES":
            continue
        species_dir = sprite_root / f"{dex:04d}"
        actions = g4a.parse_anim_data_compat(species_dir / "AnimData.xml")
        species_rec = {
            "national_dex": dex,
            "national_dex_constant": f"NATIONAL_DEX_{dex_name}",
            "sides": {},
        }
        for side, direction in VIEWS:
            common = gate["views"][side]["common_anchor"]
            anchor = tuple(int(v) for v in common["selected"])
            rendered, canvases = render_side(species_dir, actions, direction, anchor)
            storage = side_storage(rendered, canvases)
            storage["direction"] = direction
            storage["anchor"] = list(anchor)
            species_rec["sides"][side] = storage

            totals["species_side_packs"] += 1
            totals["frames"] += storage["frame_count"]
            totals["home_lz_bytes"] += storage["home_lz_bytes"]
            totals["patch_bytes"] += storage["patch_bytes"]
            totals["changed_payload_bytes"] += storage["changed_payload_bytes"]
            totals["descriptor_bytes"] += storage["frame_descriptor_bytes"] + storage["action_descriptor_bytes"]
            totals["profile_bytes"] += storage["profile_fixed_bytes"]
            totals["palette_bytes"] += storage["palette_bytes"]
            totals["shadow_metadata_bytes"] += storage["shadow_metadata_bytes"]
            totals["packed_total_bytes"] += storage["total_bytes"]
        totals["eligible_species"] += 1
        species_records.append(species_rec)

    free = trailing_ff_free(args.rom.resolve())
    result = {
        "phase": "G4E_DELTA_PACK_STORAGE_AUDIT",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "parent": "G4D_LOSSLESS_SINGLE_OBJ_BOTH_SIDES",
        "activation_change": "NONE_AUDIT_ONLY",
        "body_storage": "ONE_LZ77_HOME_KEYFRAME_PLUS_EXACT_CHANGED_BYTE_RUN_PATCHES",
        "action_start_baseline": "HOME_IDLE_FRAME_0",
        "patch_format": "u16_offset_u8_length_replacement_bytes",
        "visible_pixel_policy": "G4D_100_PERCENT_OPAQUE_PIXEL_CONSERVATION",
        "palette_model": "ONE_15_VISIBLE_COLOR_PALETTE_PER_SPECIES_SIDE_FOR_STORAGE_MEASUREMENT",
        "shadow_storage": "PMDCOLLAB_SHADOW_CENTER_SIZE_METADATA_PLUS_THREE_SHARED_MASKS",
        "multi_obj": "DEFERRED",
        "fallback": "MISSING_INVALID_OR_NON_SINGLE_OBJ_REMAINS_NATIVE_SOULGOLD",
        "accounting": {
            "frame_descriptor_bytes": FRAME_DESC_BYTES,
            "action_descriptor_bytes": ACTION_DESC_BYTES,
            "profile_fixed_bytes_per_side": PROFILE_FIXED_BYTES,
            "shadow_frame_metadata_bytes": SHADOW_FRAME_META_BYTES,
            "shared_shadow_mask_bytes": SHARED_SHADOW_MASK_BYTES,
            "palette_bytes_per_side": PALETTE_BYTES,
        },
        "rom": {"bytes": args.rom.stat().st_size, "trailing_ff_free_bytes": free},
        "totals": totals,
        "fits_current_trailing_free_space": totals["packed_total_bytes"] <= free,
        "additional_bytes_required_beyond_current_free": max(0, totals["packed_total_bytes"] - free),
        "species": species_records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("G4E delta-pack storage audit PASS")
    print(json.dumps({
        "eligible_species": totals["eligible_species"],
        "species_side_packs": totals["species_side_packs"],
        "frames": totals["frames"],
        "packed_total_bytes": totals["packed_total_bytes"],
        "rom_trailing_free_bytes": free,
        "fits_current_trailing_free_space": result["fits_current_trailing_free_space"],
        "additional_bytes_required_beyond_current_free": result["additional_bytes_required_beyond_current_free"],
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
