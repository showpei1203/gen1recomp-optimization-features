#!/usr/bin/env python3
"""Install SoulGold G3R6B PMDCollab Attack body ownership over native move FX.

G3R6B inherits the compiled G3R6A Hurt path, the G3R5C frame-synchronous PMD
shadow system, and the G3R4B OAM ordering. It adds PMDCollab Attack as a body
presentation layer while SoulGold remains authoritative for the move script,
move FX, combat timing, affine effects, and x2/y2 spatial motion.

The native Controller_DoMoveAnimation lifecycle becomes:
  state 1: PMD BeginMoveAction -> native DoMoveAnim
  state 2: native script runs unchanged; when it ends -> PMD EndMoveAction
  state 3: native substitute/special animation finishes, then controller waits
           until PMD HOME is visibly restored before BtlController_Complete.

No Rush/Hit/Return marker is used as damage authority in this gate. The markers
are preserved in generated source for the next synchronization phase.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise SystemExit(f"Missing required source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"COPY {src} -> {dst}")


def patch_adapter_native_spatial_ownership(soulgold: Path) -> None:
    header = soulgold / "include" / "pmd_soulgold_adapter.h"
    text = header.read_text(encoding="utf-8")
    reactive_decl = "void PmdSoulGold_SetReactivePresentation(u8 battler, bool32 active);\n"
    spatial_decl = reactive_decl + "void PmdSoulGold_SetNativeSpatialOwnership(u8 battler, bool32 active);\n"
    if "PmdSoulGold_SetNativeSpatialOwnership" not in text:
        if reactive_decl not in text:
            raise SystemExit("G3R6B adapter header reactive declaration anchor not found")
        text = text.replace(reactive_decl, spatial_decl, 1)
        header.write_text(text, encoding="utf-8")

    source = soulgold / "src" / "pmd_soulgold_adapter.c"
    text = source.read_text(encoding="utf-8")

    reactive_state = "static bool8 sPmdReactivePresentation[PMD_GBA_MAX_BATTLERS];\n"
    spatial_state = reactive_state + "static bool8 sPmdNativeSpatialOwnership[PMD_GBA_MAX_BATTLERS];\n"
    if "sPmdNativeSpatialOwnership" not in text:
        if reactive_state not in text:
            raise SystemExit("G3R6B adapter reactive state anchor not found")
        text = text.replace(reactive_state, spatial_state, 1)

    if "void PmdSoulGold_SetNativeSpatialOwnership" not in text:
        reactive_setter = (
            "void PmdSoulGold_SetReactivePresentation(u8 battler, bool32 active)\n"
            "{\n"
            "    if (battler < PMD_GBA_MAX_BATTLERS)\n"
            "        sPmdReactivePresentation[battler] = active;\n"
            "}\n\n"
        )
        spatial_setter = reactive_setter + (
            "void PmdSoulGold_SetNativeSpatialOwnership(u8 battler, bool32 active)\n"
            "{\n"
            "    if (battler < PMD_GBA_MAX_BATTLERS)\n"
            "        sPmdNativeSpatialOwnership[battler] = active;\n"
            "}\n\n"
        )
        if reactive_setter not in text:
            raise SystemExit("G3R6B adapter reactive setter anchor not found")
        text = text.replace(reactive_setter, spatial_setter, 1)

    old_offset = (
        "static void SoulGold_SetPresentationOffset(u8 battler, s16 x, s16 y)\n"
        "{\n"
        "    u8 spriteId = gBattlerSpriteIds[battler];\n\n"
        "    if (spriteId >= MAX_SPRITES)\n"
        "        return;\n"
        "    gSprites[spriteId].x2 = x;\n"
        "    gSprites[spriteId].y2 = y;\n"
        "}\n"
    )
    new_offset = (
        "static void SoulGold_SetPresentationOffset(u8 battler, s16 x, s16 y)\n"
        "{\n"
        "    u8 spriteId;\n\n"
        "    /* G3R6B body-only move ownership: native move animation callbacks\n"
        "     * own x2/y2. PMD may change body pixels, but must not erase native\n"
        "     * lunges, hops, recoil, shakes, or other spatial choreography. */\n"
        "    if (battler >= PMD_GBA_MAX_BATTLERS || sPmdNativeSpatialOwnership[battler])\n"
        "        return;\n"
        "    spriteId = gBattlerSpriteIds[battler];\n"
        "    if (spriteId >= MAX_SPRITES)\n"
        "        return;\n"
        "    gSprites[spriteId].x2 = x;\n"
        "    gSprites[spriteId].y2 = y;\n"
        "}\n"
    )
    if old_offset in text:
        text = text.replace(old_offset, new_offset, 1)
    elif new_offset not in text:
        raise SystemExit("G3R6B adapter presentation-offset function anchor not found")

    init_old = (
        "        sNativeShadowSuppressed[battler] = FALSE;\n"
        "        sPmdReactivePresentation[battler] = FALSE;\n"
        "        sActiveShadowProfiles[battler] = NULL;\n"
    )
    init_new = (
        "        sNativeShadowSuppressed[battler] = FALSE;\n"
        "        sPmdReactivePresentation[battler] = FALSE;\n"
        "        sPmdNativeSpatialOwnership[battler] = FALSE;\n"
        "        sActiveShadowProfiles[battler] = NULL;\n"
    )
    if "sPmdNativeSpatialOwnership[battler] = FALSE;" not in text:
        if text.count(init_old) != 2:
            raise SystemExit(f"G3R6B expected two adapter init/reset state anchors, got {text.count(init_old)}")
        text = text.replace(init_old, init_new)
    elif text.count("sPmdNativeSpatialOwnership[battler] = FALSE;") < 2:
        raise SystemExit("G3R6B native spatial state is not initialized and reset")

    source.write_text(text, encoding="utf-8")


def patch_move_controller(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    start = text.find("static void Controller_DoMoveAnimation(enum BattlerId battler)\n{")
    if start < 0:
        raise SystemExit("G3R6B Controller_DoMoveAnimation start not found")
    end = text.find("\nvoid BtlController_HandleMoveAnimation(enum BattlerId battler)", start)
    if end < 0:
        raise SystemExit("G3R6B Controller_DoMoveAnimation end boundary not found")
    fn = text[start:end]

    begin_hook = "            PmdSoulGoldPrototype_BeginMoveAction(battler);\n"
    if begin_hook not in fn:
        anchor = (
            "            SetBattlerSpriteAffineMode(ST_OAM_AFFINE_OFF);\n"
            "            DoMoveAnim(move);\n"
        )
        replacement = (
            "            SetBattlerSpriteAffineMode(ST_OAM_AFFINE_OFF);\n"
            "            PmdSoulGoldPrototype_BeginMoveAction(battler);\n"
            "            DoMoveAnim(move);\n"
        )
        if fn.count(anchor) != 1:
            raise SystemExit(f"G3R6B move begin anchor count={fn.count(anchor)}")
        fn = fn.replace(anchor, replacement, 1)

    end_hook = "            PmdSoulGoldPrototype_EndMoveAction(battler);\n"
    if end_hook not in fn:
        anchor = (
            "            u8 multihit = gBattleResources->bufferA[battler][11];\n\n"
            "            SetBattlerSpriteAffineMode(ST_OAM_AFFINE_NORMAL);\n"
        )
        replacement = (
            "            u8 multihit = gBattleResources->bufferA[battler][11];\n\n"
            "            PmdSoulGoldPrototype_EndMoveAction(battler);\n"
            "            SetBattlerSpriteAffineMode(ST_OAM_AFFINE_NORMAL);\n"
        )
        if fn.count(anchor) != 1:
            raise SystemExit(f"G3R6B move end anchor count={fn.count(anchor)}")
        fn = fn.replace(anchor, replacement, 1)

    ready_hook = (
        "            if (!PmdSoulGoldPrototype_IsMoveReturnReady(battler))\n"
        "                break;\n"
    )
    if ready_hook not in fn:
        anchor = (
            "        if (!gBattleSpritesDataPtr->healthBoxesData[battler].specialAnimActive)\n"
            "        {\n"
            "            CopyAllBattleSpritesInvisibilities();\n"
        )
        replacement = (
            "        if (!gBattleSpritesDataPtr->healthBoxesData[battler].specialAnimActive)\n"
            "        {\n"
            "            if (!PmdSoulGoldPrototype_IsMoveReturnReady(battler))\n"
            "                break;\n"
            "            CopyAllBattleSpritesInvisibilities();\n"
        )
        if fn.count(anchor) != 1:
            raise SystemExit(f"G3R6B move return gate anchor count={fn.count(anchor)}")
        fn = fn.replace(anchor, replacement, 1)

    if fn.count("PmdSoulGoldPrototype_BeginMoveAction(battler);") != 1:
        raise SystemExit("G3R6B move begin hook must occur exactly once")
    if fn.count("PmdSoulGoldPrototype_EndMoveAction(battler);") != 1:
        raise SystemExit("G3R6B move end hook must occur exactly once")
    if fn.count("PmdSoulGoldPrototype_IsMoveReturnReady(battler)") != 1:
        raise SystemExit("G3R6B move return-ready gate must occur exactly once")

    text = text[:start] + fn + text[end:]
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    g3r6b = framework / "prototype" / "soulgold_g3r6b"

    # Build on the already compiled G3R6A ownership path. G3R6B staging contains
    # the complete G3R6A ambient/Hurt data plus the new Attack body/shadow data.
    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r6a.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    # G3R6A installer copies only ambient and shadow C sources. Add Attack C.
    for slug, variant in (("cyndaquil", "player"), ("marill", "opponent")):
        copy_file(
            staging / "src" / f"pmd_{slug}_{variant}_attack.c",
            soulgold / "src" / f"pmd_{slug}_{variant}_attack.c",
        )

    patch_adapter_native_spatial_ownership(soulgold)
    copy_file(g3r6b / "pmd_soulgold_prototype.h", soulgold / "include" / "pmd_soulgold_prototype.h")
    copy_file(g3r6b / "pmd_soulgold_prototype.c", soulgold / "src" / "pmd_soulgold_prototype.c")
    patch_move_controller(soulgold / "src" / "battle_controllers.c")

    cy_attack = (soulgold / "src" / "pmd_cyndaquil_player_attack.c").read_text(encoding="utf-8")
    ma_attack = (soulgold / "src" / "pmd_marill_opponent_attack.c").read_text(encoding="utf-8")
    cy_shadow = (soulgold / "src" / "pmd_cyndaquil_player_shadow.c").read_text(encoding="utf-8")
    ma_shadow = (soulgold / "src" / "pmd_marill_opponent_shadow.c").read_text(encoding="utf-8")
    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    adapter = (soulgold / "src" / "pmd_soulgold_adapter.c").read_text(encoding="utf-8")
    controllers = (soulgold / "src" / "battle_controllers.c").read_text(encoding="utf-8")

    required = (
        (cy_attack, "gPmdCyndaquilPlayerAttackAction"),
        (ma_attack, "gPmdMarillOpponentAttackAction"),
        (cy_attack, "gPmdCyndaquilPlayerAttackRushFrame"),
        (cy_attack, "gPmdCyndaquilPlayerAttackHitFrame"),
        (cy_attack, "gPmdCyndaquilPlayerAttackReturnFrame"),
        (cy_shadow, "gPmdCyndaquilPlayerAttackShadowAction"),
        (ma_shadow, "gPmdMarillOpponentAttackShadowAction"),
        (proto, "PmdSoulGoldPrototype_BeginMoveAction"),
        (proto, "PmdSoulGoldPrototype_EndMoveAction"),
        (proto, "PmdSoulGoldPrototype_IsMoveReturnReady"),
        (adapter, "sPmdNativeSpatialOwnership"),
        (controllers, "PmdSoulGoldPrototype_BeginMoveAction(battler);"),
        (controllers, "PmdSoulGoldPrototype_EndMoveAction(battler);"),
        (controllers, "PmdSoulGoldPrototype_IsMoveReturnReady(battler)"),
    )
    for haystack, needle in required:
        if needle not in haystack:
            raise SystemExit(f"G3R6B install verification missing {needle}")

    if "if (battler >= PMD_GBA_MAX_BATTLERS || sPmdNativeSpatialOwnership[battler])" not in adapter:
        raise SystemExit("G3R6B adapter can still overwrite native x2/y2")

    (soulgold / "PMD_G3R6B_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R6B native-move Attack body candidate installed.\n"
        "parent=G3R6A_HURT_BUILD_PASS_RUNTIME_PENDING\n"
        "g3r4b_oam_timing=PRESERVED\n"
        "g3r5c_dynamic_shadow=PRESERVED\n"
        "g3r6a_hurt=PRESERVED\n"
        "ambient_known_defect=CYNDAQUIL_SINGLE_1PX_SINK_ROOT_CAUSE_UNRESOLVED_DEFERRED_BY_USER\n"
        "new_action=ATTACK\n"
        "attack_body=PMDCOLLAB_ATTACK_VISIBLE_PIXELS_100_PERCENT_CONSERVED_IN_64X64\n"
        "attack_shadow=FRAME_SYNCHRONOUS_AUTHENTIC_PMDCOLLAB\n"
        "attack_canvas_overflow=TRANSPARENT_ONLY\n"
        "move_fx_owner=SOULGOLD_NATIVE_DOMOVEANIM\n"
        "move_spatial_owner=SOULGOLD_NATIVE_X2Y2\n"
        "pmd_spatial_write_during_move=DISABLED\n"
        "controller_begin=BEFORE_DOMOVEANIM\n"
        "controller_end=AFTER_GANIMSCRIPTACTIVE_FALSE\n"
        "controller_release=AFTER_SPECIAL_ANIM_INACTIVE_AND_PMD_HOME_PRESENT\n"
        "attack_markers=PRESERVED_NOT_YET_USED_AS_DAMAGE_AUTHORITY\n"
        "non_pmd_move_animation=UNCHANGED\n"
        "runtime_status=PENDING_USER_ACCEPTANCE\n",
        encoding="utf-8",
    )
    print("G3R6B installed. Gate: native move FX + PMD Attack body/shadow + clean HOME return.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
