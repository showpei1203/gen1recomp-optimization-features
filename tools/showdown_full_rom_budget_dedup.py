#!/usr/bin/env python3
"""Run showdown_full_rom_budget with content-addressed storage and exact host pointers.

Identical frame-0 blobs share one ROM payload. Identical XOR delta blobs also
share one payload, including the two-frame identity A^B == B^A.

Native reclaim is resolved through SoulGold SpeciesInfo .frontPic/.backPic
pointers rather than guessing symbol names from filesystem slugs. This matters
for forms such as Aegislash Blade/Shield and other host naming differences.
"""
from __future__ import annotations

import importlib.util
import io
import re
import subprocess
import sys
from pathlib import Path

from PIL import Image

TOOLS = Path(__file__).resolve().parent
BASE_PATH = TOOLS / "showdown_full_rom_budget.py"
spec = importlib.util.spec_from_file_location("showdown_full_rom_budget_base", BASE_PATH)
if spec is None or spec.loader is None:
    raise RuntimeError(f"cannot import {BASE_PATH}")
base = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = base
spec.loader.exec_module(base)

FRAME0_BANK: set[bytes] = set()
DELTA_BANKS: dict[int, set[bytes]] = {k: set() for k in base.SAMPLE_COUNTS}
SYMBOL_SIZES: dict[str, int] = {}
SPECIES_PICS: dict[str, tuple[str | None, str | None]] = {}
FRONT_SENTINEL = object()
BACK_SENTINEL = object()


def cli_value(flag: str) -> Path:
    try:
        i = sys.argv.index(flag)
        return Path(sys.argv[i + 1]).resolve()
    except (ValueError, IndexError):
        raise SystemExit(f"missing required {flag}")


def build_species_pic_map(soulgold: Path) -> dict[str, tuple[str | None, str | None]]:
    root = soulgold / "src" / "data" / "pokemon" / "species_info"
    files = sorted(root.rglob("*.h"))
    if not files:
        raise RuntimeError(f"no SpeciesInfo files under {root}")
    result: dict[str, tuple[str | None, str | None]] = {}
    header = re.compile(r"(?m)^\s*\[(SPECIES_[A-Z0-9_]+)\]\s*=\s*$")
    front_rx = re.compile(r"\.frontPic\s*=\s*(gMonFrontPic_[A-Za-z0-9_]+)")
    back_rx = re.compile(r"\.backPic\s*=\s*(gMonBackPic_[A-Za-z0-9_]+)")
    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        matches = list(header.finditer(text))
        for pos, m in enumerate(matches):
            end = matches[pos + 1].start() if pos + 1 < len(matches) else len(text)
            chunk = text[m.end():end]
            f = front_rx.search(chunk)
            b = back_rx.search(chunk)
            if f or b:
                result[m.group(1)] = (f.group(1) if f else None, b.group(1) if b else None)
    return result


def parse_native_symbols_exact(elf: Path, nm: str):
    global SYMBOL_SIZES, SPECIES_PICS
    text = subprocess.check_output([nm, "-S", "--defined-only", str(elf)], text=True, errors="replace")
    rx = re.compile(r"^[0-9A-Fa-f]+\s+([0-9A-Fa-f]+)\s+\S\s+(gMon(?:Front|Back)Pic_\S+)$")
    SYMBOL_SIZES = {}
    for line in text.splitlines():
        m = rx.match(line.strip())
        if m:
            SYMBOL_SIZES[m.group(2)] = int(m.group(1), 16)
    SPECIES_PICS = build_species_pic_map(cli_value("--soulgold"))
    return FRONT_SENTINEL, BACK_SENTINEL


def resolve_native_exact(slug: str, species_constant: str, table):
    pair = SPECIES_PICS.get(species_constant)
    if not pair:
        return None
    symbol = pair[0] if table is FRONT_SENTINEL else pair[1]
    if symbol is None:
        return None
    size = SYMBOL_SIZES.get(symbol)
    if size is None:
        return None
    return symbol, size


def measure_lane_dedup(data: bytes, palette_path: Path, conv) -> dict:
    with Image.open(io.BytesIO(data)) as im:
        ds = []
        for i in range(int(getattr(im, "n_frames", 1))):
            im.seek(i)
            ds.append(base.ticks(int(im.info.get("duration", 100) or 100)))

    selections = {k: base.select_indices(ds, k) for k in base.SAMPLE_COUNTS}
    union = set(i for values in selections.values() for i in values)
    frames, ds2, source_size = base.encode_selected_gif(data, union, palette_path, conv)
    if ds != ds2:
        raise AssertionError("GIF timing changed between passes")

    frame0 = frames[0]
    frame0_lz = base.gba_lz(frame0)
    if base.gba_lz_decode(frame0_lz) != frame0:
        raise AssertionError("frame0 GBA LZ roundtrip failed")
    frame0_new = frame0 not in FRAME0_BANK
    if frame0_new:
        FRAME0_BANK.add(frame0)
    frame0_storage = base.align4(len(frame0_lz)) if frame0_new else 0

    result = {
        "source_size": list(source_size),
        "source_frames": len(ds),
        "source_ticks": sum(ds),
        "frame0_content_addressed_unique": frame0_new,
        "frame0_gba_lz_bytes_aligned": frame0_storage,
        "sampled": {},
    }

    for k, selected in selections.items():
        payload = 0
        transition_count = 0
        unique_new_blobs = 0
        reused_blobs = 0
        bank = DELTA_BANKS[k]
        for pos, src in enumerate(selected):
            dst = selected[(pos + 1) % len(selected)]
            delta = bytes(a ^ b for a, b in zip(frames[src], frames[dst]))
            if not any(delta):
                continue
            transition_count += 1
            if delta in bank:
                reused_blobs += 1
                continue
            comp = base.gba_lz(delta)
            if base.gba_lz_decode(comp) != delta:
                raise AssertionError("delta GBA LZ roundtrip failed")
            bank.add(delta)
            payload += base.align4(len(comp))
            unique_new_blobs += 1

        descriptor = len(selected) * 8 + 16
        result["sampled"][str(k)] = {
            "selected": selected,
            "transition_count": transition_count,
            "unique_new_delta_blobs": unique_new_blobs,
            "reused_delta_blobs": reused_blobs,
            "delta_gba_lz_bytes_aligned": payload,
            "descriptor_bytes": descriptor,
            "incremental_bytes": payload + descriptor,
        }
    return result


base.parse_native_symbols = parse_native_symbols_exact
base.resolve_native = resolve_native_exact
base.measure_lane = measure_lane_dedup
raise SystemExit(base.main())
