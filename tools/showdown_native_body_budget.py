#!/usr/bin/env python3
"""Measure linked SoulGold front/back battler body payload from the final ELF.

This deliberately uses linker symbols instead of source PNG sizes. The question is
how many bytes are actually resident in the GBA ROM and therefore potentially
replaceable by Showdown frame-0 bodies.
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path

SYM_RE = re.compile(r"^[0-9A-Fa-f]+\s+([0-9A-Fa-f]+)\s+\S\s+(gMon(?:Front|Back)Pic_\S+)$")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--elf", type=Path, required=True)
    ap.add_argument("--rom", type=Path, required=True)
    ap.add_argument("--nm", default="arm-none-eabi-nm")
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()

    out = subprocess.check_output(
        [args.nm, "-S", "--defined-only", str(args.elf)], text=True, errors="replace"
    )
    rows = []
    for line in out.splitlines():
        m = SYM_RE.match(line.strip())
        if not m:
            continue
        size = int(m.group(1), 16)
        name = m.group(2)
        side = "front" if name.startswith("gMonFrontPic_") else "back"
        rows.append({"name": name, "side": side, "bytes": size})

    front = [r for r in rows if r["side"] == "front"]
    back = [r for r in rows if r["side"] == "back"]
    rom = args.rom.read_bytes()
    used_end = len(rom.rstrip(b"\xff"))
    trailing_ff = len(rom) - used_end

    report = {
        "elf": str(args.elf),
        "rom": str(args.rom),
        "rom_bytes": len(rom),
        "rom_last_non_ff_plus_one": used_end,
        "rom_trailing_ff_bytes": trailing_ff,
        "rom_trailing_ff_mib": round(trailing_ff / 1048576, 4),
        "linked_front_symbol_count": len(front),
        "linked_back_symbol_count": len(back),
        "linked_front_payload_bytes": sum(r["bytes"] for r in front),
        "linked_back_payload_bytes": sum(r["bytes"] for r in back),
        "linked_front_back_payload_bytes": sum(r["bytes"] for r in rows),
        "linked_front_back_payload_mib": round(sum(r["bytes"] for r in rows) / 1048576, 4),
        "largest_20": sorted(rows, key=lambda r: r["bytes"], reverse=True)[:20],
        "symbols": sorted(rows, key=lambda r: r["name"]),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: report[k] for k in report if k not in ("symbols", "largest_20")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
