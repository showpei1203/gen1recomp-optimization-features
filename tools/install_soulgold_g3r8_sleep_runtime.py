#!/usr/bin/env python3
"""Install G3R8B persistent PMDCollab Sleep presentation into SoulGold.

G3R8 established that Sleep is a special-state action whose PMDCollab source
may be directionless. G3R8B wires that source-authored action to SoulGold's
native STATUS1_SLEEP lifecycle without changing battle status logic, turn
logic, damage, move FX, or controller timing.

Priority contract:
- PMD Hurt and native move-owned Attack/Shoot/Return retain priority.
- Otherwise STATUS1_SLEEP owns the PMD body and authentic Sleep shadow.
- When Sleep clears, PMD returns through HOME and restarts ambient at index 0.
- Move/Hurt return boundaries still pass through HOME before persistent Sleep
  is rebound on the following normal presentation tick.
- No runtime rotation is applied to directionless Sleep source art.
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
        raise SystemExit(f"Missing required G3R8 staged file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"COPY {src} -> {dst}")


def patch_prototype(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    include_anchor = '#include "constants/species.h"\n'
    include_line = '#include "constants/battle.h"\n'
    if include_line not in text:
        if include_anchor not in text:
            raise SystemExit("G3R8B constants/battle.h include anchor not found")
        text = text.replace(include_anchor, include_line + include_anchor, 1)

    externs = (
        ("extern const struct PmdGbaAction gPmdCyndaquilPlayerShootAction;\n",
         "extern const struct PmdGbaAction gPmdCyndaquilPlayerSleepAction;\n"),
        ("extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerShootShadowAction;\n",
         "extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerSleepShadowAction;\n"),
        ("extern const struct PmdGbaAction gPmdMarillOpponentShootAction;\n",
         "extern const struct PmdGbaAction gPmdMarillOpponentSleepAction;\n"),
        ("extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentShootShadowAction;\n",
         "extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentSleepShadowAction;\n"),
    )
    for anchor, addition in externs:
        if addition not in text:
            if anchor not in text:
                raise SystemExit(f"G3R8B extern anchor missing: {anchor.strip()}")
            text = text.replace(anchor, anchor + addition, 1)

    enum_anchor = "    PMD_PHASE_AMBIENT,\n    PMD_PHASE_HURT,\n"
    enum_new = "    PMD_PHASE_AMBIENT,\n    PMD_PHASE_SLEEP,\n    PMD_PHASE_HURT,\n"
    if "PMD_PHASE_SLEEP" not in text:
        if enum_anchor not in text:
            raise SystemExit("G3R8B Sleep phase enum anchor not found")
        text = text.replace(enum_anchor, enum_new, 1)

    body_struct_anchor = (
        "    const struct PmdGbaAction *attack;\n"
        "    const struct PmdGbaAction *shoot;\n"
        "    const struct PmdSoulGoldShadowAction *shadowHome;\n"
    )
    body_struct_new = (
        "    const struct PmdGbaAction *attack;\n"
        "    const struct PmdGbaAction *shoot;\n"
        "    const struct PmdGbaAction *sleep;\n"
        "    const struct PmdSoulGoldShadowAction *shadowHome;\n"
    )
    if "const struct PmdGbaAction *sleep;" not in text:
        if body_struct_anchor not in text:
            raise SystemExit("G3R8B profile Sleep body anchor not found")
        text = text.replace(body_struct_anchor, body_struct_new, 1)

    shadow_struct_anchor = (
        "    const struct PmdSoulGoldShadowAction *shadowAttack;\n"
        "    const struct PmdSoulGoldShadowAction *shadowShoot;\n"
    )
    shadow_struct_new = (
        "    const struct PmdSoulGoldShadowAction *shadowAttack;\n"
        "    const struct PmdSoulGoldShadowAction *shadowShoot;\n"
        "    const struct PmdSoulGoldShadowAction *shadowSleep;\n"
    )
    if "const struct PmdSoulGoldShadowAction *shadowSleep;" not in text:
        if shadow_struct_anchor not in text:
            raise SystemExit("G3R8B profile Sleep shadow anchor not found")
        text = text.replace(shadow_struct_anchor, shadow_struct_new, 1)

    assignments = (
        ("        .shoot = &gPmdCyndaquilPlayerShootAction,\n",
         "        .sleep = &gPmdCyndaquilPlayerSleepAction,\n"),
        ("        .shadowShoot = &gPmdCyndaquilPlayerShootShadowAction,\n",
         "        .shadowSleep = &gPmdCyndaquilPlayerSleepShadowAction,\n"),
        ("        .shoot = &gPmdMarillOpponentShootAction,\n",
         "        .sleep = &gPmdMarillOpponentSleepAction,\n"),
        ("        .shadowShoot = &gPmdMarillOpponentShootShadowAction,\n",
         "        .shadowSleep = &gPmdMarillOpponentSleepShadowAction,\n"),
    )
    for anchor, addition in assignments:
        if addition not in text:
            if anchor not in text:
                raise SystemExit(f"G3R8B profile assignment anchor missing: {anchor.strip()}")
            text = text.replace(anchor, anchor + addition, 1)

    # Add status ownership helpers after IsMovePhase/marker helpers and before
    # ClearState. This uses SoulGold's own persistent status bits as authority.
    clear_anchor = "static void ClearState(u8 battler)\n"
    helpers = (
        "static bool32 IsBattlerSleeping(u8 battler)\n"
        "{\n"
        "    return battler < gBattlersCount && (gBattleMons[battler].status1 & STATUS1_SLEEP) != 0;\n"
        "}\n\n"
        "static bool32 BindSleep(u8 battler, const struct PmdSpeciesProfile *profile)\n"
        "{\n"
        "    struct PmdPresentationState *state = &sState[battler];\n\n"
        "    if (profile == NULL || profile->sleep == NULL)\n"
        "        return FALSE;\n"
        "    /* Sleep is persistent body presentation only. SoulGold retains\n"
        "     * status/turn authority and no 45-degree runtime rotation is added. */\n"
        "    PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->sleep))\n"
        "        return FALSE;\n"
        "    state->profile = profile;\n"
        "    state->initialized = TRUE;\n"
        "    state->moveInterrupted = FALSE;\n"
        "    state->spriteId = gBattlerSpriteIds[battler];\n"
        "    state->sequenceIndex = 0;\n"
        "    state->phase = PMD_PHASE_SLEEP;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
    )
    if "static bool32 IsBattlerSleeping" not in text:
        if clear_anchor not in text:
            raise SystemExit("G3R8B Sleep helper insertion anchor not found")
        text = text.replace(clear_anchor, helpers + clear_anchor, 1)

    shadow_anchor = (
        "    if (state->phase == PMD_PHASE_MOVE_SHOOT)\n"
        "        return state->profile->shadowShoot;\n"
    )
    shadow_new = shadow_anchor + (
        "    if (state->phase == PMD_PHASE_SLEEP)\n"
        "        return state->profile->shadowSleep;\n"
    )
    if "return state->profile->shadowSleep;" not in text:
        if shadow_anchor not in text:
            raise SystemExit("G3R8B Sleep shadow selection anchor not found")
        text = text.replace(shadow_anchor, shadow_new, 1)

    # If native presentation temporarily evicts persistent Sleep, re-arm the
    # same loop instead of incorrectly restarting ambient HOME.
    interrupt_anchor = (
        "            if (state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN)\n"
        "                PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "            PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);\n"
        "            BindHome(battler, profile, 28, TRUE);\n"
        "            continue;\n"
    )
    interrupt_new = (
        "            if (state->phase == PMD_PHASE_SLEEP)\n"
        "            {\n"
        "                PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);\n"
        "                if (!BindSleep(battler, profile))\n"
        "                    BindHome(battler, profile, 28, TRUE);\n"
        "                continue;\n"
        "            }\n"
    ) + interrupt_anchor
    if "if (state->phase == PMD_PHASE_SLEEP)" not in text[text.find("PmdSoulGoldPrototype_Tick"):]:
        if interrupt_anchor not in text:
            raise SystemExit("G3R8B Sleep interruption anchor not found")
        text = text.replace(interrupt_anchor, interrupt_new, 1)

    # Initial PMD body binding should respect an already-sleeping battler.
    init_bind_anchor = (
        "        if (!state->initialized)\n"
        "        {\n"
        "            PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);\n"
        "            BindHome(battler, profile, 28, TRUE);\n"
        "            continue;\n"
        "        }\n\n"
    )
    init_bind_new = (
        "        if (!state->initialized)\n"
        "        {\n"
        "            PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);\n"
        "            if (IsBattlerSleeping(battler))\n"
        "            {\n"
        "                if (!BindSleep(battler, profile))\n"
        "                    BindHome(battler, profile, 28, TRUE);\n"
        "            }\n"
        "            else\n"
        "            {\n"
        "                BindHome(battler, profile, 28, TRUE);\n"
        "            }\n"
        "            continue;\n"
        "        }\n\n"
    )
    if "if (IsBattlerSleeping(battler))" not in text[text.find("if (!state->initialized)"):text.find("shadowAction = GetCurrentShadowAction")]:
        if init_bind_anchor not in text:
            raise SystemExit("G3R8B initial Sleep ownership anchor not found")
        text = text.replace(init_bind_anchor, init_bind_new, 1)

    # Persistent status arbitration occurs only outside Hurt and native move
    # phases. On wake, force HOME first and restart ambient sequence cleanly.
    shadow_tick_anchor = "        RecordMoveMarker(battler, state);\n        shadowAction = GetCurrentShadowAction(state);\n"
    status_block = (
        "        if (state->phase != PMD_PHASE_HURT && state->phase != PMD_PHASE_HURT_RETURN && !IsMovePhase(state))\n"
        "        {\n"
        "            if (IsBattlerSleeping(battler))\n"
        "            {\n"
        "                if (state->phase != PMD_PHASE_SLEEP && !BindSleep(battler, profile))\n"
        "                    BindHome(battler, profile, 28, TRUE);\n"
        "            }\n"
        "            else if (state->phase == PMD_PHASE_SLEEP)\n"
        "            {\n"
        "                BindHome(battler, profile, 28, TRUE);\n"
        "            }\n"
        "        }\n\n"
        "        RecordMoveMarker(battler, state);\n"
        "        shadowAction = GetCurrentShadowAction(state);\n"
    )
    if "state->phase != PMD_PHASE_SLEEP && !BindSleep" not in text:
        if shadow_tick_anchor not in text:
            raise SystemExit("G3R8B persistent Sleep arbitration anchor not found")
        text = text.replace(shadow_tick_anchor, status_block, 1)

    continue_anchor = (
        "        if (state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN || IsMovePhase(state))\n"
        "            continue;\n"
    )
    continue_new = (
        "        if (state->phase == PMD_PHASE_SLEEP || state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN || IsMovePhase(state))\n"
        "            continue;\n"
    )
    if continue_anchor in text:
        text = text.replace(continue_anchor, continue_new, 1)
    elif continue_new not in text:
        raise SystemExit("G3R8B Sleep persistent-phase continue anchor not found")

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

    # Preserve the complete G3R7B Attack/Shoot selector + presentation-marker
    # bridge as the runtime parent.
    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r7b_marker_bridge.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    for slug, variant in (("cyndaquil", "player"), ("marill", "opponent")):
        copy_file(
            staging / "src" / f"pmd_{slug}_{variant}_sleep.c",
            soulgold / "src" / f"pmd_{slug}_{variant}_sleep.c",
        )

    patch_prototype(soulgold / "src" / "pmd_soulgold_prototype.c")

    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    cy_sleep = (soulgold / "src" / "pmd_cyndaquil_player_sleep.c").read_text(encoding="utf-8")
    ma_sleep = (soulgold / "src" / "pmd_marill_opponent_sleep.c").read_text(encoding="utf-8")
    cy_shadow = (soulgold / "src" / "pmd_cyndaquil_player_shadow.c").read_text(encoding="utf-8")
    ma_shadow = (soulgold / "src" / "pmd_marill_opponent_shadow.c").read_text(encoding="utf-8")

    required = (
        (proto, "PMD_PHASE_SLEEP"),
        (proto, "gBattleMons[battler].status1 & STATUS1_SLEEP"),
        (proto, "BindSleep"),
        (proto, "profile->shadowSleep"),
        (proto, "PmdSoulGoldPrototype_ConsumeMoveMarkers"),
        (proto, "PMD_PHASE_MOVE_SHOOT"),
        (cy_sleep, "gPmdCyndaquilPlayerSleepAction"),
        (ma_sleep, "gPmdMarillOpponentSleepAction"),
        (cy_shadow, "gPmdCyndaquilPlayerSleepShadowAction"),
        (ma_shadow, "gPmdMarillOpponentSleepShadowAction"),
    )
    for haystack, needle in required:
        if needle not in haystack:
            raise SystemExit(f"G3R8B install verification missing {needle}")
    if ".loop = TRUE" not in cy_sleep or ".loop = TRUE" not in ma_sleep:
        raise SystemExit("G3R8B Sleep must remain a persistent looping PMD action")

    (soulgold / "PMD_G3R8B_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R8B persistent Sleep presentation installed.\n"
        "parent=G3R7B_MARKER_BRIDGE_BUILD_PASS_RUNTIME_PENDING\n"
        "status_authority=SOULGOLD_STATUS1_SLEEP\n"
        "sleep_body=PMDCOLLAB_SLEEP_LOOP\n"
        "sleep_shadow=FRAME_SYNCHRONOUS_AUTHENTIC_PMDCOLLAB\n"
        "special_state_view=DIRECTIONLESS_SOURCE_ALLOWED_NO_45_DEGREE_ENFORCEMENT\n"
        "priority=MOVE_AND_HURT_OVER_PERSISTENT_SLEEP\n"
        "sleep_exit=HOME_THEN_AMBIENT_RESTART\n"
        "move_return=HOME_BOUNDARY_PRESERVED_BEFORE_SLEEP_REBIND\n"
        "hurt_return=HOME_BOUNDARY_PRESERVED_BEFORE_SLEEP_REBIND\n"
        "combat_status_logic=UNCHANGED_SOULGOLD_NATIVE\n"
        "combat_damage_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "move_fx_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "controller_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "known_ambient_1px_defect=DEFERRED_ROOT_CAUSE_UNRESOLVED\n"
        "runtime_visual_status=PENDING_USER_DEFERRED_TESTING\n",
        encoding="utf-8",
    )
    print("G3R8B installed: STATUS1_SLEEP owns PMD body/shadow outside move and Hurt phases.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
