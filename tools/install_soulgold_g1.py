#!/usr/bin/env python3
"""Install the SoulGold G1 PMD rolling-cache candidate into a clean checkout.

Run prepare_soulgold_g1_assets.py first.

G1 intentionally modifies only src/battle_main.c in the host:
- include the prototype manager;
- initialize it once after CB2_InitBattleInternal finishes setup;
- tick it once per battle software tick after native tasks have updated.

No battle-controller hook, no species-table edit, no MAX_MON_PIC_FRAMES change,
and no replacement of native sprite animation tables is permitted in G1.
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
    dirty = git(repo, "status", "--porcelain")
    if dirty:
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

    if text == original:
        print("battle_main.c already contains G1 hooks")
        return
    path.write_text(text, encoding="utf-8")
    print("PATCH src/battle_main.c: include + init + software-tick hook")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True,
                    help="the staging/ directory produced by prepare_soulgold_g1_assets.py")
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    proto = framework / "prototype" / "soulgold_g1"

    require_clean_exact_checkout(soulgold)

    for name in ("pmd_gba_runtime.c", "pmd_soulgold_adapter.c", "pmd_soulgold_prototype.c"):
        copy_file(proto / name, soulgold / "src" / name)
    for name in ("pmd_gba_runtime.h", "pmd_soulgold_adapter.h", "pmd_soulgold_prototype.h"):
        copy_file(proto / name, soulgold / "include" / name)

    for variant in ("player", "opponent"):
        copy_file(
            staging / "src" / f"pmd_cyndaquil_{variant}_walk.c",
            soulgold / "src" / f"pmd_cyndaquil_{variant}_walk.c",
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
    (soulgold / "PMD_G1_INSTALL_STATUS.txt").write_text(
        "SoulGold G1 PMD rolling-cache candidate installed.\n"
        f"baseline={SOULGOLD_REV}\n"
        "scope=Cyndaquil Walk 4F, player/opponent, move-selection-only\n"
        "host_files_modified=src/battle_main.c only\n"
        "MAX_MON_PIC_FRAMES=UNCHANGED\n"
        "native sprite->anims=UNCHANGED\n"
        "compile_status=PENDING\n"
        "runtime_status=PENDING\n\n"
        + status + "\n",
        encoding="utf-8",
    )

    print("G1 install candidate prepared. Next authority gate: make -j, then mGBA visual evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
