#!/usr/bin/env python3
"""Measure real lossless single-OBJ eligibility from PMDCollab visible pixels.

G4A intentionally used source frame dimensions as a conservative first roster
screen. G3R6B already proved that this is too pessimistic: PMD canvases may be
larger than 64x64 while every opaque pixel still fits a 64x64 GBA battler OBJ.
Transparent source overflow is harmless; opaque overflow is not.

G4D therefore audits every core action frame on both SoulGold battle views. It
aligns PMDCollab's green body-center marker to ONE common action-independent
64x64 anchor per side, intersects the exact legal anchor ranges of all opaque
pixels, and requires every visible source pixel to fit. No crop, scale,
resample, or per-action body-center drift is permitted.

Species that fail remain candidates for a later multi-OBJ renderer. Missing or
malformed PMD source remains native SoulGold by policy.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

import pmd_gba_converter as pmd
import audit_soulgold_g4a_pmd_roster_coverage as g4a

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
CORE_ACTIONS = ("Idle", "Walk", "Hurt", "Attack", "Shoot")
VIEWS = (("player", "UpRight"), ("opponent", "DownLeft"))
TARGET_ANCHOR = (32, 44)
CANVAS = 64


def crop_frame(sheet: Image.Image, action: pmd.ResolvedAction, direction: str, index: int) -> Image.Image:
    fw, fh = action.frame_width, action.frame_height
    if sheet.width < fw * action.frame_count:
        raise ValueError(f"sheet width {sheet.width} < expected {fw * action.frame_count}")
    if sheet.height == fh:
        row = 0
    elif sheet.height >= fh * 8:
        row = pmd.DIRECTIONS.index(direction)
    else:
        raise ValueError(f"unsupported source rows: sheet={sheet.size}, frame={fw}x{fh}")
    x = index * fw
    y = row * fh
    if x + fw > sheet.width or y + fh > sheet.height:
        raise ValueError(f"frame crop outside sheet: action={action.requested_name} frame={index} row={row}")
    return sheet.crop((x, y, x + fw, y + fh))


def opaque_bbox(frame: Image.Image):
    alpha = frame.getchannel("A")
    box = alpha.getbbox()
    if box is None:
        raise ValueError("frame has no opaque pixels")
    return box  # left, top, right-exclusive, bottom-exclusive


def legal_anchor(center: tuple[int, int], box: tuple[int, int, int, int]) -> dict:
    left, top, right, bottom = box
    cx, cy = center
    return {
        "x": [cx - left, cx + CANVAS - right],
        "y": [cy - top, cy + CANVAS - bottom],
        "opaque_extent": [right - left, bottom - top],
        "opaque_bbox": [left, top, right - 1, bottom - 1],
    }


def clamp(v: int, lo: int, hi: int) -> int:
    return max(lo, min(v, hi))


def inspect_view(species_dir: Path, actions: dict, direction: str) -> dict:
    xlo, xhi = -32768, 32767
    ylo, yhi = -32768, 32767
    action_records = {}
    failure = None
    for action_name in CORE_ACTIONS:
        try:
            action = g4a.resolve_action_compat(action_name, actions)
            anim_path = species_dir / f"{action.source_action}-Anim.png"
            offsets_path = species_dir / f"{action.source_action}-Offsets.png"
            shadow_path = species_dir / f"{action.source_action}-Shadow.png"
            if not anim_path.is_file() or not offsets_path.is_file() or not shadow_path.is_file():
                raise FileNotFoundError(f"missing Anim/Offsets/Shadow for {action.source_action}")
            anim = Image.open(anim_path).convert("RGBA")
            offsets = Image.open(offsets_path).convert("RGBA")
            shadow = Image.open(shadow_path).convert("RGBA")
            if anim.size != offsets.size or anim.size != shadow.size:
                raise ValueError(f"Anim/Offsets/Shadow size mismatch: {anim.size}/{offsets.size}/{shadow.size}")
            frames = []
            for i in range(action.frame_count):
                body = crop_frame(anim, action, direction, i)
                off = crop_frame(offsets, action, direction, i)
                center = pmd.body_center_from_offsets(off)
                box = opaque_bbox(body)
                legal = legal_anchor(center, box)
                fxlo, fxhi = legal["x"]
                fylo, fyhi = legal["y"]
                if fxlo > fxhi or fylo > fyhi:
                    raise ValueError(
                        f"opaque extent cannot fit 64x64 at any anchor: frame={i}, "
                        f"extent={legal['opaque_extent']} legal_x={legal['x']} legal_y={legal['y']}"
                    )
                xlo, xhi = max(xlo, fxlo), min(xhi, fxhi)
                ylo, yhi = max(ylo, fylo), min(yhi, fyhi)
                frames.append({
                    "frame": i,
                    "duration": int(action.durations[i]),
                    "source_frame_size": [action.frame_width, action.frame_height],
                    "body_center": [int(center[0]), int(center[1])],
                    **legal,
                })
            action_records[action_name] = {
                "source_action": action.source_action,
                "frame_count": action.frame_count,
                "frames": frames,
            }
        except Exception as exc:
            failure = f"{action_name}:{type(exc).__name__}:{exc}"
            break

    common = None
    if failure is None and xlo <= xhi and ylo <= yhi:
        common = {
            "x_range": [xlo, xhi],
            "y_range": [ylo, yhi],
            "selected": [clamp(TARGET_ANCHOR[0], xlo, xhi), clamp(TARGET_ANCHOR[1], ylo, yhi)],
            "target": list(TARGET_ANCHOR),
        }
    elif failure is None:
        failure = f"NO_COMMON_CORE_ANCHOR:x=[{xlo},{xhi}] y=[{ylo},{yhi}]"

    return {
        "direction": direction,
        "lossless_single_obj": common is not None,
        "common_anchor": common,
        "failure": failure,
        "actions": action_records,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    soulgold = args.soulgold.resolve()
    sprite_root = args.spritecollab.resolve() / "sprite"
    dex_names = g4a.parse_national_dex(soulgold / "include/constants/pokedex.h")

    counts = {
        "LOSSLESS_SINGLE_OBJ_BOTH_SIDES": 0,
        "MULTI_OBJ_REQUIRED": 0,
        "NATIVE_FALLBACK_MISSING_OR_INVALID_CORE": 0,
    }
    records = []
    for dex, dex_name in enumerate(dex_names, 1):
        species_dir = sprite_root / f"{dex:04d}"
        rec = {
            "national_dex": dex,
            "national_dex_constant": f"NATIONAL_DEX_{dex_name}",
            "pmd_path": f"sprite/{dex:04d}",
            "views": {},
        }
        animdata = species_dir / "AnimData.xml"
        if not animdata.is_file():
            rec["eligibility"] = "NATIVE_FALLBACK_MISSING_OR_INVALID_CORE"
            rec["reason"] = "NO_CANONICAL_ANIMDATA"
            counts[rec["eligibility"]] += 1
            records.append(rec)
            continue
        try:
            actions = g4a.parse_anim_data_compat(animdata)
            for action_name in CORE_ACTIONS:
                g4a.resolve_action_compat(action_name, actions)
        except Exception as exc:
            rec["eligibility"] = "NATIVE_FALLBACK_MISSING_OR_INVALID_CORE"
            rec["reason"] = f"CORE_ACTION_RESOLVE_ERROR:{type(exc).__name__}:{exc}"
            counts[rec["eligibility"]] += 1
            records.append(rec)
            continue

        for side, direction in VIEWS:
            rec["views"][side] = inspect_view(species_dir, actions, direction)
        if all(rec["views"][side]["lossless_single_obj"] for side, _ in VIEWS):
            rec["eligibility"] = "LOSSLESS_SINGLE_OBJ_BOTH_SIDES"
            rec["reason"] = "ALL_CORE_OPAQUE_PIXELS_FIT_ONE_COMMON_64X64_ANCHOR_PER_SIDE"
        elif any(
            v["failure"] and ("FileNotFoundError" in v["failure"] or "ACTION" in v["failure"] or "size mismatch" in v["failure"])
            for v in rec["views"].values()
        ):
            rec["eligibility"] = "NATIVE_FALLBACK_MISSING_OR_INVALID_CORE"
            rec["reason"] = "CORE_SOURCE_INVALID_OR_INCOMPLETE"
        else:
            rec["eligibility"] = "MULTI_OBJ_REQUIRED"
            rec["reason"] = "VISIBLE_PIXELS_OR_COMMON_BODY_ANCHOR_EXCEED_SINGLE_OBJ_ON_ONE_OR_BOTH_SIDES"
        counts[rec["eligibility"]] += 1
        records.append(rec)

    source_complete = counts["LOSSLESS_SINGLE_OBJ_BOTH_SIDES"] + counts["MULTI_OBJ_REQUIRED"]
    summary = {
        "phase": "G4D_LOSSLESS_SINGLE_OBJ_AUDIT",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "national_dex_count": len(dex_names),
        "core_actions": list(CORE_ACTIONS),
        "views": {side: direction for side, direction in VIEWS},
        "target_body_anchor": list(TARGET_ANCHOR),
        "policy": "OPAQUE_PIXEL_CONSERVATION_PLUS_ONE_COMMON_BODY_ANCHOR_PER_SIDE",
        "transparent_source_overflow": "ALLOWED",
        "opaque_source_overflow": "FORBIDDEN_FOR_SINGLE_OBJ",
        "crop_scale_resample": "FORBIDDEN",
        "fallback": "MISSING_OR_INVALID_PMD_REMAINS_NATIVE_SOULGOLD",
        "counts": counts,
        "source_complete_core_count": source_complete,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("G4D lossless visible-pixel audit PASS")
    print(json.dumps(counts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
