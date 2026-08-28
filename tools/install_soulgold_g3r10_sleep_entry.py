#!/usr/bin/env python3
"""Install G3R10 PMDCollab EventSleep transition on the G3R8C runtime stack.

G3R10 adds presentation-only sleep-entry choreography without changing SoulGold
status or battle logic. A false->true STATUS1_SLEEP edge queues EventSleep. The
transition waits while SoulGold owns gDoingBattleAnim, then plays once and hands
control to the already-proven persistent Sleep loop.

Wake body/shadow assets are installed and linked as source-ready authority, but
Wake runtime presentation remains deliberately deferred. SoulGold can clear
sleep inside its attack-canceler immediately before the battler's own move; a
naive cosmetic Wake hook would either delay the native move or replay Wake after
that move. Neither is accepted here.
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
        raise SystemExit(f"Missing required G3R10 staged file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"COPY {src} -> {dst}")


def add_after(text: str, anchor: str, addition: str, label: str) -> str:
    if addition in text:
        return text
    if anchor not in text:
        raise SystemExit(f"G3R10 missing anchor: {label}")
    return text.replace(anchor, anchor + addition, 1)


def patch_prototype(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    extern_pairs = (
        (
            "extern const struct PmdGbaAction gPmdCyndaquilPlayerSleepAction;\n",
            "extern const struct PmdGbaAction gPmdCyndaquilPlayerEventSleepAction;\n"
            "extern const struct PmdGbaAction gPmdCyndaquilPlayerWakeAction;\n",
            "Cyndaquil transition body externs",
        ),
        (
            "extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerSleepShadowAction;\n",
            "extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerEventSleepShadowAction;\n"
            "extern const struct PmdSoulGoldShadowAction gPmdCyndaquilPlayerWakeShadowAction;\n",
            "Cyndaquil transition shadow externs",
        ),
        (
            "extern const struct PmdGbaAction gPmdMarillOpponentSleepAction;\n",
            "extern const struct PmdGbaAction gPmdMarillOpponentEventSleepAction;\n"
            "extern const struct PmdGbaAction gPmdMarillOpponentWakeAction;\n",
            "Marill transition body externs",
        ),
        (
            "extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentSleepShadowAction;\n",
            "extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentEventSleepShadowAction;\n"
            "extern const struct PmdSoulGoldShadowAction gPmdMarillOpponentWakeShadowAction;\n",
            "Marill transition shadow externs",
        ),
    )
    for anchor, addition, label in extern_pairs:
        text = add_after(text, anchor, addition, label)

    enum_old = "    PMD_PHASE_AMBIENT,\n    PMD_PHASE_SLEEP,\n    PMD_PHASE_HURT,\n"
    enum_new = "    PMD_PHASE_AMBIENT,\n    PMD_PHASE_SLEEP_ENTER,\n    PMD_PHASE_SLEEP,\n    PMD_PHASE_HURT,\n"
    if "PMD_PHASE_SLEEP_ENTER" not in text:
        if enum_old not in text:
            raise SystemExit("G3R10 Sleep-enter phase enum anchor missing")
        text = text.replace(enum_old, enum_new, 1)

    profile_body_old = (
        "    const struct PmdGbaAction *shoot;\n"
        "    const struct PmdGbaAction *sleep;\n"
        "    const struct PmdSoulGoldShadowAction *shadowHome;\n"
    )
    profile_body_new = (
        "    const struct PmdGbaAction *shoot;\n"
        "    const struct PmdGbaAction *sleep;\n"
        "    const struct PmdGbaAction *eventSleep;\n"
        "    const struct PmdGbaAction *wake;\n"
        "    const struct PmdSoulGoldShadowAction *shadowHome;\n"
    )
    if "const struct PmdGbaAction *eventSleep;" not in text:
        if profile_body_old not in text:
            raise SystemExit("G3R10 profile transition body fields anchor missing")
        text = text.replace(profile_body_old, profile_body_new, 1)

    profile_shadow_old = (
        "    const struct PmdSoulGoldShadowAction *shadowShoot;\n"
        "    const struct PmdSoulGoldShadowAction *shadowSleep;\n"
        "    const u8 *attackRushFrame;\n"
    )
    profile_shadow_new = (
        "    const struct PmdSoulGoldShadowAction *shadowShoot;\n"
        "    const struct PmdSoulGoldShadowAction *shadowSleep;\n"
        "    const struct PmdSoulGoldShadowAction *shadowEventSleep;\n"
        "    const struct PmdSoulGoldShadowAction *shadowWake;\n"
        "    const u8 *attackRushFrame;\n"
    )
    if "const struct PmdSoulGoldShadowAction *shadowEventSleep;" not in text:
        if profile_shadow_old not in text:
            raise SystemExit("G3R10 profile transition shadow fields anchor missing")
        text = text.replace(profile_shadow_old, profile_shadow_new, 1)

    state_old = "    bool8 initialized;\n    bool8 moveInterrupted;\n    u8 spriteId;\n"
    state_new = (
        "    bool8 initialized;\n"
        "    bool8 moveInterrupted;\n"
        "    bool8 lastSleeping;\n"
        "    bool8 sleepEnterPending;\n"
        "    u8 spriteId;\n"
    )
    if "bool8 sleepEnterPending;" not in text:
        if state_old not in text:
            raise SystemExit("G3R10 transition state fields anchor missing")
        text = text.replace(state_old, state_new, 1)

    assignments = (
        (
            "        .sleep = &gPmdCyndaquilPlayerSleepAction,\n",
            "        .eventSleep = &gPmdCyndaquilPlayerEventSleepAction,\n"
            "        .wake = &gPmdCyndaquilPlayerWakeAction,\n",
            "Cyndaquil transition body profile",
        ),
        (
            "        .shadowSleep = &gPmdCyndaquilPlayerSleepShadowAction,\n",
            "        .shadowEventSleep = &gPmdCyndaquilPlayerEventSleepShadowAction,\n"
            "        .shadowWake = &gPmdCyndaquilPlayerWakeShadowAction,\n",
            "Cyndaquil transition shadow profile",
        ),
        (
            "        .sleep = &gPmdMarillOpponentSleepAction,\n",
            "        .eventSleep = &gPmdMarillOpponentEventSleepAction,\n"
            "        .wake = &gPmdMarillOpponentWakeAction,\n",
            "Marill transition body profile",
        ),
        (
            "        .shadowSleep = &gPmdMarillOpponentSleepShadowAction,\n",
            "        .shadowEventSleep = &gPmdMarillOpponentEventSleepShadowAction,\n"
            "        .shadowWake = &gPmdMarillOpponentWakeShadowAction,\n",
            "Marill transition shadow profile",
        ),
    )
    for anchor, addition, label in assignments:
        text = add_after(text, anchor, addition, label)

    bind_sleep_tail = (
        "    state->phase = PMD_PHASE_SLEEP;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static void ClearState(u8 battler)\n"
    )
    bind_sleep_new = (
        "    state->phase = PMD_PHASE_SLEEP;\n"
        "    state->lastSleeping = TRUE;\n"
        "    state->sleepEnterPending = FALSE;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static bool32 BindEventSleep(u8 battler, const struct PmdSpeciesProfile *profile)\n"
        "{\n"
        "    struct PmdPresentationState *state = &sState[battler];\n\n"
        "    if (profile == NULL || profile->eventSleep == NULL || !IsBattlerSleeping(battler))\n"
        "        return FALSE;\n"
        "    PmdSoulGold_SetReactivePresentation(battler, FALSE);\n"
        "    PmdSoulGold_SetPersistentPresentation(battler, TRUE);\n"
        "    PmdSoulGold_SetNativeSpatialOwnership(battler, FALSE);\n"
        "    if (!PmdGbaRuntime_Bind(battler, profile->eventSleep))\n"
        "        return FALSE;\n"
        "    state->profile = profile;\n"
        "    state->initialized = TRUE;\n"
        "    state->moveInterrupted = FALSE;\n"
        "    state->lastSleeping = TRUE;\n"
        "    state->sleepEnterPending = FALSE;\n"
        "    state->spriteId = gBattlerSpriteIds[battler];\n"
        "    state->sequenceIndex = 0;\n"
        "    state->phase = PMD_PHASE_SLEEP_ENTER;\n"
        "    state->homeTicksLeft = 0;\n"
        "    return TRUE;\n"
        "}\n\n"
        "static void ClearState(u8 battler)\n"
    )
    if "static bool32 BindEventSleep" not in text:
        if bind_sleep_tail not in text:
            raise SystemExit("G3R10 BindEventSleep insertion anchor missing")
        text = text.replace(bind_sleep_tail, bind_sleep_new, 1)

    clear_anchor = (
        "    sState[battler].initialized = FALSE;\n"
        "    sState[battler].moveInterrupted = FALSE;\n"
        "    sState[battler].spriteId = SPRITE_NONE;\n"
    )
    clear_new = (
        "    sState[battler].initialized = FALSE;\n"
        "    sState[battler].moveInterrupted = FALSE;\n"
        "    sState[battler].lastSleeping = FALSE;\n"
        "    sState[battler].sleepEnterPending = FALSE;\n"
        "    sState[battler].spriteId = SPRITE_NONE;\n"
    )
    if "sState[battler].sleepEnterPending = FALSE;" not in text:
        if clear_anchor not in text:
            raise SystemExit("G3R10 ClearState transition reset anchor missing")
        text = text.replace(clear_anchor, clear_new, 1)

    shadow_anchor = (
        "    if (state->phase == PMD_PHASE_SLEEP)\n"
        "        return state->profile->shadowSleep;\n"
    )
    shadow_new = (
        "    if (state->phase == PMD_PHASE_SLEEP_ENTER)\n"
        "        return state->profile->shadowEventSleep;\n"
    ) + shadow_anchor
    if "return state->profile->shadowEventSleep;" not in text:
        if shadow_anchor not in text:
            raise SystemExit("G3R10 EventSleep shadow selection anchor missing")
        text = text.replace(shadow_anchor, shadow_new, 1)

    init_anchor = (
        "        sState[battler].initialized = FALSE;\n"
        "        sState[battler].moveInterrupted = FALSE;\n"
        "        sState[battler].spriteId = SPRITE_NONE;\n"
    )
    init_new = (
        "        sState[battler].initialized = FALSE;\n"
        "        sState[battler].moveInterrupted = FALSE;\n"
        "        sState[battler].lastSleeping = FALSE;\n"
        "        sState[battler].sleepEnterPending = FALSE;\n"
        "        sState[battler].spriteId = SPRITE_NONE;\n"
    )
    if text.count("sState[battler].lastSleeping = FALSE;") < 2:
        if init_anchor not in text:
            raise SystemExit("G3R10 Init transition reset anchor missing")
        text = text.replace(init_anchor, init_new, 1)

    interrupt_sleep_anchor = (
        "            if (state->phase == PMD_PHASE_SLEEP)\n"
        "            {\n"
        "                PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);\n"
        "                if (!BindSleep(battler, profile))\n"
        "                    BindHome(battler, profile, 28, TRUE);\n"
        "                continue;\n"
        "            }\n"
    )
    interrupt_transition = (
        "            if (state->phase == PMD_PHASE_SLEEP_ENTER)\n"
        "            {\n"
        "                state->sleepEnterPending = IsBattlerSleeping(battler);\n"
        "                state->lastSleeping = IsBattlerSleeping(battler);\n"
        "                PmdSoulGoldDynamicShadow_Update(battler, FALSE, NULL, 0);\n"
        "                PmdGbaRuntime_Unbind(battler);\n"
        "                state->phase = PMD_PHASE_HOME;\n"
        "                state->homeTicksLeft = 0;\n"
        "                PmdSoulGold_SetPersistentPresentation(battler, state->sleepEnterPending);\n"
        "                continue;\n"
        "            }\n"
    )
    if interrupt_transition not in text:
        if interrupt_sleep_anchor not in text:
            raise SystemExit("G3R10 interrupted EventSleep anchor missing")
        text = text.replace(interrupt_sleep_anchor, interrupt_transition + interrupt_sleep_anchor, 1)

    arbitration_old = (
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
    )
    arbitration_new = (
        "        if (IsBattlerSleeping(battler) && !state->lastSleeping)\n"
        "        {\n"
        "            state->lastSleeping = TRUE;\n"
        "            state->sleepEnterPending = TRUE;\n"
        "        }\n"
        "        else if (!IsBattlerSleeping(battler) && state->lastSleeping)\n"
        "        {\n"
        "            state->lastSleeping = FALSE;\n"
        "            state->sleepEnterPending = FALSE;\n"
        "        }\n\n"
        "        if (state->phase != PMD_PHASE_HURT && state->phase != PMD_PHASE_HURT_RETURN && !IsMovePhase(state))\n"
        "        {\n"
        "            if (IsBattlerSleeping(battler))\n"
        "            {\n"
        "                if (state->phase == PMD_PHASE_SLEEP_ENTER)\n"
        "                {\n"
        "                    if (PmdGbaRuntime_IsComplete(battler))\n"
        "                        BindSleep(battler, profile);\n"
        "                }\n"
        "                else if (state->sleepEnterPending)\n"
        "                {\n"
        "                    if (!gDoingBattleAnim && !BindEventSleep(battler, profile))\n"
        "                        BindSleep(battler, profile);\n"
        "                }\n"
        "                else if (state->phase != PMD_PHASE_SLEEP)\n"
        "                {\n"
        "                    if (!BindSleep(battler, profile))\n"
        "                        BindHome(battler, profile, 28, TRUE);\n"
        "                }\n"
        "            }\n"
        "            else if (state->phase == PMD_PHASE_SLEEP || state->phase == PMD_PHASE_SLEEP_ENTER)\n"
        "            {\n"
        "                BindHome(battler, profile, 28, TRUE);\n"
        "            }\n"
        "        }\n\n"
    )
    if "state->sleepEnterPending = TRUE;" not in text[text.find("void PmdSoulGoldPrototype_Tick"):]:
        if arbitration_old not in text:
            raise SystemExit("G3R10 sleep-entry arbitration anchor missing")
        text = text.replace(arbitration_old, arbitration_new, 1)

    continue_old = (
        "        if (state->phase == PMD_PHASE_SLEEP || state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN || IsMovePhase(state))\n"
        "            continue;\n"
    )
    continue_new = (
        "        if (state->sleepEnterPending || state->phase == PMD_PHASE_SLEEP_ENTER || state->phase == PMD_PHASE_SLEEP || state->phase == PMD_PHASE_HURT || state->phase == PMD_PHASE_HURT_RETURN || IsMovePhase(state))\n"
        "            continue;\n"
    )
    if continue_old in text:
        text = text.replace(continue_old, continue_new, 1)
    elif continue_new not in text:
        raise SystemExit("G3R10 sleep-entry persistent continue anchor missing")

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
        sys.executable, str(framework / "tools" / "install_soulgold_g3r8c_sleep_persistence.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    for slug, variant in (("cyndaquil", "player"), ("marill", "opponent")):
        copy_file(
            staging / "src" / f"pmd_{slug}_{variant}_event_sleep.c",
            soulgold / "src" / f"pmd_{slug}_{variant}_event_sleep.c",
        )
        copy_file(
            staging / "src" / f"pmd_{slug}_{variant}_wake.c",
            soulgold / "src" / f"pmd_{slug}_{variant}_wake.c",
        )

    patch_prototype(soulgold / "src" / "pmd_soulgold_prototype.c")

    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    required = (
        "PMD_PHASE_SLEEP_ENTER",
        "BindEventSleep",
        "sleepEnterPending",
        "profile->shadowEventSleep",
        "gPmdCyndaquilPlayerEventSleepAction",
        "gPmdMarillOpponentEventSleepAction",
        "gPmdCyndaquilPlayerWakeAction",
        "gPmdMarillOpponentWakeAction",
        "if (!gDoingBattleAnim && !BindEventSleep(battler, profile))",
        "PmdGbaRuntime_IsComplete(battler)",
    )
    for needle in required:
        if needle not in proto:
            raise SystemExit(f"G3R10 verification missing {needle}")

    (soulgold / "PMD_G3R10_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R10 sleep-entry transition installed.\n"
        "parent=G3R8C_PERSISTENT_SLEEP_G3R9_PER_ACTION_VIEW\n"
        "status_authority=SOULGOLD_STATUS1_SLEEP\n"
        "sleep_entry_trigger=OBSERVED_FALSE_TO_TRUE_STATUS1_SLEEP_EDGE\n"
        "sleep_entry_action=PMDCOLLAB_EVENT_SLEEP\n"
        "sleep_entry_view=SOURCE_DIRECTIONAL_REQUESTED_BATTLE_ROW\n"
        "sleep_entry_busy_policy=QUEUE_WHILE_gDoingBattleAnim_THEN_PLAY\n"
        "sleep_entry_completion=EVENT_SLEEP_THEN_PERSISTENT_SLEEP\n"
        "sleep_view=PMDCOLLAB_DIRECTIONLESS_SOURCE_AUTHORITY\n"
        "wake_assets=PMDCOLLAB_WAKE_BODY_SHADOW_SOURCE_READY\n"
        "wake_runtime=DEFERRED_NATIVE_ATTACK_CANCELER_SYNC_REQUIRED\n"
        "combat_status_logic=UNCHANGED_SOULGOLD_NATIVE\n"
        "combat_damage_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "move_hurt_priority=UNCHANGED_HIGHER_THAN_SLEEP_ENTRY\n"
        "known_ambient_1px_defect=DEFERRED_ROOT_CAUSE_UNRESOLVED\n"
        "runtime_visual_status=PENDING_USER_DEFERRED_TESTING\n",
        encoding="utf-8",
    )
    print("G3R10 installed: EventSleep queues on native sleep edge; Wake remains source-ready but runtime-deferred.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
