#!/usr/bin/env python3
"""Audit a ROM-oriented PMD delta pack for full-roster SoulGold scaling.

G4D proved that 901 National Dex base species can conserve every visible pixel
of Idle/Walk/Hurt/Attack/Shoot inside one 64x64 battler OBJ on both battle
views. G4E measures a storage format that the GBA runtime can actually decode:
one LZ77 HOME keyframe per species+side, then exact changed-byte patches for
all action frames. PMDCollab Shadow.png remains the center/size authority while
shadow storage becomes metadata plus three shared size masks.

This gate is audit-only. It activates no new species and preserves SoulGold's
native battler fallback for missing/invalid/multi-OBJ PMD cases.
"""
from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict, deque
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

RGB = tuple[int, int, int]
SparsePixel = tuple[int, int, RGB]


def sparse_visible(frame: Image.Image, center: tuple[int, int], anchor: tuple[int, int]) -> list[SparsePixel]:
    dx = anchor[0] - center[0]
    dy = anchor[1] - center[1]
    src = frame.load()
    out: list[SparsePixel] = []
    for y in range(frame.height):
        for x in range(frame.width):
            r, g, b, a = src[x, y]
            if not a:
                continue
            tx, ty = x + dx, y + dy
            if not (0 <= tx < CANVAS and 0 <= ty < CANVAS):
                raise ValueError(f"opaque pixel escaped G4D anchor: src=({x},{y}) dst=({tx},{ty})")
            out.append((tx, ty, (r, g, b)))
    if not out:
        raise ValueError("frame has no visible pixels")
    return out


def build_palette(counts: Counter[RGB]) -> list[RGB]:
    colors = sorted(counts)
    if len(colors) <= 15:
        return colors
    weighted: list[RGB] = []
    scale = max(1, sum(counts.values()) // 65536)
    for color, count in counts.items():
        weighted.extend([color] * max(1, count // scale))
    side = max(1, int(math.ceil(math.sqrt(len(weighted)))))
    atlas = Image.new("RGB", (side, side), (0, 0, 0))
    for i, color in enumerate(weighted):
        atlas.putpixel((i % side, i // side), color)
    q = atlas.quantize(colors=15, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE)
    raw = q.getpalette()[:45]
    palette: list[RGB] = []
    for i in range(0, len(raw), 3):
        c = (raw[i], raw[i + 1], raw[i + 2])
        if c not in palette:
            palette.append(c)
    return palette[:15]


def nearest(rgb: RGB, palette: list[RGB]) -> int:
    best = 0
    best_d = None
    for i, p in enumerate(palette):
        d = (rgb[0] - p[0]) ** 2 + (rgb[1] - p[1]) ** 2 + (rgb[2] - p[2]) ** 2
        if best_d is None or d < best_d:
            best, best_d = i, d
    return best + 1


def pack_sparse_4bpp(pixels: list[SparsePixel], color_to_index: dict[RGB, int]) -> bytes:
    out = bytearray(FRAME_BYTES)
    for x, y, color in pixels:
        idx = color_to_index[color]
        tile = (y // 8) * 8 + (x // 8)
        off = tile * 32 + (y % 8) * 4 + (x % 8) // 2
        if x & 1:
            out[off] = (out[off] & 0x0F) | (idx << 4)
        else:
            out[off] = (out[off] & 0xF0) | idx
    return bytes(out)


def patch_runs(previous: bytes, current: bytes) -> bytes:
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
            raise ValueError("truncated patch")
        off = patch[i] | (patch[i + 1] << 8)
        length = patch[i + 2]
        i += 3
        if length == 0 or i + length > len(patch) or off + length > FRAME_BYTES:
            raise ValueError("invalid patch")
        out[off:off + length] = patch[i:i + length]
        i += length
    return bytes(out)


def gba_lz77(data: bytes) -> bytes:
    n = len(data)
    out = bytearray((0x10, n & 0xFF, (n >> 8) & 0xFF, (n >> 16) & 0xFF))
    buckets: dict[bytes, deque[int]] = defaultdict(deque)

    def add_pos(pos: int) -> None:
        if pos + 2 >= n:
            return
        q = buckets[data[pos:pos + 3]]
        q.append(pos)
        while q and pos - q[0] > 4096:
            q.popleft()
        while len(q) > 96:
            q.popleft()

    i = 0
    while i < n:
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for token in range(8):
            if i >= n:
                break
            best_len = best_disp = 0
            if i + 2 < n:
                q = buckets.get(data[i:i + 3])
                if q:
                    for pos in reversed(q):
                        disp = i - pos
                        if not (1 <= disp <= 4096):
                            continue
                        length = 3
                        limit = min(18, n - i)
                        while length < limit and data[pos + length] == data[i + length]:
                            length += 1
                        if length > best_len:
                            best_len, best_disp = length, disp
                            if length == limit:
                                break
            if best_len >= 3:
                flags |= 1 << (7 - token)
                d = best_disp - 1
                out.extend((((best_len - 3) << 4) | ((d >> 8) & 0xF), d & 0xFF))
                old = i
                i += best_len
                for pos in range(old, i):
                    add_pos(pos)
            else:
                out.append(data[i])
                add_pos(i)
                i += 1
        out[flag_pos] = flags
    while len(out) % 4:
        out.append(0)
    return bytes(out)


def render_sparse_side(species_dir: Path, actions: dict, direction: str, anchor: tuple[int, int]):
    rendered: dict[str, dict] = {}
    colors: Counter[RGB] = Counter()
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
            pixels = sparse_visible(body, center, anchor)
            colors.update(color for _, _, color in pixels)
            frames.append({"duration": int(duration), "pixels": pixels})
        rendered[action_name] = {
            "frames": frames,
            "rush": action.rush_frame,
            "hit": action.hit_frame,
            "return": action.return_frame,
        }
    return rendered, colors


def side_storage(rendered: dict, colors: Counter[RGB]) -> dict:
    palette = build_palette(colors)
    color_to_index = {c: (palette.index(c) + 1 if c in palette else nearest(c, palette)) for c in colors}
    packed: dict[str, list[bytes]] = {}
    for action_name in CORE_ACTIONS:
        packed[action_name] = [pack_sparse_4bpp(fr["pixels"], color_to_index) for fr in rendered[action_name]["frames"]]

    home = packed["Idle"][0]
    home_lz = gba_lz77(home)
    patch_bytes = changed_payload = frames = max_patch = 0
    per_action = {}
    for action_name in CORE_ACTIONS:
        previous = home
        action_bytes = 0
        for current in packed[action_name]:
            patch = patch_runs(previous, current)
            if apply_patch(previous, patch) != current:
                raise ValueError(f"patch reconstruction failed: {action_name}")
            patch_bytes += len(patch)
            action_bytes += len(patch)
            frames += 1
            max_patch = max(max_patch, len(patch))
            j = 0
            while j < len(patch):
                ln = patch[j + 2]
                changed_payload += ln
                j += 3 + ln
            previous = current
        per_action[action_name] = {"frames": len(packed[action_name]), "patch_bytes": action_bytes}

    frame_desc = frames * FRAME_DESC_BYTES
    action_desc = len(CORE_ACTIONS) * ACTION_DESC_BYTES
    shadow_meta = frames * SHADOW_FRAME_META_BYTES + SHADOW_SPECIES_BYTES
    total = len(home_lz) + patch_bytes + frame_desc + action_desc + PROFILE_FIXED_BYTES + PALETTE_BYTES + shadow_meta
    return {
        "palette_source_colors": len(colors),
        "palette_visible_colors": len(palette),
        "home_lz_bytes": len(home_lz),
        "patch_bytes": patch_bytes,
        "changed_payload_bytes": changed_payload,
        "frame_count": frames,
        "frame_descriptor_bytes": frame_desc,
        "action_descriptor_bytes": action_desc,
        "profile_fixed_bytes": PROFILE_FIXED_BYTES,
        "palette_bytes": PALETTE_BYTES,
        "shadow_metadata_bytes": shadow_meta,
        "max_single_patch_bytes": max_patch,
        "total_bytes": total,
        "per_action": per_action,
    }


def trailing_ff_free(path: Path) -> int:
    data = path.read_bytes()
    i = len(data)
    while i and data[i - 1] == 0xFF:
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
    gate = json.loads(args.g4d_audit.read_text(encoding="utf-8"))
    dex_names = g4a.parse_national_dex(soulgold / "include/constants/pokedex.h")
    by_dex = {int(r["national_dex"]): r for r in gate["records"]}

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
        audit_rec = by_dex[dex]
        if audit_rec["eligibility"] != "LOSSLESS_SINGLE_OBJ_BOTH_SIDES":
            continue
        species_dir = sprite_root / f"{dex:04d}"
        actions = g4a.parse_anim_data_compat(species_dir / "AnimData.xml")
        rec = {"national_dex": dex, "national_dex_constant": f"NATIONAL_DEX_{dex_name}", "sides": {}}
        for side, direction in VIEWS:
            anchor = tuple(int(v) for v in audit_rec["views"][side]["common_anchor"]["selected"])
            rendered, colors = render_sparse_side(species_dir, actions, direction, anchor)
            storage = side_storage(rendered, colors)
            storage["direction"] = direction
            storage["anchor"] = list(anchor)
            rec["sides"][side] = storage
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
        species_records.append(rec)

    free = trailing_ff_free(args.rom.resolve())
    result = {
        "phase": "G4E_DELTA_PACK_STORAGE_AUDIT",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "parent": "G4D_LOSSLESS_SINGLE_OBJ_BOTH_SIDES",
        "activation_change": "NONE_AUDIT_ONLY",
        "body_storage": "ONE_GBA_LZ77_HOME_KEYFRAME_PLUS_EXACT_CHANGED_BYTE_RUN_PATCHES",
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
