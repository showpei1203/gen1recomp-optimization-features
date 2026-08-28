#!/usr/bin/env python3
"""Refine G3R8B Sleep with a dedicated persistent-presentation ownership gate.

Ambient PMD presentation is intentionally limited to ordinary battle-choice
windows, while Hurt uses a reactive override that may remain visible during
SoulGold's global battle-animation busy state. Persistent Sleep needs neither
behavior exactly: it must stay eligible across normal turn phases, but still
yield to native busy animations.

G3R8C therefore adds a third adapter gate:
- ambient: ordinary InBattleChoosingMoves ownership
- persistent Sleep: may present outside choosing-moves, but yields when
  gDoingBattleAnim is active
- reactive Hurt: may present through the explicitly-owned native hit animation

Native move x2/y2 spatial ownership remains independent and unchanged.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def patch_adapter(soulgold: Path) -> None:
    header=soulgold/"include"/"pmd_soulgold_adapter.h"
    text=header.read_text(encoding="utf-8")
    anchor="void PmdSoulGold_SetReactivePresentation(u8 battler, bool32 active);\n"
    decl=anchor+"void PmdSoulGold_SetPersistentPresentation(u8 battler, bool32 active);\n"
    if "PmdSoulGold_SetPersistentPresentation" not in text:
        if anchor not in text:
            raise SystemExit("G3R8C adapter persistent declaration anchor missing")
        text=text.replace(anchor,decl,1)
    header.write_text(text,encoding="utf-8")

    source=soulgold/"src"/"pmd_soulgold_adapter.c"
    text=source.read_text(encoding="utf-8")
    state_anchor="static bool8 sPmdReactivePresentation[PMD_GBA_MAX_BATTLERS];\n"
    state_new=state_anchor+"static bool8 sPmdPersistentPresentation[PMD_GBA_MAX_BATTLERS];\n"
    if "sPmdPersistentPresentation" not in text:
        if state_anchor not in text:
            raise SystemExit("G3R8C adapter persistent state anchor missing")
        text=text.replace(state_anchor,state_new,1)

    if "void PmdSoulGold_SetPersistentPresentation" not in text:
        setter_anchor=(
            "void PmdSoulGold_SetReactivePresentation(u8 battler, bool32 active)\n"
            "{\n"
            "    if (battler < PMD_GBA_MAX_BATTLERS)\n"
            "        sPmdReactivePresentation[battler] = active;\n"
            "}\n\n"
        )
        setter_new=setter_anchor+(
            "void PmdSoulGold_SetPersistentPresentation(u8 battler, bool32 active)\n"
            "{\n"
            "    if (battler < PMD_GBA_MAX_BATTLERS)\n"
            "        sPmdPersistentPresentation[battler] = active;\n"
            "}\n\n"
        )
        if setter_anchor not in text:
            raise SystemExit("G3R8C persistent setter insertion anchor missing")
        text=text.replace(setter_anchor,setter_new,1)

    old="    if (!InBattleChoosingMoves() && !sPmdReactivePresentation[battler])\n        return FALSE;\n"
    new="    if (!InBattleChoosingMoves() && !sPmdReactivePresentation[battler] && !sPmdPersistentPresentation[battler])\n        return FALSE;\n"
    if old in text:
        text=text.replace(old,new,1)
    elif new not in text:
        raise SystemExit("G3R8C CanPresent persistent eligibility gate missing")

    # Persistent state deliberately does NOT bypass this native busy gate.
    busy="    if (gDoingBattleAnim && !sPmdReactivePresentation[battler])\n        return FALSE;\n"
    if busy not in text:
        raise SystemExit("G3R8C native busy-yield contract missing")

    init_anchor=(
        "        sPmdReactivePresentation[battler] = FALSE;\n"
        "        sPmdNativeSpatialOwnership[battler] = FALSE;\n"
        "        sActiveShadowProfiles[battler] = NULL;\n"
    )
    init_new=(
        "        sPmdReactivePresentation[battler] = FALSE;\n"
        "        sPmdPersistentPresentation[battler] = FALSE;\n"
        "        sPmdNativeSpatialOwnership[battler] = FALSE;\n"
        "        sActiveShadowProfiles[battler] = NULL;\n"
    )
    if "sPmdPersistentPresentation[battler] = FALSE;" not in text:
        if text.count(init_anchor)!=2:
            raise SystemExit(f"G3R8C expected two adapter init/reset anchors, got {text.count(init_anchor)}")
        text=text.replace(init_anchor,init_new)
    if text.count("sPmdPersistentPresentation[battler] = FALSE;") < 2:
        raise SystemExit("G3R8C persistent gate not initialized/reset")
    source.write_text(text,encoding="utf-8")


def patch_prototype(path: Path) -> None:
    text=path.read_text(encoding="utf-8")

    clear_anchor=(
        "    PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    PmdGbaRuntime_Unbind(battler);\n"
    )
    clear_new=(
        "    PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetPersistentPresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    PmdGbaRuntime_Unbind(battler);\n"
    )
    if clear_new not in text:
        if clear_anchor not in text:
            raise SystemExit("G3R8C ClearState persistent reset anchor missing")
        text=text.replace(clear_anchor,clear_new,1)

    # HOME is the canonical boundary that exits persistent-state ownership.
    home_anchor=(
        "    if (restartSequence)\n"
        "        state->sequenceIndex = 0;\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->home))\n"
    )
    home_new=(
        "    PmdSoulGold_SetPersistentPresentation(battler, FALSE);\n"
        "    if (restartSequence)\n"
        "        state->sequenceIndex = 0;\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->home))\n"
    )
    if home_new not in text:
        if home_anchor not in text:
            raise SystemExit("G3R8C BindHome persistent-release anchor missing")
        text=text.replace(home_anchor,home_new,1)

    hurt_anchor=(
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    PmdSoulGold_SetReactivePresentation(battler, TRUE);\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->hurt))\n"
    )
    hurt_new=(
        "    PmdSoulGold_SetPersistentPresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    PmdSoulGold_SetReactivePresentation(battler, TRUE);\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->hurt))\n"
    )
    if hurt_new not in text:
        if hurt_anchor not in text:
            raise SystemExit("G3R8C BindHurt persistent-release anchor missing")
        text=text.replace(hurt_anchor,hurt_new,1)

    move_anchor=(
        "    PmdSoulGold_SetReactivePresentation(battler, TRUE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, TRUE);\n"
    )
    move_new=(
        "    PmdSoulGold_SetPersistentPresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetReactivePresentation(battler, TRUE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, TRUE);\n"
    )
    if text.count(move_new)==0:
        if text.count(move_anchor)!=3:
            raise SystemExit(f"G3R8C expected Attack/Shoot/MoveReturn ownership anchors=3, got {text.count(move_anchor)}")
        text=text.replace(move_anchor,move_new)
    if text.count("PmdSoulGold_SetPersistentPresentation(battler, FALSE);\n    PmdSoulGold_SetReactivePresentation(battler, TRUE);") != 3:
        raise SystemExit("G3R8C Attack/Shoot/MoveReturn must all release persistent ownership")

    sleep_anchor=(
        "    PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->sleep))\n"
    )
    sleep_new=(
        "    PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetPersistentPresentation(battler, TRUE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->sleep))\n"
    )
    if sleep_new not in text:
        if sleep_anchor not in text:
            raise SystemExit("G3R8C BindSleep persistent-enable anchor missing")
        text=text.replace(sleep_anchor,sleep_new,1)

    path.write_text(text,encoding="utf-8")


def main() -> int:
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold",type=Path,required=True)
    ap.add_argument("--assets-staging",type=Path,required=True)
    ap.add_argument("--framework-root",type=Path,default=Path(__file__).resolve().parents[1])
    args=ap.parse_args()
    soulgold=args.soulgold.resolve(); framework=args.framework_root.resolve()

    run([
        sys.executable,str(framework/"tools"/"install_soulgold_g3r8_sleep_runtime.py"),
        "--soulgold",str(soulgold),"--assets-staging",str(args.assets_staging.resolve()),
        "--framework-root",str(framework),
    ])
    patch_adapter(soulgold)
    patch_prototype(soulgold/"src"/"pmd_soulgold_prototype.c")

    adapter=(soulgold/"src"/"pmd_soulgold_adapter.c").read_text(encoding="utf-8")
    header=(soulgold/"include"/"pmd_soulgold_adapter.h").read_text(encoding="utf-8")
    proto=(soulgold/"src"/"pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    required=(
        (header,"PmdSoulGold_SetPersistentPresentation"),
        (adapter,"sPmdPersistentPresentation"),
        (adapter,"!InBattleChoosingMoves() && !sPmdReactivePresentation[battler] && !sPmdPersistentPresentation[battler]"),
        (adapter,"if (gDoingBattleAnim && !sPmdReactivePresentation[battler])"),
        (proto,"PmdSoulGold_SetPersistentPresentation(battler, TRUE);"),
        (proto,"PMD_PHASE_SLEEP"),
        (proto,"gBattleMons[battler].status1 & STATUS1_SLEEP"),
        (proto,"PmdSoulGoldPrototype_ConsumeMoveMarkers"),
    )
    for haystack,needle in required:
        if needle not in haystack:
            raise SystemExit(f"G3R8C verification missing {needle}")

    (soulgold/"PMD_G3R8C_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R8C persistent Sleep ownership refinement installed.\n"
        "parent=G3R8B_SLEEP_STATUS_RUNTIME_STRUCTURAL\n"
        "persistent_gate=DEDICATED_PMD_PRESENTATION_OWNERSHIP\n"
        "persistent_sleep_allowed_outside_move_choice=TRUE\n"
        "persistent_sleep_yields_to_gDoingBattleAnim=TRUE\n"
        "reactive_hurt_semantics=PRESERVED\n"
        "native_move_spatial_ownership=PRESERVED\n"
        "sleep_view=PMDCOLLAB_DIRECTIONLESS_SOURCE_AUTHORITY\n"
        "status_authority=SOULGOLD_STATUS1_SLEEP\n"
        "priority=MOVE_HURT_OVER_SLEEP_OVER_AMBIENT\n"
        "wake_transition=HOME_THEN_AMBIENT_RESTART\n"
        "combat_status_logic=UNCHANGED_SOULGOLD_NATIVE\n"
        "combat_damage_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "known_ambient_1px_defect=DEFERRED_ROOT_CAUSE_UNRESOLVED\n"
        "runtime_visual_status=PENDING_USER_DEFERRED_TESTING\n",
        encoding="utf-8",
    )
    print("G3R8C installed: persistent Sleep survives normal turn phases but yields to native busy animations.")
    return 0

if __name__=="__main__":
    raise SystemExit(main())
