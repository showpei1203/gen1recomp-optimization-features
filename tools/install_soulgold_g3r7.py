#!/usr/bin/env python3
"""Install G3R7 PMD Attack/Shoot semantic move-body selection.

Selector policy for the first source-grounded move-action split:
- status moves: no PMD move-body action; SoulGold native animation remains alone
- damaging contact moves: PMDCollab Attack
- damaging non-contact moves: PMDCollab Shoot

This is intentionally presentation-only. SoulGold remains authoritative for
move scripts, effects, damage, targets, and x2/y2 spatial choreography.
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


def patch_header(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = "void PmdSoulGoldPrototype_BeginMoveAction(enum BattlerId battler);\n"
    new = "void PmdSoulGoldPrototype_BeginMoveAction(enum BattlerId battler, enum Move move);\n"
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit("G3R7 prototype header BeginMoveAction anchor not found")
    path.write_text(text, encoding="utf-8")


def patch_prototype(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    include_anchor = '#include "battle_util.h"\n'
    if '#include "move.h"\n' not in text:
        if include_anchor not in text:
            raise SystemExit("G3R7 move.h include anchor not found")
        text = text.replace(include_anchor, include_anchor + '#include "move.h"\n', 1)

    cy_attack = "extern const struct PmdGbaAction gPmdCyndaquilPlayerAttackAction;\n"
    cy_shoot = cy_attack + "extern const struct PmdGbaAction gPmdCyndaquilPlayerShootAction;\n"
    if "gPmdCyndaquilPlayerShootAction" not in text:
        if cy_attack not in text:
            raise SystemExit("G3R7 Cyndaquil Attack extern anchor not found")
        text = text.replace(cy_attack, cy_shoot, 1)

    cy_shadow_attack = "extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerAttackShadowAction;\n"
    cy_shadow_shoot = cy_shadow_attack + "extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerShootShadowAction;\n"
    if "gPmdCyndaquilPlayerShootShadowAction" not in text:
        if cy_shadow_attack not in text:
            raise SystemExit("G3R7 Cyndaquil Attack shadow extern anchor not found")
        text = text.replace(cy_shadow_attack, cy_shadow_shoot, 1)

    ma_attack = "extern const struct PmdGbaAction gPmdMarillOpponentAttackAction;\n"
    ma_shoot = ma_attack + "extern const struct PmdGbaAction gPmdMarillOpponentShootAction;\n"
    if "gPmdMarillOpponentShootAction" not in text:
        if ma_attack not in text:
            raise SystemExit("G3R7 Marill Attack extern anchor not found")
        text = text.replace(ma_attack, ma_shoot, 1)

    ma_shadow_attack = "extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentAttackShadowAction;\n"
    ma_shadow_shoot = ma_shadow_attack + "extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentShootShadowAction;\n"
    if "gPmdMarillOpponentShootShadowAction" not in text:
        if ma_shadow_attack not in text:
            raise SystemExit("G3R7 Marill Attack shadow extern anchor not found")
        text = text.replace(ma_shadow_attack, ma_shadow_shoot, 1)

    enum_old = (
        "    PMD_PHASE_HURT_RETURN,\n"
        "    PMD_PHASE_MOVE_ATTACK,\n"
        "    PMD_PHASE_MOVE_RETURN,\n"
    )
    enum_new = (
        "    PMD_PHASE_HURT_RETURN,\n"
        "    PMD_PHASE_MOVE_ATTACK,\n"
        "    PMD_PHASE_MOVE_SHOOT,\n"
        "    PMD_PHASE_MOVE_RETURN,\n"
    )
    if "PMD_PHASE_MOVE_SHOOT" not in text:
        if enum_old not in text:
            raise SystemExit("G3R7 presentation phase enum anchor not found")
        text = text.replace(enum_old, enum_new, 1)

    struct_old = (
        "    const struct PmdGbaAction *hurt;\n"
        "    const struct PmdGbaAction *attack;\n"
        "    const struct PmdSoulGoldShadowAction *shadowHome;\n"
    )
    struct_new = (
        "    const struct PmdGbaAction *hurt;\n"
        "    const struct PmdGbaAction *attack;\n"
        "    const struct PmdGbaAction *shoot;\n"
        "    const struct PmdSoulGoldShadowAction *shadowHome;\n"
    )
    if "const struct PmdGbaAction *shoot;" not in text:
        if struct_old not in text:
            raise SystemExit("G3R7 profile body struct anchor not found")
        text = text.replace(struct_old, struct_new, 1)

    shadow_struct_old = (
        "    const struct PmdSoulGoldShadowAction *shadowHurt;\n"
        "    const struct PmdSoulGoldShadowAction *shadowAttack;\n"
        "    u16 homeHolds[PMD_G3R6B_AMBIENT_COUNT];\n"
    )
    shadow_struct_new = (
        "    const struct PmdSoulGoldShadowAction *shadowHurt;\n"
        "    const struct PmdSoulGoldShadowAction *shadowAttack;\n"
        "    const struct PmdSoulGoldShadowAction *shadowShoot;\n"
        "    u16 homeHolds[PMD_G3R6B_AMBIENT_COUNT];\n"
    )
    if "const struct PmdSoulGoldShadowAction *shadowShoot;" not in text:
        if shadow_struct_old not in text:
            raise SystemExit("G3R7 profile shadow struct anchor not found")
        text = text.replace(shadow_struct_old, shadow_struct_new, 1)

    for attack_sym, shoot_sym in (
        ("        .attack = &gPmdCyndaquilPlayerAttackAction,\n", "        .attack = &gPmdCyndaquilPlayerAttackAction,\n        .shoot = &gPmdCyndaquilPlayerShootAction,\n"),
        ("        .attack = &gPmdMarillOpponentAttackAction,\n", "        .attack = &gPmdMarillOpponentAttackAction,\n        .shoot = &gPmdMarillOpponentShootAction,\n"),
        ("        .shadowAttack = &gPmdCyndaquilPlayerAttackShadowAction,\n", "        .shadowAttack = &gPmdCyndaquilPlayerAttackShadowAction,\n        .shadowShoot = &gPmdCyndaquilPlayerShootShadowAction,\n"),
        ("        .shadowAttack = &gPmdMarillOpponentAttackShadowAction,\n", "        .shadowAttack = &gPmdMarillOpponentAttackShadowAction,\n        .shadowShoot = &gPmdMarillOpponentShootShadowAction,\n"),
    ):
        if shoot_sym not in text:
            if attack_sym not in text:
                raise SystemExit(f"G3R7 profile assignment anchor not found: {attack_sym.strip()}")
            text = text.replace(attack_sym, shoot_sym, 1)

    old_is_move = (
        "    return state != NULL && (state->phase == PMD_PHASE_MOVE_ATTACK || state->phase == PMD_PHASE_MOVE_RETURN);\n"
    )
    new_is_move = (
        "    return state != NULL && (state->phase == PMD_PHASE_MOVE_ATTACK || state->phase == PMD_PHASE_MOVE_SHOOT || state->phase == PMD_PHASE_MOVE_RETURN);\n"
    )
    if old_is_move in text:
        text = text.replace(old_is_move, new_is_move, 1)
    elif new_is_move not in text:
        raise SystemExit("G3R7 IsMovePhase anchor not found")

    bind_attack_end = (
        "    state->phase = PMD_PHASE_MOVE_ATTACK;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static const struct PmdGbaFrame *GetHomeFrame"
    )
    bind_shoot = (
        "    state->phase = PMD_PHASE_MOVE_ATTACK;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static bool32 BindMoveShoot(u8 battler, const struct PmdSpeciesProfile *profile)\n"
        "{\n"
        "    struct PmdPresentationState *state = &sState[battler];\n\n"
        "    if (profile == NULL || profile->shoot == NULL)\n"
        "        return FALSE;\n"
        "    PmdSoulGold_SetReactivePresentation(battler, TRUE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, TRUE);\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->shoot))\n"
        "    {\n"
        "        PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "        PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "        return FALSE;\n"
        "    }\n"
        "    state->profile = profile;\n"
        "    state->initialized = TRUE;\n"
        "    state->moveInterrupted = FALSE;\n"
        "    state->spriteId = gBattlerSpriteIds[battler];\n"
        "    state->phase = PMD_PHASE_MOVE_SHOOT;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static const struct PmdGbaFrame *GetHomeFrame"
    )
    if "static bool32 BindMoveShoot" not in text:
        if bind_attack_end not in text:
            raise SystemExit("G3R7 BindMoveShoot insertion anchor not found")
        text = text.replace(bind_attack_end, bind_shoot, 1)

    shadow_old = (
        "    if (state->phase == PMD_PHASE_MOVE_ATTACK)\n"
        "        return state->profile->shadowAttack;\n"
    )
    shadow_new = (
        "    if (state->phase == PMD_PHASE_MOVE_ATTACK)\n"
        "        return state->profile->shadowAttack;\n"
        "    if (state->phase == PMD_PHASE_MOVE_SHOOT)\n"
        "        return state->profile->shadowShoot;\n"
    )
    if "return state->profile->shadowShoot;" not in text:
        if shadow_old not in text:
            raise SystemExit("G3R7 current shadow action anchor not found")
        text = text.replace(shadow_old, shadow_new, 1)

    begin_start = text.find("void PmdSoulGoldPrototype_BeginMoveAction(enum BattlerId battler)\n{")
    if begin_start >= 0:
        begin_end = text.find("\nvoid PmdSoulGoldPrototype_EndMoveAction", begin_start)
        if begin_end < 0:
            raise SystemExit("G3R7 BeginMoveAction end boundary not found")
        new_begin = (
            "void PmdSoulGoldPrototype_BeginMoveAction(enum BattlerId battler, enum Move move)\n"
            "{\n"
            "    const struct PmdSpeciesProfile *profile;\n"
            "    u8 spriteId;\n\n"
            "    if (battler >= PMD_GBA_MAX_BATTLERS)\n"
            "        return;\n"
            "    profile = FindProfile(battler);\n"
            "    spriteId = battler < gBattlersCount ? gBattlerSpriteIds[battler] : SPRITE_NONE;\n"
            "    if (profile == NULL || spriteId >= MAX_SPRITES || !gSprites[spriteId].inUse || gSprites[spriteId].invisible)\n"
            "        return;\n\n"
            "    /* Source-grounded semantic split. Status moves do not invent a\n"
            "     * PMD body gesture. Damaging contact moves use Attack; damaging\n"
            "     * non-contact moves use Shoot. Combat behavior remains native. */\n"
            "    if (GetMoveCategory(move) == DAMAGE_CATEGORY_STATUS)\n"
            "        return;\n"
            "    if (MoveMakesContact(move))\n"
            "        BindMoveAttack(battler, profile);\n"
            "    else\n"
            "        BindMoveShoot(battler, profile);\n"
            "}\n"
        )
        text = text[:begin_start] + new_begin + text[begin_end:]
    elif "void PmdSoulGoldPrototype_BeginMoveAction(enum BattlerId battler, enum Move move)" not in text:
        raise SystemExit("G3R7 BeginMoveAction signature not found")

    old_end_check = (
        "    if (profile == NULL || state->profile != profile || state->phase != PMD_PHASE_MOVE_ATTACK)\n"
        "        return;\n"
    )
    new_end_check = (
        "    if (profile == NULL || state->profile != profile\n"
        "     || (state->phase != PMD_PHASE_MOVE_ATTACK && state->phase != PMD_PHASE_MOVE_SHOOT))\n"
        "        return;\n"
    )
    if old_end_check in text:
        text = text.replace(old_end_check, new_end_check, 1)
    elif new_end_check not in text:
        raise SystemExit("G3R7 EndMoveAction phase check anchor not found")

    old_return = "    if (state->phase != PMD_PHASE_MOVE_RETURN)\n        return state->phase != PMD_PHASE_MOVE_ATTACK;\n"
    new_return = "    if (state->phase != PMD_PHASE_MOVE_RETURN)\n        return !IsMovePhase(state);\n"
    if old_return in text:
        text = text.replace(old_return, new_return, 1)
    elif new_return not in text:
        raise SystemExit("G3R7 return-ready phase anchor not found")

    old_interrupt = "            if (state->phase == PMD_PHASE_MOVE_ATTACK)\n"
    new_interrupt = "            if (state->phase == PMD_PHASE_MOVE_ATTACK || state->phase == PMD_PHASE_MOVE_SHOOT)\n"
    if old_interrupt in text:
        text = text.replace(old_interrupt, new_interrupt, 1)
    elif new_interrupt not in text:
        raise SystemExit("G3R7 move interruption phase anchor not found")

    path.write_text(text, encoding="utf-8")


def patch_controller(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = "PmdSoulGoldPrototype_BeginMoveAction(battler);"
    new = "PmdSoulGoldPrototype_BeginMoveAction(battler, move);"
    if old in text:
        if text.count(old) != 1:
            raise SystemExit(f"G3R7 expected one BeginMoveAction controller hook, got {text.count(old)}")
        text = text.replace(old, new, 1)
    elif text.count(new) != 1:
        raise SystemExit("G3R7 move controller BeginMoveAction(move) hook missing")
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

    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r6b.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    for slug, variant in (("cyndaquil", "player"), ("marill", "opponent")):
        copy_file(
            staging / "src" / f"pmd_{slug}_{variant}_shoot.c",
            soulgold / "src" / f"pmd_{slug}_{variant}_shoot.c",
        )

    patch_header(soulgold / "include" / "pmd_soulgold_prototype.h")
    patch_prototype(soulgold / "src" / "pmd_soulgold_prototype.c")
    patch_controller(soulgold / "src" / "battle_controllers.c")

    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    controller = (soulgold / "src" / "battle_controllers.c").read_text(encoding="utf-8")
    cy_shoot = (soulgold / "src" / "pmd_cyndaquil_player_shoot.c").read_text(encoding="utf-8")
    ma_shoot = (soulgold / "src" / "pmd_marill_opponent_shoot.c").read_text(encoding="utf-8")
    cy_shadow = (soulgold / "src" / "pmd_cyndaquil_player_shadow.c").read_text(encoding="utf-8")
    ma_shadow = (soulgold / "src" / "pmd_marill_opponent_shadow.c").read_text(encoding="utf-8")

    required = (
        (proto, "PMD_PHASE_MOVE_SHOOT"),
        (proto, "BindMoveShoot"),
        (proto, "GetMoveCategory(move) == DAMAGE_CATEGORY_STATUS"),
        (proto, "MoveMakesContact(move)"),
        (proto, "profile->shadowShoot"),
        (controller, "PmdSoulGoldPrototype_BeginMoveAction(battler, move);"),
        (cy_shoot, "gPmdCyndaquilPlayerShootAction"),
        (ma_shoot, "gPmdMarillOpponentShootAction"),
        (cy_shadow, "gPmdCyndaquilPlayerShootShadowAction"),
        (ma_shadow, "gPmdMarillOpponentShootShadowAction"),
    )
    for haystack, needle in required:
        if needle not in haystack:
            raise SystemExit(f"G3R7 install verification missing {needle}")

    (soulgold / "PMD_G3R7_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R7 Attack/Shoot semantic selector installed.\n"
        "parent=G3R6B_BUILD_PASS_RUNTIME_PENDING\n"
        "g3r6a_hurt=PRESERVED\n"
        "g3r6b_attack=PRESERVED\n"
        "new_action=SHOOT\n"
        "selector_status=NO_PMD_MOVE_BODY_NATIVE_ONLY\n"
        "selector_damaging_contact=PMD_ATTACK\n"
        "selector_damaging_non_contact=PMD_SHOOT\n"
        "selector_authority=SOULGOLD_GETMOVECATEGORY_PLUS_MOVEMAKESCONTACT\n"
        "combat_timing=SOULGOLD_NATIVE\n"
        "move_fx=SOULGOLD_NATIVE\n"
        "move_spatial_x2y2=SOULGOLD_NATIVE\n"
        "shoot_shadow=FRAME_SYNCHRONOUS_AUTHENTIC_PMDCOLLAB\n"
        "known_ambient_1px_defect=DEFERRED_ROOT_CAUSE_UNRESOLVED\n"
        "runtime_status=PENDING_USER_ACCEPTANCE\n",
        encoding="utf-8",
    )
    print("G3R7 installed: status=native-only, contact=Attack, non-contact=Shoot.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
