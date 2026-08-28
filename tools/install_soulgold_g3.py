#!/usr/bin/env python3
"""Install SoulGold G3 battle-facing Rich Ambient + PMD send-out body prime.

G3 preserves the sealed G1 rolling renderer and G2 HOME/interruption state
machine. It adds two narrowly-scoped host integrations:
- src/battle_main.c: the existing init/software-tick lifecycle hooks;
- src/battle_controllers.c: prime both mon image slots with PMD HOME immediately
  before the native Pokemon sprite is created.

Generated G3 frames already contain authentic PMD per-frame shadows under the
body, so send-out and ambient use one atomic body+shadow frame contract.
The send-out animation/timing/callbacks remain native SoulGold ownership.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
PROTOTYPE_INCLUDE = '#include "pmd_soulgold_prototype.h"\n'


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

    if PROTOTYPE_INCLUDE not in text:
        anchor = '#include "battle_main.h"\n'
        if anchor not in text:
            raise SystemExit("battle_main.c include anchor not found")
        text = text.replace(anchor, anchor + PROTOTYPE_INCLUDE, 1)

    fn_start = text.find("static void CB2_InitBattleInternal(void)\n{")
    fn_end = text.find("\n#define BUFFER_PARTY_VS_SCREEN_STATUS", fn_start)
    if fn_start < 0 or fn_end < 0:
        raise SystemExit("CB2_InitBattleInternal boundary not found")
    init_fn = text[fn_start:fn_end]
    if "    PmdSoulGoldPrototype_Init();\n" not in init_fn:
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
    if "    PmdSoulGoldPrototype_Tick();\n" not in tick_fn:
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
        print("PATCH src/battle_main.c: G3 init + software-tick lifecycle")


def patch_battle_controllers(path: Path) -> int:
    text = path.read_text(encoding="utf-8")
    original = text

    if PROTOTYPE_INCLUDE not in text:
        anchor = '#include "battle_controllers.h"\n'
        if anchor not in text:
            raise SystemExit("battle_controllers.c include anchor not found")
        text = text.replace(anchor, anchor + PROTOTYPE_INCLUDE, 1)

    old = (
        "    SetMultiuseSpriteTemplateToPokemon(species, GetBattlerPosition(battler));\n\n"
        "    gBattlerSpriteIds[battler] = CreateSprite"
    )
    new = (
        "    SetMultiuseSpriteTemplateToPokemon(species, GetBattlerPosition(battler));\n"
        "    PmdSoulGoldPrototype_PrimeBattlerBody(battler);\n\n"
        "    gBattlerSpriteIds[battler] = CreateSprite"
    )

    already = text.count("PmdSoulGoldPrototype_PrimeBattlerBody(battler);")
    inserted = 0
    if already == 0:
        occurrences = text.count(old)
        if occurrences == 0:
            raise SystemExit("battle_controllers.c Pokemon CreateSprite anchor not found")
        text = text.replace(old, new)
        inserted = occurrences
    else:
        inserted = already

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"PATCH src/battle_controllers.c: PMD HOME prime before {inserted} Pokemon sprite creation path(s)")

    return inserted


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    g3 = framework / "prototype" / "soulgold_g3"
    g2 = framework / "prototype" / "soulgold_g2"

    require_clean_exact_checkout(soulgold)

    copy_file(g2 / "pmd_gba_runtime.c", soulgold / "src" / "pmd_gba_runtime.c")
    copy_file(g2 / "pmd_gba_runtime.h", soulgold / "include" / "pmd_gba_runtime.h")
    copy_file(g3 / "pmd_soulgold_adapter.c", soulgold / "src" / "pmd_soulgold_adapter.c")
    copy_file(g3 / "pmd_soulgold_adapter.h", soulgold / "include" / "pmd_soulgold_adapter.h")
    copy_file(g3 / "pmd_soulgold_prototype.c", soulgold / "src" / "pmd_soulgold_prototype.c")
    copy_file(g3 / "pmd_soulgold_prototype.h", soulgold / "include" / "pmd_soulgold_prototype.h")

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
    prime_paths = patch_battle_controllers(soulgold / "src" / "battle_controllers.c")

    status = git(soulgold, "status", "--short")
    (soulgold / "PMD_G3_INSTALL_STATUS.txt").write_text(
        "SoulGold G3 PMD battle-facing/sendout/shadow candidate installed.\n"
        f"baseline={SOULGOLD_REV}\n"
        "scope=Cyndaquil HOME+Idle+Walk+Nod+Pose+Rotate\n"
        "banned_ambient=LookUp,DeepBreath,Sit (shared single-row/non-directional)\n"
        "direction_policy=45-degree HOME start/end; transitional turn allowed; real directional source required\n"
        "shadow_policy=authentic PMD per-frame Shadow.png / ShadowSize=1 / composited below body / atomic frame sync\n"
        "host_files_modified=src/battle_main.c,src/battle_controllers.c\n"
        f"sendout_prime_paths={prime_paths}\n"
        "sendout_motion_owner=SOULGOLD_NATIVE\n"
        "save_structure=UNCHANGED\n"
        "MAX_MON_PIC_FRAMES=UNCHANGED\n"
        "native sprite->anims=UNCHANGED\n"
        "G1_renderer_contract=SEALED_REUSED\n"
        "compile_status=PENDING\n"
        "runtime_status=PENDING\n\n"
        + status + "\n",
        encoding="utf-8",
    )

    print("G3 candidate prepared. Next gate: full compile + PMD-from-entry + shadow visual test.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
