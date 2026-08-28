#!/usr/bin/env python3
"""Install G3R11 PMDCollab Wake presentation on exact SoulGold wake paths.

G3R10 deliberately stopped at source-ready Wake assets because STATUS1_SLEEP is
cleared inside SoulGold's attack canceler immediately before the native wake
message and the battler's move. Polling only the status bit is too late and can
replay Wake after the move.

G3R11 adds a presentation-only notification at the two native wake paths inside
CancelerAsleepOrFrozen: ordinary timer wake and Uproar wake. The native code
still clears sleep and owns the battle script. PMD Wake begins concurrently with
BattleScript_MoveUsedWokeUp and never blocks that script. If the move begins
before Wake finishes, the existing native move PMD ownership preempts Wake.

Other status cures remain outside this narrow bridge until their exact native
notification points are audited. No battle result, status counter, turn order,
damage, message, or move timing is modified by this patch.
"""
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def patch_header(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    anchor = "void PmdSoulGoldPrototype_HandleHitAnimation(enum BattlerId battler);\n"
    addition = anchor + (
        "\n/* G3R11: presentation-only notification from SoulGold's native sleep canceler. */\n"
        "void PmdSoulGoldPrototype_NotifyWake(enum BattlerId battler);\n"
    )
    if "PmdSoulGoldPrototype_NotifyWake" not in text:
        if anchor not in text:
            raise SystemExit("G3R11 prototype header wake notification anchor missing")
        text = text.replace(anchor, addition, 1)
    path.write_text(text, encoding="utf-8")


def patch_prototype(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    enum_old = "    PMD_PHASE_SLEEP_ENTER,\n    PMD_PHASE_SLEEP,\n    PMD_PHASE_HURT,\n"
    enum_new = "    PMD_PHASE_SLEEP_ENTER,\n    PMD_PHASE_SLEEP,\n    PMD_PHASE_WAKE,\n    PMD_PHASE_HURT,\n"
    if "PMD_PHASE_WAKE" not in text:
        if enum_old not in text:
            raise SystemExit("G3R11 Wake phase enum anchor missing")
        text = text.replace(enum_old, enum_new, 1)

    shadow_anchor = (
        "    if (state->phase == PMD_PHASE_SLEEP)\n"
        "        return state->profile->shadowSleep;\n"
    )
    shadow_new = shadow_anchor + (
        "    if (state->phase == PMD_PHASE_WAKE)\n"
        "        return state->profile->shadowWake;\n"
    )
    if "return state->profile->shadowWake;" not in text:
        if shadow_anchor not in text:
            raise SystemExit("G3R11 Wake shadow selection anchor missing")
        text = text.replace(shadow_anchor, shadow_new, 1)

    bind_event_end = (
        "    state->phase = PMD_PHASE_SLEEP_ENTER;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static void ClearState(u8 battler)\n"
    )
    bind_wake = (
        "    state->phase = PMD_PHASE_SLEEP_ENTER;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static bool32 BindWake(u8 battler, const struct PmdSpeciesProfile *profile)\n"
        "{\n"
        "    struct PmdPresentationState *state = &sState[battler];\n\n"
        "    if (profile == NULL || profile->wake == NULL)\n"
        "        return FALSE;\n"
        "    PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetPersistentPresentation(battler, TRUE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->wake))\n"
        "    {\n"
        "        PmdSoulGold_SetPersistentPresentation(battler, FALSE);\n"
        "        return FALSE;\n"
        "    }\n"
        "    state->profile = profile;\n"
        "    state->initialized = TRUE;\n"
        "    state->moveInterrupted = FALSE;\n"
        "    state->lastSleeping = FALSE;\n"
        "    state->sleepEnterPending = FALSE;\n"
        "    state->spriteId = gBattlerSpriteIds[battler];\n"
        "    state->sequenceIndex = 0;\n"
        "    state->phase = PMD_PHASE_WAKE;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static void ClearState(u8 battler)\n"
    )
    if "static bool32 BindWake" not in text:
        if bind_event_end not in text:
            raise SystemExit("G3R11 BindWake insertion anchor missing")
        text = text.replace(bind_event_end, bind_wake, 1)

    tick_anchor = "void PmdSoulGoldPrototype_Tick(void)\n"
    notify_fn = (
        "void PmdSoulGoldPrototype_NotifyWake(enum BattlerId battler)\n"
        "{\n"
        "    const struct PmdSpeciesProfile *profile;\n"
        "    struct PmdPresentationState *state;\n\n"
        "    if (battler >= gBattlersCount || battler >= PMD_GBA_MAX_BATTLERS)\n"
        "        return;\n"
        "    profile = FindProfile(battler);\n"
        "    if (profile == NULL)\n"
        "        return;\n"
        "    state = &sState[battler];\n"
        "    state->lastSleeping = FALSE;\n"
        "    state->sleepEnterPending = FALSE;\n"
        "    /* Native status authority has already cleared STATUS1_SLEEP. This\n"
        "     * notification owns only PMD body/shadow presentation. */\n"
        "    if (!BindWake(battler, profile))\n"
        "        BindHome(battler, profile, 28, TRUE);\n"
        "}\n\n"
    )
    if "void PmdSoulGoldPrototype_NotifyWake" not in text:
        if tick_anchor not in text:
            raise SystemExit("G3R11 public Wake notification insertion anchor missing")
        text = text.replace(tick_anchor, notify_fn + tick_anchor, 1)

    wake_tick_anchor = (
        "        if (IsBattlerSleeping(battler) && !state->lastSleeping)\n"
    )
    wake_tick = (
        "        if (state->phase == PMD_PHASE_WAKE)\n"
        "        {\n"
        "            state->lastSleeping = FALSE;\n"
        "            state->sleepEnterPending = FALSE;\n"
        "            if (PmdGbaRuntime_IsComplete(battler))\n"
        "            {\n"
        "                PmdSoulGold_SetPersistentPresentation(battler, FALSE);\n"
        "                BindHome(battler, profile, 28, TRUE);\n"
        "            }\n"
        "        }\n\n"
    )
    if wake_tick not in text:
        if wake_tick_anchor not in text:
            raise SystemExit("G3R11 Wake completion arbitration anchor missing")
        text = text.replace(wake_tick_anchor, wake_tick + wake_tick_anchor, 1)

    # Status arbitration must not immediately collapse a just-notified Wake to HOME.
    no_sleep_old = (
        "            else if (state->phase == PMD_PHASE_SLEEP || state->phase == PMD_PHASE_SLEEP_ENTER)\n"
        "            {\n"
        "                BindHome(battler, profile, 28, TRUE);\n"
        "            }\n"
    )
    no_sleep_new = (
        "            else if (state->phase == PMD_PHASE_SLEEP || state->phase == PMD_PHASE_SLEEP_ENTER)\n"
        "            {\n"
        "                BindHome(battler, profile, 28, TRUE);\n"
        "            }\n"
        "            /* PMD_PHASE_WAKE was explicitly notified by native SoulGold\n"
        "             * and is allowed to finish unless a higher-priority move/Hurt\n"
        "             * phase replaces it. */\n"
    )
    if no_sleep_old in text and "PMD_PHASE_WAKE was explicitly notified" not in text:
        text = text.replace(no_sleep_old, no_sleep_new, 1)

    continue_old = (
        "        if (state->sleepEnterPending || state->phase == PMD_PHASE_SLEEP_ENTER || state->phase == PMD_PHASE_SLEEP || state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN || IsMovePhase(state))\n"
        "            continue;\n"
    )
    continue_new = (
        "        if (state->sleepEnterPending || state->phase == PMD_PHASE_SLEEP_ENTER || state->phase == PMD_PHASE_SLEEP || state->phase == PMD_PHASE_WAKE || state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN || IsMovePhase(state))\n"
        "            continue;\n"
    )
    if continue_old in text:
        text = text.replace(continue_old, continue_new, 1)
    elif continue_new not in text:
        raise SystemExit("G3R11 Wake persistent-phase continue anchor missing")

    path.write_text(text, encoding="utf-8")


def patch_native_wake(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    include_anchor = '#include "battle_move_resolution.h"\n'
    include_line = '#include "pmd_soulgold_prototype.h"\n'
    if include_line not in text:
        if include_anchor not in text:
            raise SystemExit("G3R11 native wake include anchor missing")
        text = text.replace(include_anchor, include_anchor + include_line, 1)

    uproar_anchor = (
        "            gBattleMons[ctx->battlerAtk].status1 &= ~STATUS1_SLEEP;\n"
        "            gBattleMons[ctx->battlerAtk].volatiles.nightmare = FALSE;\n"
        "            gEffectBattler = ctx->battlerAtk;\n"
    )
    uproar_new = (
        "            gBattleMons[ctx->battlerAtk].status1 &= ~STATUS1_SLEEP;\n"
        "            gBattleMons[ctx->battlerAtk].volatiles.nightmare = FALSE;\n"
        "            PmdSoulGoldPrototype_NotifyWake(ctx->battlerAtk);\n"
        "            gEffectBattler = ctx->battlerAtk;\n"
    )
    if uproar_new not in text:
        if uproar_anchor not in text:
            raise SystemExit("G3R11 Uproar wake notification anchor missing")
        text = text.replace(uproar_anchor, uproar_new, 1)

    normal_anchor = (
        "                TryDeactivateSleepClause(GetBattlerSide(ctx->battlerAtk), gBattlerPartyIndexes[ctx->battlerAtk]);\n"
        "                gBattleMons[ctx->battlerAtk].volatiles.nightmare = FALSE;\n"
        "                gBattleCommunication[MULTISTRING_CHOOSER] = B_MSG_WOKE_UP;\n"
    )
    normal_new = (
        "                TryDeactivateSleepClause(GetBattlerSide(ctx->battlerAtk), gBattlerPartyIndexes[ctx->battlerAtk]);\n"
        "                gBattleMons[ctx->battlerAtk].volatiles.nightmare = FALSE;\n"
        "                PmdSoulGoldPrototype_NotifyWake(ctx->battlerAtk);\n"
        "                gBattleCommunication[MULTISTRING_CHOOSER] = B_MSG_WOKE_UP;\n"
    )
    if normal_new not in text:
        if normal_anchor not in text:
            raise SystemExit("G3R11 normal timer wake notification anchor missing")
        text = text.replace(normal_anchor, normal_new, 1)

    if text.count("PmdSoulGoldPrototype_NotifyWake(ctx->battlerAtk);") != 2:
        raise SystemExit("G3R11 expected exactly two native sleep-canceler Wake notifications")
    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    framework = args.framework_root.resolve()
    staging = args.assets_staging.resolve()

    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r10_sleep_entry.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    patch_header(soulgold / "include" / "pmd_soulgold_prototype.h")
    patch_prototype(soulgold / "src" / "pmd_soulgold_prototype.c")
    patch_native_wake(soulgold / "src" / "battle_move_resolution.c")

    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    native = (soulgold / "src" / "battle_move_resolution.c").read_text(encoding="utf-8")
    required = (
        "PMD_PHASE_WAKE",
        "static bool32 BindWake",
        "void PmdSoulGoldPrototype_NotifyWake",
        "return state->profile->shadowWake;",
        "PmdSoulGold_SetPersistentPresentation(battler, TRUE);",
        "PmdGbaRuntime_IsComplete(battler)",
    )
    for needle in required:
        if needle not in proto:
            raise SystemExit(f"G3R11 prototype verification missing {needle}")
    if native.count("PmdSoulGoldPrototype_NotifyWake(ctx->battlerAtk);") != 2:
        raise SystemExit("G3R11 native wake notification count changed")
    if "BattleScriptCall(BattleScript_MoveUsedWokeUp);" not in native:
        raise SystemExit("G3R11 native Wake battle-script authority missing")

    (soulgold / "PMD_G3R11_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R11 native Wake notification bridge installed.\n"
        "parent=G3R10_EVENT_SLEEP_ENTRY_TRANSITION\n"
        "wake_source=PMDCOLLAB_WAKE_BODY_SHADOW_DIRECTIONAL_SOURCE_ROW\n"
        "wake_native_authority=SOULGOLD_CANCELER_ASLEEP_OR_FROZEN\n"
        "wake_notification_paths=NORMAL_TIMER_WAKE,UPROAR_WAKE\n"
        "wake_notification_count=2\n"
        "wake_presentation=NONBLOCKING_CONCURRENT_WITH_NATIVE_WAKE_MESSAGE\n"
        "wake_move_preemption=EXISTING_MOVE_ATTACK_SHOOT_OWNERSHIP\n"
        "wake_completion=HOME_THEN_AMBIENT_IF_NOT_PREEMPTED\n"
        "other_status_cures=DEFERRED_UNTIL_EXACT_NATIVE_NOTIFICATION_AUDIT\n"
        "status_authority=SOULGOLD_STATUS1_SLEEP_UNCHANGED\n"
        "battle_script_authority=SOULGOLD_BattleScript_MoveUsedWokeUp_UNCHANGED\n"
        "combat_damage_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "known_ambient_1px_defect=DEFERRED_ROOT_CAUSE_UNRESOLVED\n"
        "runtime_visual_status=PENDING_USER_DEFERRED_TESTING\n",
        encoding="utf-8",
    )
    print("G3R11 installed: native timer/Uproar wake notify PMD Wake without blocking SoulGold's wake/move flow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
