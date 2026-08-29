#!/usr/bin/env python3
"""Generate a minimal SoulGoldRecomp S0 game project from local build evidence.

This intentionally does NOT include the Emerald launcher or Emerald-specific
RAM flash hardcodes. S0 only needs a native runner capable of reaching the
SoulGold title/overworld. Transient stack-executed flash helpers may fall back
to GBARecomp's interpreter during S0; a byte-verified symbol-driven RAM
canonicalizer can be added after boot is proven.
"""

from __future__ import annotations

import argparse
import binascii
import hashlib
import pathlib
import shutil


def digest(path: pathlib.Path, algo: str) -> str:
    h = hashlib.new(algo)
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def copy_text(src: pathlib.Path, dst: pathlib.Path) -> None:
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--workspace", required=True, type=pathlib.Path,
                    help="S0 workspace containing soulgold/ and gbarecomp/")
    ap.add_argument("--out", type=pathlib.Path,
                    help="runner project (default: <workspace>/SoulGoldRecomp)")
    args = ap.parse_args()

    ws = args.workspace.resolve()
    sg = ws / "soulgold"
    gb = ws / "gbarecomp"
    out = (args.out or (ws / "SoulGoldRecomp")).resolve()

    rom = sg / "Soulgold_Beta_1.gba"
    symdir = sg / "_recomp_symbols"
    overlay = symdir / "SOULGOLD_BETA1_symbols.toml"
    runtime_copies = symdir / "SOULGOLD_runtime_copies.toml"
    seeds = symdir / "imported_symbols.tsv"
    data_symbols = symdir / "imported_data_symbols.tsv"
    boundaries = symdir / "function_boundaries.tsv"

    required = [rom, overlay, runtime_copies, seeds, data_symbols, boundaries,
                gb / "CMakeLists.txt"]
    missing = [str(p) for p in required if not p.exists()]
    if missing:
        print("Missing S0 prerequisites:")
        for p in missing:
            print("  -", p)
        print("Run S0_BOOTSTRAP.ps1 -BuildSoulGold and S0_IMPORT_SYMBOLS.py first.")
        return 2

    rom_size = rom.stat().st_size
    rom_sha1 = digest(rom, "sha1")
    rom_sha256 = digest(rom, "sha256")
    crc = 0
    with rom.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            crc = binascii.crc32(chunk, crc)
    crc &= 0xFFFFFFFF

    variant = out / "variants" / "soulgold"
    symbols = variant / "symbols"
    generated = variant / "generated"
    roms = variant / "roms"
    src = out / "src"
    for d in (symbols, generated, roms, src):
        d.mkdir(parents=True, exist_ok=True)

    # Local-only ROM copy. The generated project explicitly ignores it.
    local_rom = roms / "soulgold_beta1.gba"
    shutil.copy2(rom, local_rom)
    for p in (overlay, runtime_copies, seeds, data_symbols, boundaries):
        copy_text(p, symbols / p.name)

    game_toml = f'''# AUTO-GENERATED S0 config from a locally built SoulGold ROM.
# Do not commit ROM-derived identity changes without a deliberate source pin bump.

[game]
name = "Pokemon SoulGold Beta 1"
short_name = "soulgold"
default_region = "custom"

[bios]
path = "../../../gbarecomp/bios/gba_bios.bin"
sha1 = "300c20df6731a33952ded8c436f7f186d25d3492"

[rom]
path = "roms/soulgold_beta1.gba"
sha1 = "{rom_sha1}"

[program]
name = "Pokemon SoulGold Beta 1"
id = "soulgold_beta1"
load_address = 0x08000000
size = 0x{rom_size:08X}
entry_pc = 0x08000000
codegen_shards = 64
static_resume_all = true

[identity]
sha1 = "{rom_sha1}"

[recompiler]
entry_point = "0x08000000"
seeds = "symbols/imported_symbols.tsv"
boundaries = "symbols/function_boundaries.tsv"
out_dir = "generated"
strict = true

[save]
type = "flash1m"

[runtime]
debug_port = 19902
window_title = "SoulGoldRecomp S0"

[functions]
arm = []
thumb = []
'''
    (variant / "game.toml").write_text(game_toml, encoding="utf-8", newline="\n")

    main_cpp = f'''#include <cstdio>
#include "runtime.h"

int main(int argc, char** argv) {{
    gbarecomp::RunOptions opts;
    opts.builtin_game_name = "Pokemon SoulGold Beta 1";
    opts.builtin_rom_sha1 = "{rom_sha1}";
    opts.builtin_rom_crc32 = 0x{crc:08X}u;
    opts.mod_game_id = "pokemon-soulgold-beta1";
    opts.launcher_region = "CUSTOM";

    // S0 deliberately leaves g_runtime_ram_dispatch_hook unset. SoulGold has
    // moving stack copies of a few flash helpers; GBARecomp's interpreter is
    // the correctness fallback until a symbol/byte-verified canonicalizer is
    // validated against this exact ROM.
    return gbarecomp::run_game(argc, argv, opts);
}}
'''
    (src / "main.cpp").write_text(main_cpp, encoding="utf-8", newline="\n")

    cmake = r'''cmake_minimum_required(VERSION 3.20)
project(SoulGoldRecomp C CXX)
set(CMAKE_C_STANDARD 11)
set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

set(GBARECOMP_ROOT "${CMAKE_CURRENT_SOURCE_DIR}/../gbarecomp"
    CACHE PATH "Path to pinned gbarecomp checkout")
set(GBARECOMP_ENABLE_MODS ON CACHE BOOL "Enable data-only mod catalog" FORCE)

if(NOT EXISTS "${GBARECOMP_ROOT}/CMakeLists.txt")
    message(FATAL_ERROR "GBARECOMP_ROOT does not point to the pinned engine checkout")
endif()

add_subdirectory("${GBARECOMP_ROOT}" gbarecomp_build EXCLUDE_FROM_ALL)

file(GLOB SOULGOLD_GENERATED CONFIGURE_DEPENDS
    "${CMAKE_CURRENT_SOURCE_DIR}/variants/soulgold/generated/*.c"
    "${CMAKE_CURRENT_SOURCE_DIR}/variants/soulgold/generated/*.cpp")

if(NOT SOULGOLD_GENERATED)
    message(FATAL_ERROR "No generated SoulGold shards. Run RECOMPILE_S0 first.")
endif()

add_executable(SoulGoldRecomp src/main.cpp ${SOULGOLD_GENERATED})

target_include_directories(SoulGoldRecomp PRIVATE
    "${GBARECOMP_ROOT}/src/armv4t"
    "${GBARECOMP_ROOT}/src/gba"
    "${GBARECOMP_ROOT}/src/runtime"
    "${GBARECOMP_ROOT}/src/debug"
    src)

target_link_libraries(SoulGoldRecomp PRIVATE
    "-Wl,--start-group"
    gbarecomp_runtime
    gbarecomp_debug
    gbarecomp_gba
    gbarecomp_armv4t
    "-Wl,--end-group")

set(RECOMPILED ${SOULGOLD_GENERATED})
list(FILTER RECOMPILED INCLUDE REGEX "/recompiled_[0-9]+\\.cpp$")
if(RECOMPILED)
    set_source_files_properties(${RECOMPILED} PROPERTIES
        COMPILE_OPTIONS "-O1;-g0")
endif()

if(MSVC)
    target_link_options(SoulGoldRecomp PRIVATE /STACK:268435456)
elseif(MINGW OR WIN32)
    target_link_options(SoulGoldRecomp PRIVATE -Wl,--stack,268435456)
endif()
'''
    (out / "CMakeLists.txt").write_text(cmake, encoding="utf-8", newline="\n")

    gitignore = """build/\nvariants/soulgold/generated/*\n!variants/soulgold/generated/README.md\nvariants/soulgold/roms/*.gba\n*.sav\n*.log\n"""
    (out / ".gitignore").write_text(gitignore, encoding="utf-8", newline="\n")
    (generated / "README.md").write_text(
        "Generated locally by gba_recompile. Do not hand-edit or commit ROM-derived shards.\n",
        encoding="utf-8", newline="\n")

    recompile_ps1 = r'''param(
    [string]$GbaRecompile = "..\gbarecomp\build-vs\Release\gba_recompile.exe"
)
$ErrorActionPreference = 'Stop'
if (-not (Test-Path $GbaRecompile)) {
    throw "gba_recompile.exe not found: $GbaRecompile"
}
& $GbaRecompile `
  --rom "variants\soulgold\roms\soulgold_beta1.gba" `
  --config "variants\soulgold\game.toml" `
  --config "variants\soulgold\symbols\SOULGOLD_BETA1_symbols.toml" `
  --config "variants\soulgold\symbols\SOULGOLD_runtime_copies.toml" `
  --symbols "variants\soulgold\symbols\imported_symbols.tsv" `
  --data-symbols "variants\soulgold\symbols\imported_data_symbols.tsv" `
  --out "variants\soulgold\generated" `
  --max-functions 65536
if ($LASTEXITCODE -ne 0) { throw "gba_recompile failed: $LASTEXITCODE" }
Write-Host "RECOMPILE_RESULT=PASS"
'''
    (out / "RECOMPILE_S0.ps1").write_text(recompile_ps1, encoding="utf-8", newline="\n")

    run_bat = r'''@echo off
setlocal
cd /d "%~dp0"
if not exist "build\SoulGoldRecomp.exe" (
  echo ERROR: build\SoulGoldRecomp.exe not found
  pause
  exit /b 1
)
"build\SoulGoldRecomp.exe" --bios "..\gbarecomp\bios\gba_bios.bin" --rom "variants\soulgold\roms\soulgold_beta1.gba" "variants\soulgold\game.toml"
set RC=%ERRORLEVEL%
echo.
echo EXIT_CODE=%RC%
pause
exit /b %RC%
'''
    (out / "RUN_S0.bat").write_text(run_bat, encoding="utf-8", newline="\r\n")

    evidence = out / "S0_RUNNER_AUTHORITY.txt"
    evidence.write_text(
        "SOULGOLD S0 RUNNER AUTHORITY\n"
        f"ROM_SIZE={rom_size}\n"
        f"ROM_SHA1={rom_sha1}\n"
        f"ROM_SHA256={rom_sha256}\n"
        f"ROM_CRC32={crc:08x}\n"
        "MOD_GAME_ID=pokemon-soulgold-beta1\n"
        "RAM_STACK_COPY_POLICY=INTERPRETER_FALLBACK_UNTIL_CANONICALIZER_VALIDATED\n"
        "RESULT=PREPARED\n",
        encoding="utf-8", newline="\n")

    print(f"Prepared minimal S0 runner: {out}")
    print(f"ROM SHA1   : {rom_sha1}")
    print(f"ROM CRC32  : {crc:08x}")
    print("Next: build gba_recompile, run RECOMPILE_S0.ps1, then configure/build SoulGoldRecomp.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
