#!/usr/bin/env python3
"""Install the SoulGold G2 Rich Ambient candidate into a clean checkout.

G2 preserves the sealed G1 renderer contract. It replaces only the prototype
runtime/manager layer and expands generated Cyndaquil assets. The host patch
surface remains src/battle_main.c only.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
INCLUDE_LINE = '#include "pmd_soulgold_prototype.h"\n'


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def require_clean_exact_checkout(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD")
    if head != SOULGOLD_REV:
        raise SystemExit(f"SoulGold baseline mismatch: expected {SOULGOLD_REV}, got {head}")
    if git(repo, "status", "--porcelain"):
        raise SystemExit("SoulGold checkout is not clean; refusing to patch over local changes")


def copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise SystemExit(f"Missing required source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"COPY {src} -> {dst}")


def patch_battle_main(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text

    if INCLUDE_LINE not in text:
        anchor = '#include "battle_main.h"\n'
        if anchor not in text:
            raise SystemExit("battle_main.c include anchor not found")
        text = text.replace(anchor, anchor + INCLUDE_LINE, 1)

    fn_start = text.find("static void CB2_InitBattleInternal(void)\n{")
    fn_end = text.find("\n#define BUFFER_PARTY_VS_SCREEN_STATUS", fn_start)
    if fn_start < 0 or fn_end < 0:
        raise SystemExit("CB2_InitBattleInternal boundary not found")
    init_fn = text[fn_start:fn_end]
    init_call = "    PmdSoulGoldPrototype_Init();\n"
    if init_call not in init_fn:
        tail = "    gBattleCommunication[MULTIUSE_STATE] = 0;\n}"
        if tail not in init_fn:
            raise SystemExit("CB2_InitBattleInternal tail anchor not found")
        init_fn = init_fn.replace(
            tail,
            "    gBattleCommunication[MULTIUSE_STATE] = 0;\n"
            "    PmdSoulGoldPrototype_Init();\n}"
        )
        text = text[:fn_start] + init_fn + text[fn_end:]

    tick_start = text.find("static void RunBattleSoftwareTick(void)\n{")
    tick_end = text.find("\nstatic void AdvanceBattleFrameRng(void)", tick_start)
    if tick_start < 0 or tick_end < 0:
        raise SystemExit("RunBattleSoftwareTick boundary not found")
    tick_fn = text[tick_start:tick_end]
    tick_call = "    PmdSoulGoldPrototype_Tick();\n"
    if tick_call not in tick_fn:
        tail = "    RunTasks();\n}"
        if tail not in tick_fn:
            raise SystemExit("RunBattleSoftwareTick tail anchor not found")
        tick_fn = tick_fn.replace(
            tail,
            "    RunTasks();\n"
            "    PmdSoulGoldPrototype_Tick();\n}"
        )
        text = text[:tick_start] + tick_fn + text[tick_end:]

    if text != original:
        path.write_text(text, encoding="utf-8")
        print("PATCH src/battle_main.c: include + init + software-tick hook")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    g2 = framework / "prototype" / "soulgold_g2"
    g1 = framework / "prototype" / "soulgold_g1"

    require_clean_exact_checkout(soulgold)

    copy_file(g2 / "pmd_gba_runtime.c", soulgold / "src" / "pmd_gba_runtime.c")
    copy_file(g2 / "pmd_gba_runtime.h", soulgold / "include" / "pmd_gba_runtime.h")
    copy_file(g2 / "pmd_soulgold_prototype.c", soulgold / "src" / "pmd_soulgold_prototype.c")
    copy_file(g2 / "pmd_soulgold_prototype.h", soulgold / "include" / "pmd_soulgold_prototype.h")

    # G2 intentionally reuses the already accepted G1 SoulGold renderer adapter.
    copy_file(g1 / "pmd_soulgold_adapter.c", soulgold / "src" / "pmd_soulgold_adapter.c")
    copy_file(g1 / "pmd_soulgold_adapter.h", soulgold / "include" / "pmd_soulgold_adapter.h")

    for variant in ("player", "opponent"):
        copy_file(
            staging / "src" / f"pmd_cyndaquil_{variant}_ambient.c",
            soulgold / "src" / f"pmd_cyndaquil_{variant}_ambient.c",
        )
        src_graphics = staging / "graphics" / "pmd" / "cyndaquil" / variant
        dst_graphics = soulgold / "graphics" / "pmd" / "cyndaquil" / variant
        if not src_graphics.is_dir():
            raise SystemExit(f"Missing staged graphics: {src_graphics}")
        if dst_graphics.exists():
            shutil.rmtree(dst_graphics)
        dst_graphics.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_graphics, dst_graphics)
        print(f"COPY {src_graphics} -> {dst_graphics}")

    patch_battle_main(soulgold / "src" / "battle_main.c")

    status = git(soulgold, "status", "--short")
    (soulgold / "PMD_G2_INSTALL_STATUS.txt").write_text(
        "SoulGold G2 PMD Rich Ambient candidate installed.\n"
        f"baseline={SOULGOLD_REV}\n"
        "scope=Cyndaquil HOME+Idle+Walk+LookUp+DeepBreath+Rotate, player/opponent\n"
        "host_files_modified=src/battle_main.c only\n"
        "save_structure=UNCHANGED\n"
        "MAX_MON_PIC_FRAMES=UNCHANGED\n"
        "native sprite->anims=UNCHANGED\n"
        "G1_renderer_adapter=REUSED\n"
        "compile_status=PENDING\n"
        "runtime_status=PENDING\n\n"
        + status + "\n",
        encoding="utf-8",
    )

    print("G2 Rich Ambient install candidate prepared. Next authority gate: full make + visual test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
