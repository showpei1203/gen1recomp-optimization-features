#!/usr/bin/env python3
"""Install SoulGold G3R6A PMDCollab Hurt reaction prototype."""

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
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"COPY {src} -> {dst}")


def patch_adapter(soulgold: Path) -> None:
    header = soulgold / "include" / "pmd_soulgold_adapter.h"
    text = header.read_text(encoding="utf-8")
    anchor = "void PmdSoulGold_UpdateGroundShadow(u8 battler, bool32 active);\n"
    decl = anchor + "void PmdSoulGold_SetReactivePresentation(u8 battler, bool32 active);\n"
    if "PmdSoulGold_SetReactivePresentation" not in text:
        if anchor not in text:
            raise SystemExit("G3R6A adapter header anchor not found")
        text = text.replace(anchor, decl, 1)
        header.write_text(text, encoding="utf-8")

    source = soulgold / "src" / "pmd_soulgold_adapter.c"
    text = source.read_text(encoding="utf-8")
    if "sPmdReactivePresentation" not in text:
        anchor = "static bool8 sNativeShadowSuppressed[PMD_GBA_MAX_BATTLERS];\n"
        if anchor not in text:
            raise SystemExit("G3R6A reactive state anchor not found")
        text = text.replace(anchor, anchor + "static bool8 sPmdReactivePresentation[PMD_GBA_MAX_BATTLERS];\n", 1)

    if "void PmdSoulGold_SetReactivePresentation" not in text:
        anchor = "static bool32 SoulGold_CanPresentBattler(u8 battler)\n"
        setter = (
            "void PmdSoulGold_SetReactivePresentation(u8 battler, bool32 active)\n"
            "{\n"
            "    if (battler < PMD_GBA_MAX_BATTLERS)\n"
            "        sPmdReactivePresentation[battler] = active;\n"
            "}\n\n"
        )
        if anchor not in text:
            raise SystemExit("G3R6A CanPresent anchor not found")
        text = text.replace(anchor, setter + anchor, 1)

    old = "    if (!InBattleChoosingMoves())\n        return FALSE;\n"
    new = "    if (!InBattleChoosingMoves() && !sPmdReactivePresentation[battler])\n        return FALSE;\n"
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit("G3R6A move-choice ownership gate not found")

    # Native hit animation raises gDoingBattleAnim while its visual is active.
    # G3R6A preserves that global busy semantic, but allows only this battler's
    # explicitly reactive PMD body to keep presenting during the Hurt command.
    old = "    if (gDoingBattleAnim)\n        return FALSE;\n"
    new = "    if (gDoingBattleAnim && !sPmdReactivePresentation[battler])\n        return FALSE;\n"
    if old in text:
        text = text.replace(old, new, 1)
    elif new not in text:
        raise SystemExit("G3R6A gDoingBattleAnim ownership gate not found")

    # Initialize and reset the reactive gate alongside existing per-battler state.
    old_pair = "        sNativeShadowSuppressed[battler] = FALSE;\n        sActiveShadowProfiles[battler] = NULL;\n"
    new_pair = "        sNativeShadowSuppressed[battler] = FALSE;\n        sPmdReactivePresentation[battler] = FALSE;\n        sActiveShadowProfiles[battler] = NULL;\n"
    text = text.replace(old_pair, new_pair)
    if text.count("sPmdReactivePresentation[battler] = FALSE;") < 2:
        raise SystemExit("G3R6A reactive state was not initialized and reset")
    source.write_text(text, encoding="utf-8")


def patch_hit_dispatch(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    include = '#include "pmd_soulgold_prototype.h"\n'
    if include not in text:
        anchor = '#include "global.h"\n'
        if anchor not in text:
            raise SystemExit(f"global include anchor missing: {path}")
        text = text.replace(anchor, anchor + include, 1)

    lines = text.splitlines()
    changed = 0
    for i, line in enumerate(lines):
        if "[CONTROLLER_HITANIMATION]" in line and "BtlController_HandleHitAnimation" in line:
            lines[i] = line.replace("BtlController_HandleHitAnimation", "PmdSoulGoldPrototype_HandleHitAnimation")
            changed += 1
    if changed != 1:
        if sum("[CONTROLLER_HITANIMATION]" in line and "PmdSoulGoldPrototype_HandleHitAnimation" in line for line in lines) != 1:
            raise SystemExit(f"Expected exactly one hit-animation dispatch patch in {path}, changed={changed}")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    g3r6a = framework / "prototype" / "soulgold_g3r6a"

    # Preserve G3R5C body/shadow integration and G3R4B OAM timing, then add
    # reactive ownership only around the semantic hit-animation controller event.
    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r5c.py"),
        "--soulgold", str(soulgold), "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    patch_adapter(soulgold)
    copy_file(g3r6a / "pmd_soulgold_prototype.h", soulgold / "include" / "pmd_soulgold_prototype.h")
    copy_file(g3r6a / "pmd_soulgold_prototype.c", soulgold / "src" / "pmd_soulgold_prototype.c")
    patch_hit_dispatch(soulgold / "src" / "battle_controller_player.c")
    patch_hit_dispatch(soulgold / "src" / "battle_controller_opponent.c")

    cy_body = (soulgold / "src" / "pmd_cyndaquil_player_ambient.c").read_text(encoding="utf-8")
    ma_body = (soulgold / "src" / "pmd_marill_opponent_ambient.c").read_text(encoding="utf-8")
    cy_shadow = (soulgold / "src" / "pmd_cyndaquil_player_shadow.c").read_text(encoding="utf-8")
    ma_shadow = (soulgold / "src" / "pmd_marill_opponent_shadow.c").read_text(encoding="utf-8")
    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    adapter = (soulgold / "src" / "pmd_soulgold_adapter.c").read_text(encoding="utf-8")

    required = (
        (cy_body, "gPmdCyndaquilPlayerHurtAction"),
        (ma_body, "gPmdMarillOpponentHurtAction"),
        (cy_shadow, "gPmdCyndaquilPlayerHurtShadowAction"),
        (ma_shadow, "gPmdMarillOpponentHurtShadowAction"),
        (proto, "PmdSoulGoldPrototype_HandleHitAnimation"),
        (proto, "WaitForPmdHurt"),
        (proto, "DoHitAnimHealthboxEffect"),
        (proto, "gDoingBattleAnim = TRUE"),
        (adapter, "sPmdReactivePresentation"),
    )
    for text, needle in required:
        if needle not in text:
            raise SystemExit(f"G3R6A install verification missing {needle}")

    (soulgold / "PMD_G3R6A_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R6A Hurt reaction candidate installed.\n"
        "parent=G3R5C_SHADOW_RUNTIME_ACCEPTED_AMBIENT_1PX_DEFERRED\n"
        "g3r4b_oam_timing=PRESERVED\n"
        "ambient_known_defect=CYNDAQUIL_SINGLE_1PX_SINK_ROOT_CAUSE_UNRESOLVED_DEFERRED_BY_USER\n"
        "new_action=HURT\n"
        "hurt_source=PMDCOLLAB_HURT_ANIM_OFFSETS_SHADOW\n"
        "hurt_trigger=CONTROLLER_HITANIMATION\n"
        "hurt_body=ACTION_SPECIFIC_CLIP_SAFE_CANVAS_PLUS_EXACT_BATTLE_ANCHOR_COMPENSATION\n"
        "hurt_crop_or_scale=FALSE\n"
        "hurt_shadow=FRAME_SYNCHRONOUS_AUTHENTIC_PMDCOLLAB_PLUS_BODY_X2Y2_COMPENSATION\n"
        "native_hit_busy_flag=PRESERVED_GDOINGBATTLEANIM\n"
        "native_hit_healthbox_effect=PRESERVED\n"
        "native_hit_visual=REPLACED_ONLY_FOR_PMD_PROFILED_PLAYER_OPPONENT\n"
        "non_pmd_hit_visual=UNCHANGED\n"
        "return_policy=HURT_TO_HOME_BEFORE_CONTROLLER_RELEASE\n"
        "runtime_status=PENDING_USER_ACCEPTANCE\n",
        encoding="utf-8",
    )
    print("G3R6A installed. Runtime gate: PMD Hurt on both battlers, then clean HOME return.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
