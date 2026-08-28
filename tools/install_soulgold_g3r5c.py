#!/usr/bin/env python3
"""Install SoulGold G3R5C action-ground + frame-synchronous PMD shadows."""

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


def patch_runtime_getter(soulgold: Path) -> None:
    header = soulgold / "include" / "pmd_gba_runtime.h"
    text = header.read_text(encoding="utf-8")
    anchor = "bool32 PmdGbaRuntime_ConsumeInterrupted(u8 battler);\n"
    decl = anchor + "u8 PmdGbaRuntime_GetFrameIndex(u8 battler);\n"
    if "PmdGbaRuntime_GetFrameIndex" not in text:
        if anchor not in text:
            raise SystemExit("runtime header getter anchor not found")
        text = text.replace(anchor, decl, 1)
        header.write_text(text, encoding="utf-8")

    source = soulgold / "src" / "pmd_gba_runtime.c"
    text = source.read_text(encoding="utf-8")
    if "PmdGbaRuntime_GetFrameIndex" not in text:
        anchor = "void PmdGbaRuntime_Tick(void)\n"
        if anchor not in text:
            raise SystemExit("runtime source getter anchor not found")
        getter = (
            "u8 PmdGbaRuntime_GetFrameIndex(u8 battler)\n"
            "{\n"
            "    if (battler >= PMD_GBA_MAX_BATTLERS)\n"
            "        return 0;\n"
            "    return sBattlers[battler].frameIndex;\n"
            "}\n\n"
        )
        text = text.replace(anchor, getter + anchor, 1)
        source.write_text(text, encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    g3r5c = framework / "prototype" / "soulgold_g3r5c"

    # Reuse the proven G3R5/G3R4B body integration hooks and OAM tick order.
    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r5.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    patch_runtime_getter(soulgold)
    copy_file(g3r5c / "pmd_soulgold_dynamic_shadow.h", soulgold / "include" / "pmd_soulgold_dynamic_shadow.h")
    copy_file(g3r5c / "pmd_soulgold_dynamic_shadow.c", soulgold / "src" / "pmd_soulgold_dynamic_shadow.c")
    copy_file(g3r5c / "pmd_soulgold_prototype.c", soulgold / "src" / "pmd_soulgold_prototype.c")

    cy_ambient = (soulgold / "src" / "pmd_cyndaquil_player_ambient.c").read_text(encoding="utf-8")
    cy_shadow = (soulgold / "src" / "pmd_cyndaquil_player_shadow.c").read_text(encoding="utf-8")
    proto = (soulgold / "src" / "pmd_soulgold_prototype.c").read_text(encoding="utf-8")
    dyn = (soulgold / "src" / "pmd_soulgold_dynamic_shadow.c").read_text(encoding="utf-8")

    if cy_ambient.count(".presentationY = -1") < 4:
        raise SystemExit("G3R5C expected Idle1 plus whole Cyndaquil Nod action to carry -1 body correction")
    if "gPmdCyndaquilPlayerNodShadowAction" not in cy_shadow:
        raise SystemExit("G3R5C dynamic Cyndaquil Nod shadow action missing")
    if "PmdGbaRuntime_GetFrameIndex" not in proto:
        raise SystemExit("G3R5C prototype is not synchronized to runtime frame index")
    if "body->x + body->x2 + frame->xOffset" not in dyn or "body->y + body->y2 + frame->yOffset" not in dyn:
        raise SystemExit("G3R5C dynamic shadow does not follow rendered body translation")

    (soulgold / "PMD_G3R5C_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R5C action-ground + frame-synchronous shadow candidate installed.\n"
        "parent=G3R5B_RUNTIME_PARTIAL_FAIL\n"
        "g3r4b_oam_timing=PRESERVED\n"
        "body_anchor=G3R4_PMDCOLLAB_GREEN_BODY_CENTER\n"
        "body_action_ground=MEDIAN_PMDCOLLAB_SHADOW_WHITE_CENTER_DELTA_TO_IDLE0\n"
        "body_runtime_micro_override=CYNDAQUIL_IDLE1_MINUS_1\n"
        "cyndaquil_nod_action_ground=MINUS_1\n"
        "shadow_art=EVERY_SELECTED_PMDCOLLAB_ACTION_FRAME\n"
        "shadow_x=IDLE0_CENTERED_PLUS_PMDCOLLAB_FRAME_DELTA\n"
        "shadow_y=PMDCOLLAB_FRAME_DELTA_PLUS_BODY_PRESENTATION_Y\n"
        "shadow_follows=BODY_BASE_XY_PLUS_BODY_X2Y2_PLUS_FRAME_METADATA\n"
        "native_shadow=RESTORED_WHEN_PMD_BODY_NOT_PRESENTING\n"
        "runtime_status=PENDING_USER_ACCEPTANCE\n",
        encoding="utf-8",
    )
    print("G3R5C installed. Gate: action-level grounding + per-frame PMD shadow timeline.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
