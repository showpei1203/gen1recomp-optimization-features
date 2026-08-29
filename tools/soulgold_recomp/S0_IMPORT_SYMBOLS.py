#!/usr/bin/env python3
"""SoulGold -> GBARecomp symbol bootstrap.

Consumes a locally built SoulGold ROM/ELF/MAP and the pinned gbarecomp
symbol importer. No ROM bytes or generated ROM-derived output are committed.

SoulGold's modern linker gives IWRAM/EWRAM objects RAM VMAs and ROM LMAs, then
InitializeWorkingMemory copies the images at boot. For executable RAM symbols,
GBARecomp needs explicit [[code_copy]] mappings so the function finder can read
the authoritative ROM backing. We emit mappings per ELF FUNC, not per whole RAM
image, to avoid making ordinary RAM data look executable to speculative scans.
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
    "__iwram_start", "__iwram_end", "__iwram_lma",
    "__ewram_start", "__ewram_end", "__ewram_lma",
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
    funcs: list[tuple[int, int, int, str]] = []
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
            funcs.append((value & ~1, value & 1, size, name))
    return values, funcs


def choose_readelf() -> str:
    for name in ("arm-none-eabi-readelf", "readelf"):
        found = shutil.which(name)
        if found:
            return found
    raise SystemExit("readelf not found (need arm-none-eabi-readelf or readelf)")


def checked_region(values, prefix: str, lo: int, hi: int):
    start = values[f"__{prefix}_start"][0]
    end = values[f"__{prefix}_end"][0]
    lma = values[f"__{prefix}_lma"][0]
    if not (lo <= start <= end <= hi):
        raise SystemExit(
            f"unexpected {prefix.upper()} range 0x{start:08X}..0x{end:08X}")
    if not (0x08000000 <= lma <= 0x09FFFFFF):
        raise SystemExit(f"unexpected __{prefix}_lma 0x{lma:08X}")
    return start, end, lma


def funcs_in_region(funcs, start: int, end: int):
    return sorted(
        (addr, thumb, size, name)
        for addr, thumb, size, name in funcs
        if start <= addr < end
    )


def emit_copy_blocks(region: str, rows, start: int, lma: int):
    blocks: list[str] = []
    skipped: list[tuple[int, int, int, str]] = []
    for addr, thumb, size, name in rows:
        if size <= 0:
            skipped.append((addr, thumb, size, name))
            continue
        source = lma + (addr - start)
        safe_name = re.sub(r"[^A-Za-z0-9_.-]", "_", name)
        blocks.append(
            "[[code_copy]]\n"
            f"runtime_start = 0x{addr:08X}\n"
            f"source_start = 0x{source:08X}\n"
            f"size = 0x{size:X}\n"
            f"name = \"SoulGold_{region}_{safe_name}\"\n"
            f"note = \"ELF FUNC {name}; {region} VMA backed by linker ROM LMA\"\n"
        )
    return blocks, skipped


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

    iwram_start, iwram_end, iwram_lma = checked_region(
        values, "iwram", 0x03000000, 0x03008000)
    ewram_start, ewram_end, ewram_lma = checked_region(
        values, "ewram", 0x02000000, 0x02040000)

    iwram_funcs = funcs_in_region(funcs, iwram_start, iwram_end)
    ewram_funcs = funcs_in_region(funcs, ewram_start, ewram_end)
    iwram_blocks, iwram_skipped = emit_copy_blocks(
        "IWRAM", iwram_funcs, iwram_start, iwram_lma)
    ewram_blocks, ewram_skipped = emit_copy_blocks(
        "EWRAM", ewram_funcs, ewram_start, ewram_lma)

    copies = out / "SOULGOLD_runtime_copies.toml"
    header = (
        "# AUTO-GENERATED by S0_IMPORT_SYMBOLS.py\n"
        "# Precise RAM code mappings derived from ELF FUNC symbols and the\n"
        "# modern linker's RAM VMA <-> ROM LMA relationship.\n"
        "# Compose after game.toml and SOULGOLD_BETA1_symbols.toml.\n\n"
    )
    copies.write_text(
        header + "\n".join(iwram_blocks + ewram_blocks),
        encoding="utf-8", newline="\n")

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
        f"IWRAM_FUNC_COUNT={len(iwram_funcs)}",
        f"IWRAM_CODE_COPY_COUNT={len(iwram_blocks)}",
        f"EWRAM_START=0x{ewram_start:08X}",
        f"EWRAM_END=0x{ewram_end:08X}",
        f"EWRAM_LMA=0x{ewram_lma:08X}",
        f"EWRAM_FUNC_COUNT={len(ewram_funcs)}",
        f"EWRAM_CODE_COPY_COUNT={len(ewram_blocks)}",
        "RAM_FUNCS:",
    ]
    for region, rows in (("IWRAM", iwram_funcs), ("EWRAM", ewram_funcs)):
        lines.extend(
            f"  {region}\t0x{addr:08X}\t{'thumb' if thumb else 'arm'}\t"
            f"size=0x{size:X}\t{name}"
            for addr, thumb, size, name in rows
        )
    skipped = iwram_skipped + ewram_skipped
    lines.append(f"RAM_ZERO_SIZE_FUNC_COUNT={len(skipped)}")
    for addr, thumb, size, name in skipped:
        lines.append(
            f"  SKIP_ZERO_SIZE\t0x{addr:08X}\t"
            f"{'thumb' if thumb else 'arm'}\t{name}")
    report.write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")

    print(f"==> wrote {copies}")
    print(f"==> wrote {report}")
    print(f"==> precise RAM code copies: IWRAM={len(iwram_blocks)} EWRAM={len(ewram_blocks)}")
    print(f"==> zero-size RAM funcs skipped: {len(skipped)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
