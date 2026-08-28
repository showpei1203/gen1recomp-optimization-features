#!/usr/bin/env python3
"""Inventory exact SoulGold battle-runtime paths that can clear sleep.

G3R11 deliberately hooks only ordinary timer wake and Uproar wake in
CancelerAsleepOrFrozen.  G3R12 is a source-authority gate before adding any more
presentation notifications: it inventories mutations around STATUS1_SLEEP and
records whether a path already carries the G3R11 PMD Wake notification.

This tool does not modify battle behavior. Ambiguous cure paths remain native.
"""
from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
SCAN_FILES = (
    "src/battle_move_resolution.c",
    "src/battle_script_commands.c",
    "src/battle_end_turn.c",
    "src/battle_hold_effects.c",
)

MUTATION_PATTERNS = (
    re.compile(r"status1\s*&=\s*~STATUS1_SLEEP"),
    re.compile(r"status1\s*=\s*0\s*;"),
    re.compile(r"status1\s*&=\s*~STATUS1_ANY"),
    re.compile(r"status1\s*=\s*[^;]+"),
)


def context(lines: list[str], idx: int, radius: int = 5) -> dict:
    lo = max(0, idx - radius)
    hi = min(len(lines), idx + radius + 1)
    return {
        "line": idx + 1,
        "start_line": lo + 1,
        "end_line": hi,
        "text": "".join(lines[lo:hi]),
    }


def classify(text: str) -> str:
    t = text.lower()
    if "pmdsoulgoldprototype_notifywake" in t:
        if "uproar" in t:
            return "G3R11_COVERED_UPROAR_WAKE"
        return "G3R11_COVERED_NATIVE_WAKE"
    if "hold_effect" in t or "held item" in t or "item" in t:
        return "NATIVE_ITEM_OR_HOLD_CURE_REVIEW"
    if "ability" in t:
        return "NATIVE_ABILITY_CURE_REVIEW"
    if "end turn" in t or "endturn" in t:
        return "NATIVE_END_TURN_CURE_REVIEW"
    if "move" in t or "effect" in t:
        return "NATIVE_MOVE_OR_SCRIPT_CURE_REVIEW"
    return "NATIVE_CLEAR_PATH_REVIEW"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    root = args.soulgold.resolve()

    records = []
    all_status_refs = 0
    for rel in SCAN_FILES:
        path = root / rel
        if not path.is_file():
            raise SystemExit(f"missing pinned SoulGold source: {rel}")
        lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
        for i, line in enumerate(lines):
            if "STATUS1_SLEEP" not in line:
                continue
            all_status_refs += 1
            c = context(lines, i)
            is_mutation = any(p.search(line) for p in MUTATION_PATTERNS)
            # A number of mutations are split over adjacent source lines, so a
            # local context containing an explicit clear is also a candidate.
            local_clear = "~STATUS1_SLEEP" in c["text"]
            if not (is_mutation or local_clear):
                continue
            c.update({
                "file": rel,
                "source_line": line.rstrip("\n"),
                "classification": classify(c["text"]),
                "has_pmd_wake_notify": "PmdSoulGoldPrototype_NotifyWake" in c["text"],
            })
            # Deduplicate multiple STATUS1_SLEEP references that point at the
            # same clear operation/context.
            key = (rel, c["start_line"], c["end_line"], c["classification"])
            if not any(r["_key"] == key for r in records):
                c["_key"] = key
                records.append(c)

    for r in records:
        r.pop("_key", None)

    covered = [r for r in records if r["has_pmd_wake_notify"]]
    review = [r for r in records if not r["has_pmd_wake_notify"]]
    if len(covered) < 2:
        raise SystemExit(
            f"G3R12 expected at least two G3R11 source-grounded Wake hooks, found {len(covered)}"
        )

    summary = {
        "phase": "G3R12_SLEEP_CLEAR_PATH_AUDIT",
        "soulgold_revision": SOULGOLD_REV,
        "policy": "SOURCE_AUTHORITY_BEFORE_ANY_ADDITIONAL_WAKE_NOTIFICATION",
        "runtime_change": "NONE_AUDIT_ONLY_PARENT_G3R11_RUNTIME",
        "scan_files": list(SCAN_FILES),
        "status1_sleep_reference_count": all_status_refs,
        "sleep_clear_candidate_count": len(records),
        "g3r11_covered_count": len(covered),
        "native_review_count": len(review),
        "records": records,
        "decision": (
            "Only exact native cure/message transitions may receive future PMD Wake notification; "
            "ambiguous item/ability/script/end-turn paths remain SoulGold-native."
        ),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print(f"G3R12 sleep-clear audit PASS: {len(records)} candidates, {len(covered)} covered, {len(review)} review")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
