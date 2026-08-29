#!/usr/bin/env python3
"""Run showdown_full_rom_budget with a content-addressed graphics/delta bank.

Identical frame-0 blobs may share one ROM payload. Identical XOR delta blobs may
also share one payload, including the important two-frame case where A^B == B^A.
Descriptors still pay their normal per-animation cost and point into the shared
bank. This is a buildable storage model, not a compression-ratio fantasy.
"""
from __future__ import annotations

import importlib.util
import io
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


base.measure_lane = measure_lane_dedup
raise SystemExit(base.main())
