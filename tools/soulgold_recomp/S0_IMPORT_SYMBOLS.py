#!/usr/bin/env python3
"""SoulGold -> GBARecomp symbol bootstrap.

Consumes a locally built SoulGold ROM/ELF/MAP and the pinned gbarecomp
symbol importer. No ROM bytes or generated ROM-derived output are committed.

The important SoulGold-specific wrinkle is its modern linker layout:
`.iwram` has a RAM VMA but a ROM LMA (`__iwram_lma`) and is copied during
InitializeWorkingMemory. GBARecomp needs an explicit [[code_copy]] so its
function finder can map IWRAM function seeds back to their ROM backing.
"""

from __future__ import annotations

import argparse
import hashlib
import pathlib
import re
import shutil
import subprocess
import sys

SYM_RE = re.compile(
    r"^\s*\d+:\s+([0-9A-Fa-f]+)\s+(\d+)\s+(\S+)\s+(\S+)\s+\S+\s+(\S+)\s+(.+?)\s*$"
)

REQUIRED_LINKER_SYMBOLS = (
    "__iwram_start",
    "__iwram_end",
    "__iwram_lma",
)


def run(cmd: list[str], *, stdout_path: pathlib.Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd), flush=True)
    if stdout_path is None:
        subprocess.run(cmd, check=True)
        return
    with stdout_path.open("w", encoding="utf-8", newline="\n") as fh:
        subprocess.run(cmd, check=True, stdout=fh)


def sha1(path: pathlib.Path) -> str:
    h = hashlib.sha1()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def parse_symbols(path: pathlib.Path):
    values: dict[str, tuple[int, int, str]] = {}
    funcs: list[tuple[int, int, str]] = []
    for line in path.read_text(encoding="utf-8", errors="replace").splitlines():
        m = SYM_RE.match(line)
        if not m:
            continue
        value_s, size_s, typ, _bind, ndx, name = m.groups()
        if ndx == "UND":
            continue
        value = int(value_s, 16)
        size = int(size_s)
        name = name.strip()
        values.setdefault(name, (value, size, typ))
        if typ == "FUNC":
            funcs.append((value & ~1, value & 1, name))
    return values, funcs


def choose_readelf() -> str:
    for name in ("arm-none-eabi-readelf", "readelf"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("readelf not found (need arm-none-eabi-readelf or readelf)")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--soulgold", required=True, type=pathlib.Path,
                    help="local Eemeliri/soulgold checkout after a successful make")
    ap.add_argument("--gbarecomp", required=True, type=pathlib.Path,
                    help="local mstan/gbarecomp checkout")
    ap.add_argument("--out", type=pathlib.Path,
                    help="output symbol dir (default: <soulgold>/_recomp_symbols)")
    args = ap.parse_args()

    sg = args.soulgold.resolve()
    gb = args.gbarecomp.resolve()
    out = (args.out or (sg / "_recomp_symbols")).resolve()
    out.mkdir(parents=True, exist_ok=True)

    rom = sg / "Soulgold_Beta_1.gba"
    elf = sg / "Soulgold_Beta_1.elf"
    link_map = sg / "Soulgold_Beta_1.map"
    importer = gb / "tools" / "symbol_import" / "import_decomp_symbols.py"

    missing = [str(p) for p in (rom, elf, link_map, importer) if not p.exists()]
    if missing:
        print("Missing required inputs:", file=sys.stderr)
        for p in missing:
            print("  -", p, file=sys.stderr)
        return 2

    readelf = choose_readelf()
    syms = out / "soulgold_readelf_syms.txt"
    sections = out / "soulgold_readelf_sections.txt"
    run([readelf, "-sW", str(elf)], stdout_path=syms)
    run([readelf, "-SW", str(elf)], stdout_path=sections)

    # Let the shared importer own the ordinary function/data symbol model.
    run([
        sys.executable, str(importer),
        "--id", "SOULGOLD_BETA1",
        "--name", "Pokemon SoulGold Beta 1",
        "--syms", str(syms),
        "--sections", str(sections),
        "--map", str(link_map),
        "--rom", str(rom),
        "--out", str(out),
    ])

    values, funcs = parse_symbols(syms)
    missing_names = [n for n in REQUIRED_LINKER_SYMBOLS if n not in values]
    if missing_names:
        print("Required modern-linker symbols missing: " + ", ".join(missing_names),
              file=sys.stderr)
        return 3

    iwram_start = values["__iwram_start"][0]
    iwram_end = values["__iwram_end"][0]
    iwram_lma = values["__iwram_lma"][0]
    if not (0x03000000 <= iwram_start < iwram_end <= 0x03008000):
        raise SystemExit(
            f"unexpected IWRAM range 0x{iwram_start:08X}..0x{iwram_end:08X}")
    if not (0x08000000 <= iwram_lma <= 0x09FFFFFF):
        raise SystemExit(f"unexpected __iwram_lma 0x{iwram_lma:08X}")

    iwram_size = iwram_end - iwram_start
    iwram_funcs = sorted(
        (addr, thumb, name) for addr, thumb, name in funcs
        if iwram_start <= addr < iwram_end
    )

    # If an executable symbol is in IWRAM, its bytes must be readable through
    # this mapping. The imported function seeds retain their individual
    # ARM/THUMB modes, so the code_copy itself does not need a single mode.
    copies = out / "SOULGOLD_runtime_copies.toml"
    copies.write_text(
        "# AUTO-GENERATED by S0_IMPORT_SYMBOLS.py\n"
        "# SoulGold modern linker: .iwram VMA is copied from this ROM LMA.\n"
        "# Compose after the hand-authored game.toml and symbol overlay.\n\n"
        "[[code_copy]]\n"
        f"runtime_start = 0x{iwram_start:08X}\n"
        f"source_start = 0x{iwram_lma:08X}\n"
        f"size = 0x{iwram_size:X}\n"
        "name = \"SoulGold_IWRAM_Image\"\n"
        "note = \"ld_script_modern.ld __iwram_start/end copied from __iwram_lma\"\n",
        encoding="utf-8",
        newline="\n",
    )

    report = out / "S0_SYMBOL_IMPORT_REPORT.txt"
    lines = [
        "SOULGOLD S0 SYMBOL IMPORT",
        "RESULT=PASS",
        f"ROM={rom}",
        f"ROM_SIZE={rom.stat().st_size}",
        f"ROM_SHA1={sha1(rom)}",
        f"IWRAM_START=0x{iwram_start:08X}",
        f"IWRAM_END=0x{iwram_end:08X}",
        f"IWRAM_LMA=0x{iwram_lma:08X}",
        f"IWRAM_SIZE=0x{iwram_size:X}",
        f"IWRAM_FUNC_COUNT={len(iwram_funcs)}",
        "IWRAM_FUNCS:",
    ]
    lines.extend(
        f"  0x{addr:08X}\t{'thumb' if thumb else 'arm'}\t{name}"
        for addr, thumb, name in iwram_funcs
    )
    report.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(f"==> wrote {copies}")
    print(f"==> wrote {report}")
    print(f"==> IWRAM code copy 0x{iwram_start:08X} <- 0x{iwram_lma:08X} size=0x{iwram_size:X}")
    print(f"==> IWRAM function seeds: {len(iwram_funcs)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
