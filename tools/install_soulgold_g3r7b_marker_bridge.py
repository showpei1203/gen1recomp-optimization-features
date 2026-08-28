#!/usr/bin/env python3
"""Install G3R7B non-authoritative PMD Rush/Hit/Return marker bridge.

This stage exposes PMDCollab action markers as runtime presentation events while
leaving SoulGold combat timing completely unchanged. Marker events are recorded
only when the PMD body runtime actually presents the marked frame. Future phases
may use these events to align presentation, but G3R7B does not move damage,
move FX, controller timing, or battle-script authority.
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
    anchor = "bool32 PmdSoulGoldPrototype_IsMoveReturnReady(enum BattlerId battler);\n"
    block = anchor + (
        "\n#define PMD_SOULGOLD_MOVE_MARKER_RUSH   (1 << 0)\n"
        "#define PMD_SOULGOLD_MOVE_MARKER_HIT    (1 << 1)\n"
        "#define PMD_SOULGOLD_MOVE_MARKER_RETURN (1 << 2)\n"
        "u8 PmdSoulGoldPrototype_ConsumeMoveMarkers(enum BattlerId battler);\n"
        "u8 PmdSoulGoldPrototype_GetMoveMarkerSeenMask(enum BattlerId battler);\n"
    )
    if "PmdSoulGoldPrototype_ConsumeMoveMarkers" not in text:
        if anchor not in text:
            raise SystemExit("G3R7B prototype header marker anchor not found")
        text = text.replace(anchor, block, 1)
    path.write_text(text, encoding="utf-8")


def patch_prototype(path: Path) -> None:
    text = path.read_text(encoding="utf-8")

    # Marker constants are emitted from pinned PMDCollab AnimData.xml.
    extern_anchors = (
        ("extern const struct PmdGbaAction gPmdCyndaquilPlayerAttackAction;\n",
         "extern const u8 gPmdCyndaquilPlayerAttackRushFrame;\nextern const u8 gPmdCyndaquilPlayerAttackHitFrame;\nextern const u8 gPmdCyndaquilPlayerAttackReturnFrame;\n"),
        ("extern const struct PmdGbaAction gPmdCyndaquilPlayerShootAction;\n",
         "extern const u8 gPmdCyndaquilPlayerShootRushFrame;\nextern const u8 gPmdCyndaquilPlayerShootHitFrame;\nextern const u8 gPmdCyndaquilPlayerShootReturnFrame;\n"),
        ("extern const struct PmdGbaAction gPmdMarillOpponentAttackAction;\n",
         "extern const u8 gPmdMarillOpponentAttackRushFrame;\nextern const u8 gPmdMarillOpponentAttackHitFrame;\nextern const u8 gPmdMarillOpponentAttackReturnFrame;\n"),
        ("extern const struct PmdGbaAction gPmdMarillOpponentShootAction;\n",
         "extern const u8 gPmdMarillOpponentShootRushFrame;\nextern const u8 gPmdMarillOpponentShootHitFrame;\nextern const u8 gPmdMarillOpponentShootReturnFrame;\n"),
    )
    for anchor, addition in extern_anchors:
        first = addition.splitlines()[0].split()[-1].rstrip(';')
        if first not in text:
            if anchor not in text:
                raise SystemExit(f"G3R7B marker extern anchor not found: {anchor.strip()}")
            text = text.replace(anchor, anchor + addition, 1)

    profile_anchor = (
        "    const struct PmdSoulGoldShadowAction *shadowAttack;\n"
        "    const struct PmdSoulGoldShadowAction *shadowShoot;\n"
        "    u16 homeHolds[PMD_G3R6B_AMBIENT_COUNT];\n"
    )
    profile_new = (
        "    const struct PmdSoulGoldShadowAction *shadowAttack;\n"
        "    const struct PmdSoulGoldShadowAction *shadowShoot;\n"
        "    const u8 *attackRushFrame;\n"
        "    const u8 *attackHitFrame;\n"
        "    const u8 *attackReturnFrame;\n"
        "    const u8 *shootRushFrame;\n"
        "    const u8 *shootHitFrame;\n"
        "    const u8 *shootReturnFrame;\n"
        "    u16 homeHolds[PMD_G3R6B_AMBIENT_COUNT];\n"
    )
    if "const u8 *attackRushFrame;" not in text:
        if profile_anchor not in text:
            raise SystemExit("G3R7B profile marker pointer anchor not found")
        text = text.replace(profile_anchor, profile_new, 1)

    assignments = (
        ("        .shadowShoot = &gPmdCyndaquilPlayerShootShadowAction,\n",
         "        .attackRushFrame = &gPmdCyndaquilPlayerAttackRushFrame,\n        .attackHitFrame = &gPmdCyndaquilPlayerAttackHitFrame,\n        .attackReturnFrame = &gPmdCyndaquilPlayerAttackReturnFrame,\n        .shootRushFrame = &gPmdCyndaquilPlayerShootRushFrame,\n        .shootHitFrame = &gPmdCyndaquilPlayerShootHitFrame,\n        .shootReturnFrame = &gPmdCyndaquilPlayerShootReturnFrame,\n"),
        ("        .shadowShoot = &gPmdMarillOpponentShootShadowAction,\n",
         "        .attackRushFrame = &gPmdMarillOpponentAttackRushFrame,\n        .attackHitFrame = &gPmdMarillOpponentAttackHitFrame,\n        .attackReturnFrame = &gPmdMarillOpponentAttackReturnFrame,\n        .shootRushFrame = &gPmdMarillOpponentShootRushFrame,\n        .shootHitFrame = &gPmdMarillOpponentShootHitFrame,\n        .shootReturnFrame = &gPmdMarillOpponentShootReturnFrame,\n"),
    )
    for anchor, addition in assignments:
        if addition.splitlines()[0] not in text:
            if anchor not in text:
                raise SystemExit(f"G3R7B profile marker assignment anchor not found: {anchor.strip()}")
            text = text.replace(anchor, anchor + addition, 1)

    state_anchor = (
        "    u8 sequenceIndex;\n"
        "    u8 phase;\n"
        "    u16 homeTicksLeft;\n"
    )
    state_new = (
        "    u8 sequenceIndex;\n"
        "    u8 phase;\n"
        "    u8 moveMarkerPendingMask;\n"
        "    u8 moveMarkerSeenMask;\n"
        "    u8 moveMarkerLastFrame;\n"
        "    u16 homeTicksLeft;\n"
    )
    if "moveMarkerPendingMask" not in text:
        if state_anchor not in text:
            raise SystemExit("G3R7B presentation state marker anchor not found")
        text = text.replace(state_anchor, state_new, 1)

    # Add helper logic immediately after IsMovePhase.
    is_move_fn = (
        "static bool32 IsMovePhase(const struct PmdPresentationState *state)\n"
        "{\n"
        "    return state != NULL && (state->phase == PMD_PHASE_MOVE_ATTACK || state->phase == PMD_PHASE_MOVE_SHOOT || state->phase == PMD_PHASE_MOVE_RETURN);\n"
        "}\n\n"
    )
    helper = is_move_fn + (
        "#define PMD_SOURCE_MARKER_NONE 0xFF\n\n"
        "static void ResetMoveMarkerState(struct PmdPresentationState *state)\n"
        "{\n"
        "    if (state == NULL)\n"
        "        return;\n"
        "    state->moveMarkerPendingMask = 0;\n"
        "    state->moveMarkerSeenMask = 0;\n"
        "    state->moveMarkerLastFrame = PMD_SOURCE_MARKER_NONE;\n"
        "}\n\n"
        "static void RecordMoveMarker(u8 battler, struct PmdPresentationState *state)\n"
        "{\n"
        "    const u8 *rush;\n"
        "    const u8 *hit;\n"
        "    const u8 *ret;\n"
        "    u8 frame;\n"
        "    u8 mask = 0;\n\n"
        "    if (state == NULL || state->profile == NULL || !PmdGbaRuntime_IsPresenting(battler))\n"
        "        return;\n"
        "    if (state->phase == PMD_PHASE_MOVE_ATTACK)\n"
        "    {\n"
        "        rush = state->profile->attackRushFrame;\n"
        "        hit = state->profile->attackHitFrame;\n"
        "        ret = state->profile->attackReturnFrame;\n"
        "    }\n"
        "    else if (state->phase == PMD_PHASE_MOVE_SHOOT)\n"
        "    {\n"
        "        rush = state->profile->shootRushFrame;\n"
        "        hit = state->profile->shootHitFrame;\n"
        "        ret = state->profile->shootReturnFrame;\n"
        "    }\n"
        "    else\n"
        "    {\n"
        "        return;\n"
        "    }\n\n"
        "    frame = PmdGbaRuntime_GetFrameIndex(battler);\n"
        "    if (frame == state->moveMarkerLastFrame)\n"
        "        return;\n"
        "    state->moveMarkerLastFrame = frame;\n"
        "    if (rush != NULL && *rush != PMD_SOURCE_MARKER_NONE && frame == *rush)\n"
        "        mask |= PMD_SOULGOLD_MOVE_MARKER_RUSH;\n"
        "    if (hit != NULL && *hit != PMD_SOURCE_MARKER_NONE && frame == *hit)\n"
        "        mask |= PMD_SOULGOLD_MOVE_MARKER_HIT;\n"
        "    if (ret != NULL && *ret != PMD_SOURCE_MARKER_NONE && frame == *ret)\n"
        "        mask |= PMD_SOULGOLD_MOVE_MARKER_RETURN;\n"
        "    state->moveMarkerPendingMask |= mask;\n"
        "    state->moveMarkerSeenMask |= mask;\n"
        "}\n\n"
    )
    if "static void RecordMoveMarker" not in text:
        if is_move_fn not in text:
            raise SystemExit("G3R7B marker helper insertion anchor not found")
        text = text.replace(is_move_fn, helper, 1)

    # Reset state in ClearState and Init.
    clear_anchor = (
        "    sState[battler].sequenceIndex = 0;\n"
        "    sState[battler].phase = PMD_PHASE_HOME;\n"
        "    sState[battler].homeTicksLeft = 0;\n"
    )
    clear_new = (
        "    sState[battler].sequenceIndex = 0;\n"
        "    sState[battler].phase = PMD_PHASE_HOME;\n"
        "    ResetMoveMarkerState(&sState[battler]);\n"
        "    sState[battler].homeTicksLeft = 0;\n"
    )
    if clear_new not in text:
        if clear_anchor not in text:
            raise SystemExit("G3R7B ClearState marker reset anchor not found")
        text = text.replace(clear_anchor, clear_new, 1)

    init_anchor = (
        "        sState[battler].sequenceIndex = 0;\n"
        "        sState[battler].phase = PMD_PHASE_HOME;\n"
        "        sState[battler].homeTicksLeft = 0;\n"
    )
    init_new = (
        "        sState[battler].sequenceIndex = 0;\n"
        "        sState[battler].phase = PMD_PHASE_HOME;\n"
        "        ResetMoveMarkerState(&sState[battler]);\n"
        "        sState[battler].homeTicksLeft = 0;\n"
    )
    if init_new not in text:
        if init_anchor not in text:
            raise SystemExit("G3R7B Init marker reset anchor not found")
        text = text.replace(init_anchor, init_new, 1)

    # Begin a new marker ledger only for damaging moves.
    begin_anchor = (
        "    if (GetMoveCategory(move) == DAMAGE_CATEGORY_STATUS)\n"
        "        return;\n"
        "    if (MoveMakesContact(move))\n"
    )
    begin_new = (
        "    if (GetMoveCategory(move) == DAMAGE_CATEGORY_STATUS)\n"
        "        return;\n"
        "    ResetMoveMarkerState(&sState[battler]);\n"
        "    if (MoveMakesContact(move))\n"
    )
    if begin_new not in text:
        if begin_anchor not in text:
            raise SystemExit("G3R7B BeginMoveAction marker reset anchor not found")
        text = text.replace(begin_anchor, begin_new, 1)

    # Record only after interruption/availability handling, immediately before
    # shadow selection so body marker and shadow frame share the same index.
    tick_anchor = (
        "        shadowAction = GetCurrentShadowAction(state);\n"
        "        PmdSoulGoldDynamicShadow_Update(\n"
    )
    tick_new = (
        "        RecordMoveMarker(battler, state);\n"
        "        shadowAction = GetCurrentShadowAction(state);\n"
        "        PmdSoulGoldDynamicShadow_Update(\n"
    )
    if tick_new not in text:
        if tick_anchor not in text:
            raise SystemExit("G3R7B Tick marker record anchor not found")
        text = text.replace(tick_anchor, tick_new, 1)

    # Public consume/diagnostic APIs do not alter battle semantics.
    api_anchor = "void PmdSoulGoldPrototype_PrimeLoadedBattlerBody(u8 battler)\n"
    api_block = (
        "u8 PmdSoulGoldPrototype_ConsumeMoveMarkers(enum BattlerId battler)\n"
        "{\n"
        "    u8 mask;\n"
        "    if (battler >= PMD_GBA_MAX_BATTLERS)\n"
        "        return 0;\n"
        "    mask = sState[battler].moveMarkerPendingMask;\n"
        "    sState[battler].moveMarkerPendingMask = 0;\n"
        "    return mask;\n"
        "}\n\n"
        "u8 PmdSoulGoldPrototype_GetMoveMarkerSeenMask(enum BattlerId battler)\n"
        "{\n"
        "    if (battler >= PMD_GBA_MAX_BATTLERS)\n"
        "        return 0;\n"
        "    return sState[battler].moveMarkerSeenMask;\n"
        "}\n\n"
    ) + api_anchor
    if "u8 PmdSoulGoldPrototype_ConsumeMoveMarkers" not in text:
        if api_anchor not in text:
            raise SystemExit("G3R7B marker public API anchor not found")
        text = text.replace(api_anchor, api_block, 1)

    path.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    framework = args.framework_root.resolve()
    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r7.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(args.assets_staging.resolve()),
        "--framework-root", str(framework),
    ])

    patch_header(soulgold / "include" / "pmd_soulgold_prototype.h")
    patch_prototype(soulgold / "src" / "pmd_soulgold_prototype.c")

    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    header = (soulgold / "include" / "pmd_soulgold_prototype.h").read_text(encoding="utf-8")
    for needle in (
        "PMD_SOULGOLD_MOVE_MARKER_RUSH",
        "PMD_SOULGOLD_MOVE_MARKER_HIT",
        "PMD_SOULGOLD_MOVE_MARKER_RETURN",
        "RecordMoveMarker",
        "PmdSoulGoldPrototype_ConsumeMoveMarkers",
        "PmdSoulGoldPrototype_GetMoveMarkerSeenMask",
        "attackRushFrame",
        "shootHitFrame",
    ):
        if needle not in proto and needle not in header:
            raise SystemExit(f"G3R7B install verification missing {needle}")

    (soulgold / "PMD_G3R7B_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R7B PMDCollab marker bridge installed.\n"
        "parent=G3R7_ATTACK_SHOOT_SELECTOR_BUILD_GATE\n"
        "marker_source=PINNED_PMDCOLLAB_ANIMDATA_XML\n"
        "marker_events=RUSH_HIT_RETURN_FRAME_ENTRY\n"
        "marker_event_condition=PMD_BODY_FRAME_ACTUALLY_PRESENTING\n"
        "marker_api=CONSUME_PENDING_PLUS_GET_SEEN_MASK\n"
        "combat_damage_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "move_fx_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "controller_timing=UNCHANGED_SOULGOLD_NATIVE\n"
        "status_selector=NO_PMD_MOVE_BODY\n"
        "contact_selector=ATTACK\n"
        "non_contact_selector=SHOOT\n"
        "known_ambient_1px_defect=DEFERRED_ROOT_CAUSE_UNRESOLVED\n"
        "runtime_status=STRUCTURAL_ONLY_NO_VISUAL_CLAIM\n",
        encoding="utf-8",
    )
    print("G3R7B installed: PMD marker events observable, combat authority unchanged.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
