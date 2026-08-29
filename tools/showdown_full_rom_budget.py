#!/usr/bin/env python3
"""Measure real 32 MiB ROM budget for all safe Showdown normal front/back battlers.

The audit reads official GIFs directly. It uses the same 64x64 bottom-center,
host-palette conversion helpers as showdown_sprites_ingest.py, then stores:
- Showdown frame 0 as the replacement static battler body;
- 2/3/4/6/8 time-spaced animation samples as GBA-LZ compressed XOR deltas;
- compact timing/pointer descriptors.

The GBA-LZ writer emits standard BIOS-compatible 0x10 streams. Sizes are aligned
to 4 bytes to model normal ROM linking conservatively.
"""
from __future__ import annotations

import argparse
import bisect
import importlib.util
import io
import json
import re
import subprocess
import sys
import zipfile
from collections import defaultdict
from pathlib import Path, PurePosixPath

from PIL import Image

ROM_LIMIT = 32 * 1024 * 1024
FRAME_BYTES = 2048
SAMPLE_COUNTS = (2, 3, 4, 6, 8)
RUNTIME_RESERVE_BYTES = 64 * 1024


def align4(n: int) -> int:
    return (n + 3) & ~3


def load_converter(path: Path):
    spec = importlib.util.spec_from_file_location("showdown_sprites_ingest_budget", path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot load converter {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    return mod


def gba_lz(data: bytes) -> bytes:
    """Greedy BIOS-compatible GBA LZ77 (type 0x10)."""
    if len(data) >= (1 << 24):
        raise ValueError("GBA LZ input too large")
    positions: dict[bytes, list[int]] = defaultdict(list)
    for i in range(max(0, len(data) - 2)):
        positions[data[i:i + 3]].append(i)

    out = bytearray((0x10, len(data) & 0xFF, (len(data) >> 8) & 0xFF, (len(data) >> 16) & 0xFF))
    pos = 0
    while pos < len(data):
        flag_pos = len(out)
        out.append(0)
        flags = 0
        for bit in range(8):
            if pos >= len(data):
                break
            best_len = 0
            best_disp = 0
            if pos + 2 < len(data):
                key = data[pos:pos + 3]
                cand = positions.get(key, [])
                stop = bisect.bisect_left(cand, pos)
                for ci in range(stop - 1, -1, -1):
                    src = cand[ci]
                    disp = pos - src
                    if disp > 4096:
                        break
                    max_len = min(18, len(data) - pos)
                    length = 3
                    while length < max_len and data[src + length] == data[pos + length]:
                        length += 1
                    if length > best_len:
                        best_len = length
                        best_disp = disp
                        if best_len == 18:
                            break
            if best_len >= 3:
                flags |= 1 << (7 - bit)
                d = best_disp - 1
                out.append(((best_len - 3) << 4) | ((d >> 8) & 0xF))
                out.append(d & 0xFF)
                pos += best_len
            else:
                out.append(data[pos])
                pos += 1
        out[flag_pos] = flags
    return bytes(out)


def gba_lz_decode(blob: bytes) -> bytes:
    if len(blob) < 4 or blob[0] != 0x10:
        raise ValueError("not GBA LZ")
    target = blob[1] | (blob[2] << 8) | (blob[3] << 16)
    out = bytearray()
    p = 4
    while len(out) < target:
        flags = blob[p]
        p += 1
        for bit in range(8):
            if len(out) >= target:
                break
            if flags & (1 << (7 - bit)):
                a, b = blob[p], blob[p + 1]
                p += 2
                length = (a >> 4) + 3
                disp = (((a & 0xF) << 8) | b) + 1
                for _ in range(length):
                    out.append(out[-disp])
            else:
                out.append(blob[p])
                p += 1
    return bytes(out[:target])


def normalize(s: str) -> str:
    return re.sub(r"[^a-z0-9]", "", s.lower())


def parse_native_symbols(elf: Path, nm: str) -> tuple[dict[str, list[tuple[str, int]]], dict[str, list[tuple[str, int]]]]:
    text = subprocess.check_output([nm, "-S", "--defined-only", str(elf)], text=True, errors="replace")
    front: dict[str, list[tuple[str, int]]] = defaultdict(list)
    back: dict[str, list[tuple[str, int]]] = defaultdict(list)
    rx = re.compile(r"^[0-9A-Fa-f]+\s+([0-9A-Fa-f]+)\s+\S\s+(gMon(Front|Back)Pic_(\S+))$")
    for line in text.splitlines():
        m = rx.match(line.strip())
        if not m:
            continue
        size = int(m.group(1), 16)
        full, side, suffix = m.group(2), m.group(3), m.group(4)
        (front if side == "Front" else back)[normalize(suffix)].append((full, size))
    return front, back


def resolve_native(slug: str, species_constant: str, table: dict[str, list[tuple[str, int]]]):
    keys = [normalize(slug), normalize(species_constant.removeprefix("SPECIES_"))]
    found = []
    for key in dict.fromkeys(keys):
        found.extend(table.get(key, []))
    unique = {(name, size) for name, size in found}
    if len(unique) == 1:
        return next(iter(unique))
    return None


def zip_index(zf: zipfile.ZipFile) -> dict[tuple[str, str], str]:
    idx: dict[tuple[str, str], str] = {}
    duplicates = set()
    for name in zf.namelist():
        parts = PurePosixPath(name).parts
        if len(parts) < 2 or not parts[-1].lower().endswith(".gif"):
            continue
        key = (parts[-2].lower(), parts[-1].lower())
        if key in idx:
            duplicates.add(key)
        else:
            idx[key] = name
    for key in duplicates:
        idx.pop(key, None)
    return idx


def ticks(ms: int) -> int:
    return max(1, int(round(ms / (1000.0 / 60.0))))


def select_indices(ds: list[int], wanted: int) -> list[int]:
    n = len(ds)
    wanted = min(wanted, n)
    if wanted >= n:
        return list(range(n))
    starts = []
    t = 0
    for d in ds:
        starts.append(t)
        t += d
    chosen = {0}
    for slot in range(1, wanted):
        target = t * slot / wanted
        chosen.add(min(range(n), key=lambda i: (abs(starts[i] - target), i)))
    while len(chosen) < wanted:
        remain = [i for i in range(n) if i not in chosen]
        chosen.add(max(remain, key=lambda i: min(abs(starts[i] - starts[j]) for j in chosen)))
    return sorted(chosen)


def encode_selected_gif(data: bytes, selected_union: set[int], palette_path: Path, conv) -> tuple[dict[int, bytes], list[int], tuple[int, int]]:
    host_palette, source_count = conv.read_jasc_palette(palette_path)
    visible = list(host_palette[1:source_count])
    transparent = host_palette[0]
    encoded: dict[int, bytes] = {}
    durations: list[int] = []
    with Image.open(io.BytesIO(data)) as im:
        source_size = im.size
        n = int(getattr(im, "n_frames", 1))
        for i in range(n):
            im.seek(i)
            durations.append(ticks(int(im.info.get("duration", 100) or 100)))
            if i not in selected_union:
                continue
            rgba = im.convert("RGBA").copy()
            fi = conv.FrameInfo(rgba, int(im.info.get("duration", 100) or 100))
            transformed = conv.transform_frames([fi], source_size)[0].image
            indexed = conv.index_frame(transformed, visible, transparent)
            encoded[i] = conv.encode_4bpp(indexed)
    return encoded, durations, source_size


def measure_lane(data: bytes, palette_path: Path, conv) -> dict:
    with Image.open(io.BytesIO(data)) as im:
        ds = []
        for i in range(int(getattr(im, "n_frames", 1))):
            im.seek(i)
            ds.append(ticks(int(im.info.get("duration", 100) or 100)))
    selections = {k: select_indices(ds, k) for k in SAMPLE_COUNTS}
    union = set(i for values in selections.values() for i in values)
    frames, ds2, source_size = encode_selected_gif(data, union, palette_path, conv)
    if ds != ds2:
        raise AssertionError("GIF timing changed between passes")
    frame0_lz = gba_lz(frames[0])
    if gba_lz_decode(frame0_lz) != frames[0]:
        raise AssertionError("frame0 GBA LZ roundtrip failed")
    result = {
        "source_size": list(source_size),
        "source_frames": len(ds),
        "source_ticks": sum(ds),
        "frame0_gba_lz_bytes_aligned": align4(len(frame0_lz)),
        "sampled": {},
    }
    for k, selected in selections.items():
        payload = 0
        blobs = 0
        for pos, src in enumerate(selected):
            dst = selected[(pos + 1) % len(selected)]
            delta = bytes(a ^ b for a, b in zip(frames[src], frames[dst]))
            if any(delta):
                comp = gba_lz(delta)
                if gba_lz_decode(comp) != delta:
                    raise AssertionError("delta GBA LZ roundtrip failed")
                payload += align4(len(comp))
                blobs += 1
        descriptor = len(selected) * 8 + 16
        result["sampled"][str(k)] = {
            "selected": selected,
            "delta_blob_count": blobs,
            "delta_gba_lz_bytes_aligned": payload,
            "descriptor_bytes": descriptor,
            "incremental_bytes": payload + descriptor,
        }
    return result


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--catalog", type=Path, required=True)
    ap.add_argument("--sprites-zip", type=Path, required=True)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--elf", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--converter", type=Path, required=True)
    ap.add_argument("--nm", default="arm-none-eabi-nm")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    conv = load_converter(args.converter)
    catalog = json.loads(args.catalog.read_text(encoding="utf-8"))
    rows = [r for r in catalog["rows"] if r.get("runtime_candidate", False)]
    rows.sort(key=lambda r: r["slug"])
    front_symbols, back_symbols = parse_native_symbols(args.elf, args.nm)
    rom = args.rom.read_bytes()
    clean_used = len(rom.rstrip(b"\xff"))
    trailing = len(rom) - clean_used

    totals = {
        "species": 0,
        "lanes": 0,
        "native_reclaim_bytes": 0,
        "native_reclaim_species": 0,
        "showdown_frame0_bytes": 0,
        "sampled_incremental_bytes": {str(k): 0 for k in SAMPLE_COUNTS},
    }
    native_unresolved = []
    species_rows = []

    with zipfile.ZipFile(args.sprites_zip) as zf:
        zi = zip_index(zf)
        for n, row in enumerate(rows, 1):
            slug = row["slug"]
            source = row.get("front_source_slug") or slug
            if source != (row.get("back_source_slug") or slug):
                raise RuntimeError(f"front/back source mismatch: {slug}")
            palette = args.soulgold / "graphics" / "pokemon" / slug / "normal.pal"
            native_front = resolve_native(slug, row["species_constant"], front_symbols)
            native_back = resolve_native(slug, row["species_constant"], back_symbols)
            native_bytes = 0
            if native_front and native_back:
                native_bytes = native_front[1] + native_back[1]
                totals["native_reclaim_bytes"] += native_bytes
                totals["native_reclaim_species"] += 1
            else:
                native_unresolved.append({"slug": slug, "front": native_front, "back": native_back})

            sr = {"slug": slug, "source": source, "native_reclaim_bytes": native_bytes, "lanes": {}}
            for lane, dirname in (("front", "ani"), ("back", "ani-back")):
                member = zi.get((dirname, f"{source}.gif".lower()))
                if member is None:
                    raise RuntimeError(f"missing exact indexed GIF for {slug} {lane} source={source}")
                measured = measure_lane(zf.read(member), palette, conv)
                sr["lanes"][lane] = measured
                totals["lanes"] += 1
                totals["showdown_frame0_bytes"] += measured["frame0_gba_lz_bytes_aligned"]
                for k in SAMPLE_COUNTS:
                    totals["sampled_incremental_bytes"][str(k)] += measured["sampled"][str(k)]["incremental_bytes"]
            totals["species"] += 1
            species_rows.append(sr)
            if n % 50 == 0:
                print(f"measured {n}/{len(rows)} species", flush=True)

    # Registry reserve is separate from per-lane descriptors. Add a conservative
    # global species lookup table plus runtime/code reserve.
    registry = totals["species"] * 8
    budgets = {}
    for k in SAMPLE_COUNTS:
        projected = (
            clean_used
            - totals["native_reclaim_bytes"]
            + totals["showdown_frame0_bytes"]
            + totals["sampled_incremental_bytes"][str(k)]
            + registry
            + RUNTIME_RESERVE_BYTES
        )
        budgets[str(k)] = {
            "projected_used_bytes": projected,
            "projected_used_mib": round(projected / 1048576, 4),
            "headroom_bytes": ROM_LIMIT - projected,
            "headroom_mib": round((ROM_LIMIT - projected) / 1048576, 4),
            "fits_32mib": projected <= ROM_LIMIT,
        }

    report = {
        "format": "soulgold-showdown-full-rom-budget-v1",
        "rom_limit_bytes": ROM_LIMIT,
        "clean_rom_bytes": len(rom),
        "clean_used_bytes": clean_used,
        "clean_used_mib": round(clean_used / 1048576, 4),
        "clean_trailing_ff_bytes": trailing,
        "clean_trailing_ff_mib": round(trailing / 1048576, 4),
        "runtime_reserve_bytes": RUNTIME_RESERVE_BYTES,
        "registry_bytes": registry,
        "totals": totals,
        "native_unresolved_count": len(native_unresolved),
        "native_unresolved": native_unresolved,
        "budgets": budgets,
        "species": species_rows,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({
        "species": totals["species"],
        "native_reclaim_bytes": totals["native_reclaim_bytes"],
        "showdown_frame0_bytes": totals["showdown_frame0_bytes"],
        "clean_trailing_ff_bytes": trailing,
        "sampled_incremental_bytes": totals["sampled_incremental_bytes"],
        "budgets": budgets,
        "native_unresolved_count": len(native_unresolved),
    }, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
