#!/usr/bin/env python3
"""Audit full SoulGold National Dex against pinned PMDCollab battle assets.

This is the scaling gate before replacing hundreds of native battler sprites.
The safety rule is deliberately boring and therefore useful:

    source-complete + GBA-safe -> eligible for generated PMD registry
    missing / malformed / oversize -> KEEP SOULGOLD NATIVE BATTLE SPRITE

No species is allowed to lose its native fallback. Form/variant directories are
inventoried but not automatically mapped to SoulGold forms in this gate.

PMDCollab legitimately permits CopyOf aliases without their own Index. The old
prototype parser predates that source pattern, so this full-roster audit uses a
source-compatible parser rather than misclassifying an otherwise healthy
species because an unrelated alias omitted redundant metadata.
"""
from __future__ import annotations

import argparse
import json
import re
import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image

import pmd_gba_converter as pmd

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
SPRITECOLLAB_REV = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"
CORE_ACTIONS = ("Idle", "Walk", "Hurt", "Attack", "Shoot")
OPTIONAL_ACTIONS = ("Nod", "Rotate", "Sleep", "EventSleep", "Wake")
ALL_ACTIONS = CORE_ACTIONS + OPTIONAL_ACTIONS


def parse_national_dex(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    start = text.index("enum NationalDexOrder")
    body = text[start:text.index("NATIONAL_DEX_COUNT", start)]
    names = []
    for line in body.splitlines():
        m = re.match(r"\s*NATIONAL_DEX_([A-Z0-9_]+)\s*,", line)
        if not m:
            continue
        name = m.group(1)
        if name == "NONE":
            continue
        names.append(name)
    if len(names) < 151:
        raise SystemExit(f"implausible SoulGold National Dex parse: {len(names)} entries")
    return names


def text_int(parent: ET.Element, tag: str):
    node = parent.find(tag)
    if node is None or node.text is None or not node.text.strip():
        return None
    return int(node.text.strip())


def parse_anim_data_compat(path: Path) -> dict:
    """Parse current PMDCollab XML, including CopyOf aliases without Index."""
    root = ET.parse(path).getroot()
    actions = {}
    for anim in root.findall("./Anims/Anim"):
        name_node = anim.find("Name")
        if name_node is None or name_node.text is None or not name_node.text.strip():
            raise ValueError("AnimData.xml contains an Anim without Name")
        name = name_node.text.strip()
        copy_node = anim.find("CopyOf")
        copy_of = copy_node.text.strip() if copy_node is not None and copy_node.text and copy_node.text.strip() else None
        index = text_int(anim, "Index")
        if index is None and copy_of is None:
            raise ValueError(f"non-CopyOf action {name} lacks Index")
        durations = tuple(
            int(n.text.strip())
            for n in anim.findall("./Durations/Duration")
            if n.text and n.text.strip()
        )
        actions[name] = pmd.ActionMeta(
            name=name,
            index=index,
            copy_of=copy_of,
            frame_width=text_int(anim, "FrameWidth"),
            frame_height=text_int(anim, "FrameHeight"),
            durations=durations,
            rush_frame=text_int(anim, "RushFrame"),
            hit_frame=text_int(anim, "HitFrame"),
            return_frame=text_int(anim, "ReturnFrame"),
        )
    if not actions:
        raise ValueError(f"No animations found in {path}")
    return actions


def resolve_action_compat(name: str, actions: dict) -> pmd.ResolvedAction:
    if name not in actions:
        raise KeyError(f"Unknown PMD action: {name}")
    requested = actions[name]
    cur = requested
    seen = set()
    while cur.copy_of:
        if cur.name in seen:
            raise ValueError(f"CopyOf cycle while resolving {name}: {sorted(seen)}")
        seen.add(cur.name)
        if cur.copy_of not in actions:
            raise KeyError(f"{cur.name} CopyOf references missing action {cur.copy_of}")
        cur = actions[cur.copy_of]
    if cur.index is None:
        raise ValueError(f"resolved source action {cur.name} lacks Index")
    if cur.frame_width is None or cur.frame_height is None or not cur.durations:
        raise ValueError(f"Resolved PMD action {cur.name} lacks dimensions/durations")
    index = requested.index if requested.index is not None else cur.index
    return pmd.ResolvedAction(
        requested_name=name,
        source_action=cur.name,
        index=index,
        frame_width=cur.frame_width,
        frame_height=cur.frame_height,
        durations=cur.durations,
        rush_frame=requested.rush_frame if requested.rush_frame is not None else cur.rush_frame,
        hit_frame=requested.hit_frame if requested.hit_frame is not None else cur.hit_frame,
        return_frame=requested.return_frame if requested.return_frame is not None else cur.return_frame,
    )


def source_layout(sheet_size: tuple[int, int], action: pmd.ResolvedAction) -> str:
    expected_w = action.frame_width * action.frame_count
    w, h = sheet_size
    if w < expected_w:
        return "INVALID_WIDTH"
    if h == action.frame_height:
        return "DIRECTIONLESS_SINGLE_ROW"
    if h >= action.frame_height * 8:
        return "DIRECTIONAL_8_ROWS_OR_MORE"
    return "UNSUPPORTED_ROW_GEOMETRY"


def inspect_action(species_dir: Path, action_name: str, actions: dict) -> dict:
    rec = {"requested_action": action_name, "available": False}
    if action_name not in actions:
        rec["reason"] = "ACTION_NOT_IN_ANIMDATA"
        return rec
    try:
        action = resolve_action_compat(action_name, actions)
    except Exception as exc:
        rec["reason"] = f"ACTION_RESOLVE_ERROR:{type(exc).__name__}:{exc}"
        return rec
    files = {
        "anim": species_dir / f"{action.source_action}-Anim.png",
        "offsets": species_dir / f"{action.source_action}-Offsets.png",
        "shadow": species_dir / f"{action.source_action}-Shadow.png",
    }
    rec.update({
        "source_action": action.source_action,
        "frame_size": [action.frame_width, action.frame_height],
        "frame_count": action.frame_count,
        "durations": list(action.durations),
        "single_obj_geometry_safe": action.gba_safe_single_obj,
        "files": {k: v.name for k, v in files.items()},
    })
    missing = [k for k, v in files.items() if not v.is_file()]
    if missing:
        rec["reason"] = "MISSING_SOURCE_FILES:" + ",".join(missing)
        return rec
    try:
        sizes = {k: list(Image.open(v).size) for k, v in files.items()}
    except Exception as exc:
        rec["reason"] = f"IMAGE_READ_ERROR:{type(exc).__name__}:{exc}"
        return rec
    rec["sheet_sizes"] = sizes
    if not (sizes["anim"] == sizes["offsets"] == sizes["shadow"]):
        rec["reason"] = "ANIM_OFFSETS_SHADOW_SIZE_MISMATCH"
        return rec
    layout = source_layout(tuple(sizes["anim"]), action)
    rec["source_layout"] = layout
    if layout.startswith("INVALID") or layout.startswith("UNSUPPORTED"):
        rec["reason"] = layout
        return rec
    rec["available"] = True
    rec["reason"] = "OK" if action.gba_safe_single_obj else "NEEDS_MULTI_OBJ"
    return rec


def nested_variant_dirs(species_dir: Path) -> list[str]:
    out = []
    if not species_dir.is_dir():
        return out
    for path in sorted(species_dir.rglob("AnimData.xml")):
        if path.parent == species_dir:
            continue
        out.append(str(path.parent.relative_to(species_dir)))
    return out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    soulgold = args.soulgold.resolve()
    sprite_root = args.spritecollab.resolve() / "sprite"
    dex_names = parse_national_dex(soulgold / "include/constants/pokedex.h")

    counts = {
        "FULL_PMD_SINGLE_OBJ": 0,
        "PMD_CORE_NEEDS_MULTI_OBJ": 0,
        "NATIVE_FALLBACK_MISSING_OR_INVALID_CORE": 0,
    }
    records = []
    for dex, dex_name in enumerate(dex_names, 1):
        species_dir = sprite_root / f"{dex:04d}"
        rec = {
            "national_dex": dex,
            "national_dex_constant": f"NATIONAL_DEX_{dex_name}",
            "pmd_path": f"sprite/{dex:04d}",
            "native_fallback_required": True,
            "variants_unmapped": nested_variant_dirs(species_dir),
            "actions": {},
        }
        animdata = species_dir / "AnimData.xml"
        if not animdata.is_file():
            rec["eligibility"] = "NATIVE_FALLBACK_MISSING_OR_INVALID_CORE"
            rec["reason"] = "NO_CANONICAL_ANIMDATA"
            counts[rec["eligibility"]] += 1
            records.append(rec)
            continue
        try:
            actions = parse_anim_data_compat(animdata)
        except Exception as exc:
            rec["eligibility"] = "NATIVE_FALLBACK_MISSING_OR_INVALID_CORE"
            rec["reason"] = f"ANIMDATA_PARSE_ERROR:{type(exc).__name__}:{exc}"
            counts[rec["eligibility"]] += 1
            records.append(rec)
            continue
        for action_name in ALL_ACTIONS:
            rec["actions"][action_name] = inspect_action(species_dir, action_name, actions)
        core = [rec["actions"][x] for x in CORE_ACTIONS]
        if not all(x["available"] for x in core):
            rec["eligibility"] = "NATIVE_FALLBACK_MISSING_OR_INVALID_CORE"
            rec["reason"] = "CORE_ACTION_SET_INCOMPLETE"
        elif not all(x["single_obj_geometry_safe"] for x in core):
            rec["eligibility"] = "PMD_CORE_NEEDS_MULTI_OBJ"
            rec["reason"] = "CORE_PRESENT_BUT_ONE_OR_MORE_FRAMES_EXCEED_64X64"
        else:
            rec["eligibility"] = "FULL_PMD_SINGLE_OBJ"
            rec["reason"] = "CORE_PRESENT_AND_SINGLE_OBJ_SAFE"
            rec["native_fallback_required"] = False
        counts[rec["eligibility"]] += 1
        records.append(rec)

    summary = {
        "phase": "G4A_FULL_ROSTER_PMD_COVERAGE",
        "soulgold_revision": SOULGOLD_REV,
        "spritecollab_revision": SPRITECOLLAB_REV,
        "soulgold_national_dex_count": len(dex_names),
        "core_actions": list(CORE_ACTIONS),
        "optional_capability_actions": list(OPTIONAL_ACTIONS),
        "xml_policy": "PMDCOLLAB_COPYOF_ALIAS_MAY_OMIT_INDEX_AND_INHERIT_SOURCE_INDEX",
        "policy": "PMD_ELIGIBLE_ONLY_WHEN_CORE_SOURCE_COMPLETE; OTHERWISE_NATIVE_SOULGOLD_FALLBACK",
        "form_policy": "NESTED_PMDCOLLAB_VARIANTS_INVENTORIED_BUT_NOT_AUTO_MAPPED",
        "oversize_policy": "NO_CROP_NO_SCALE; MARK_NEEDS_MULTI_OBJ",
        "counts": counts,
        "records": records,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("G4A roster coverage PASS")
    print(json.dumps(counts, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
