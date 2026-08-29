#!/usr/bin/env python3
"""Install the SoulGold Showdown S1C natural first-battle candidate.

S1C removes the temporary overworld B-button harness. The normal starter flow is
used instead: the left starter option is Sprigatito, and CB2_GiveStarter replaces
the pending first-battle enemy with a level-5 Marill immediately before the
existing BATTLE_TYPE_FIRST_BATTLE path begins.
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
INCLUDE_LINE = '#include "showdown_soulgold_prototype.h"\n'


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


def ensure_include(text: str, anchor: str) -> str:
    if INCLUDE_LINE in text:
        return text
    if anchor not in text:
        raise SystemExit(f"include anchor not found: {anchor.strip()}")
    return text.replace(anchor, anchor + INCLUDE_LINE, 1)


def patch_battle_main(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text
    text = ensure_include(text, '#include "battle_main.h"\n')

    fn_start = text.find("static void CB2_InitBattleInternal(void)\n{")
    fn_end = text.find("\n#define BUFFER_PARTY_VS_SCREEN_STATUS", fn_start)
    if fn_start < 0 or fn_end < 0:
        raise SystemExit("CB2_InitBattleInternal boundary not found")
    init_fn = text[fn_start:fn_end]
    init_call = "    ShowdownSoulGoldPrototype_Init();\n"
    if init_call not in init_fn:
        tail = "    gBattleCommunication[MULTIUSE_STATE] = 0;\n}"
        if tail not in init_fn:
            raise SystemExit("CB2_InitBattleInternal tail anchor not found")
        init_fn = init_fn.replace(
            tail,
            "    gBattleCommunication[MULTIUSE_STATE] = 0;\n"
            "    ShowdownSoulGoldPrototype_Init();\n}"
        )
        text = text[:fn_start] + init_fn + text[fn_end:]

    tick_start = text.find("static void RunBattleSoftwareTick(void)\n{")
    tick_end = text.find("\nstatic void AdvanceBattleFrameRng(void)", tick_start)
    if tick_start < 0 or tick_end < 0:
        raise SystemExit("RunBattleSoftwareTick boundary not found")
    tick_fn = text[tick_start:tick_end]
    tick_call = "    ShowdownSoulGoldPrototype_Tick();\n"
    if tick_call not in tick_fn:
        tail = "    RunTasks();\n}"
        if tail not in tick_fn:
            raise SystemExit("RunBattleSoftwareTick tail anchor not found")
        tick_fn = tick_fn.replace(
            tail,
            "    RunTasks();\n"
            "    ShowdownSoulGoldPrototype_Tick();\n}"
        )
        text = text[:tick_start] + tick_fn + text[tick_end:]

    if text == original:
        print("battle_main.c already contains Showdown S1 hooks")
        return
    path.write_text(text, encoding="utf-8")
    print("PATCH src/battle_main.c: Showdown include + init + software-tick hook")


def patch_starter_choose(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text
    old = (
        "static const u16 sStarterMon[STARTER_MON_COUNT] =\n"
        "{\n"
        "    SPECIES_TREECKO,\n"
        "    SPECIES_TORCHIC,\n"
        "    SPECIES_MUDKIP,\n"
        "};"
    )
    new = (
        "static const u16 sStarterMon[STARTER_MON_COUNT] =\n"
        "{\n"
        "    SPECIES_SPRIGATITO, // SHOWDOWN_S1C_TEST_STARTER\n"
        "    SPECIES_TORCHIC,\n"
        "    SPECIES_MUDKIP,\n"
        "};"
    )
    if "SHOWDOWN_S1C_TEST_STARTER" not in text:
        if old not in text:
            raise SystemExit("starter roster anchor not found")
        text = text.replace(old, new, 1)

    if text == original:
        print("starter_choose.c already contains S1C Sprigatito starter")
        return
    path.write_text(text, encoding="utf-8")
    print("PATCH src/starter_choose.c: left starter -> Sprigatito")


def patch_first_battle(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text
    old = (
        "    starterMon = GetStarterPokemon(gSpecialVar_Result);\n"
        "    ScriptGiveMon(starterMon, 5, ITEM_NONE, ITEM_NONE);\n"
        "    Achievement_Unlock(ACH_RECEIVE_STARTER);"
    )
    new = (
        "    starterMon = GetStarterPokemon(gSpecialVar_Result);\n"
        "    ScriptGiveMon(starterMon, 5, ITEM_NONE, ITEM_NONE);\n"
        "\n"
        "    // SHOWDOWN_S1C_FIRST_BATTLE_MARILL: deterministic visual proof only.\n"
        "    ZeroEnemyPartyMons();\n"
        "    CreateRandomMon(&gEnemyParty[0], SPECIES_MARILL, 5);\n"
        "    gEnemyPartyCount = 1;\n"
        "\n"
        "    Achievement_Unlock(ACH_RECEIVE_STARTER);"
    )
    if "SHOWDOWN_S1C_FIRST_BATTLE_MARILL" not in text:
        if old not in text:
            raise SystemExit("CB2_GiveStarter anchor not found")
        text = text.replace(old, new, 1)

    if text == original:
        print("battle_setup.c already contains S1C Marill first-battle override")
        return
    path.write_text(text, encoding="utf-8")
    print("PATCH src/battle_setup.c: normal first battle enemy -> Lv5 Marill")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    proto = framework / "prototype" / "soulgold_showdown_s1"

    require_clean_exact_checkout(soulgold)

    for name in ("showdown_gba_runtime.c", "showdown_soulgold_adapter.c", "showdown_soulgold_prototype.c"):
        copy_file(proto / name, soulgold / "src" / name)
    for name in ("showdown_gba_runtime.h", "showdown_soulgold_adapter.h", "showdown_soulgold_prototype.h"):
        copy_file(proto / name, soulgold / "include" / name)

    for name in ("showdown_sprigatito_back_idle.c", "showdown_marill_front_idle.c"):
        copy_file(staging / "src" / name, soulgold / "src" / name)

    for species in ("sprigatito", "marill"):
        src_graphics = staging / "graphics" / "showdown" / species
        dst_graphics = soulgold / "graphics" / "showdown" / species
        if not src_graphics.is_dir():
            raise SystemExit(f"Missing staged graphics: {src_graphics}")
        if dst_graphics.exists():
            shutil.rmtree(dst_graphics)
        dst_graphics.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_graphics, dst_graphics)
        print(f"COPY {src_graphics} -> {dst_graphics}")

    patch_battle_main(soulgold / "src" / "battle_main.c")
    patch_starter_choose(soulgold / "src" / "starter_choose.c")
    patch_first_battle(soulgold / "src" / "battle_setup.c")

    status = git(soulgold, "status", "--short")
    (soulgold / "SHOWDOWN_S1_INSTALL_STATUS.txt").write_text(
        "SoulGold Showdown S1C natural first-battle candidate installed.\n"
        f"baseline={SOULGOLD_REV}\n"
        "player_target=Sprigatito back Showdown idle\n"
        "opponent_target=Marill front Showdown idle\n"
        "starter_flow=normal starter chooser; left option replaced with Sprigatito\n"
        "first_battle_flow=normal CB2_GiveStarter -> CB2_StartFirstBattle path\n"
        "first_battle_enemy=Lv5 Marill\n"
        "ownership=move-selection-only\n"
        "palette=per-species existing SoulGold normal palette\n"
        "b_button_harness=REMOVED\n"
        "overworld_patch=NONE\n"
        "host_files_modified=src/battle_main.c,src/starter_choose.c,src/battle_setup.c\n"
        "PMD_RUNTIME_DEPENDENCY=NONE\n"
        "compile_status=PENDING\n"
        "runtime_status=PENDING\n\n"
        + status + "\n",
        encoding="utf-8",
    )

    print("Showdown S1C install candidate prepared. Next gate: compile/link, then normal new-game starter/first-battle runtime evidence.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
