#!/usr/bin/env python3
"""Install SoulGold G3R5B runtime body override + centered authentic PMD shadow."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    framework = args.framework_root.resolve()
    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g3r5.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(args.assets_staging.resolve()),
        "--framework-root", str(framework),
    ])

    cy_ambient = (soulgold / "src" / "pmd_cyndaquil_player_ambient.c").read_text(encoding="utf-8")
    cy_shadow = (soulgold / "src" / "pmd_cyndaquil_player_shadow.c").read_text(encoding="utf-8")
    if cy_ambient.count(".presentationY = -1") != 1:
        raise SystemExit("G3R5B requires exactly one Cyndaquil -1px runtime body override")
    if "GroundShadowXOffset = 0;" not in cy_shadow:
        raise SystemExit("G3R5B player shadow is not centered on battler base X")

    (soulgold / "PMD_G3R5B_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G3R5B residual presentation correction installed.\n"
        "parent=G3R5_AUTHENTIC_SHADOW_BUILD_PASS_RUNTIME_PARTIAL_FAIL\n"
        "g3r4b_oam_timing=PRESERVED\n"
        "body_grounding=G3R4B_ZERO_PLUS_RUNTIME_ACCEPTANCE_OVERRIDE\n"
        "cyndaquil_idle1_presentation_y=-1\n"
        "all_other_ambient_body_offsets=0\n"
        "shadow_png_may_move_body=FALSE\n"
        "shadow_art=AUTHENTIC_PMDCOLLAB_IDLE0_MASK\n"
        "player_shadow_x=CENTERED_ON_BATTLER_BASE_X\n"
        "shadow_y=PMD_AUTHORED_IDLE0_VERTICAL_OFFSET\n"
        "expected_cyndaquil_idle1=NO_1PX_DOWNWARD_STEP\n"
        "runtime_status=PENDING_USER_ACCEPTANCE\n",
        encoding="utf-8",
    )
    print("G3R5B installed. Gate: Cyndaquil Idle1 stability + centered player shadow.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
