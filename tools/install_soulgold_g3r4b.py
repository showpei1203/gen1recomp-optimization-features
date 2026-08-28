#!/usr/bin/env python3
"""Install SoulGold G3R4B OAM-timing regression fix.

G3R4 proved body ownership and species isolation, but runtime video showed the
player PMD body still inherited native species Y motion. Root cause: the G3R4
PMD tick ran after BuildOamBuffer(), so zeroing sprite x2/y2 happened after the
visible OAM snapshot had already been captured.

G3R4B reuses the sealed G3R4 assets/runtime and changes only the software-tick
ordering:

    AnimateSprites()
    PmdSoulGoldPrototype_Tick()
    BuildOamBuffer()
    RunTextPrinters()
    UpdatePaletteFade()
    RunTasks()

This lets native callbacks run first, then lets PMD ownership clamp presentation
coordinates before OAM is snapshotted. Shadow behavior is intentionally
unchanged in this diagnostic build; the separate PMD ground-shadow layer is the
next gate after body stability is accepted.
"""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path


def run(cmd: list[str]) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, check=True)


def patch_tick_order(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = (
        "static void RunBattleSoftwareTick(void)\n"
        "{\n"
        "    // Preserve the original order for every logical tick. BuildOamBuffer only\n"
        "    // creates the software snapshot; the last snapshot is uploaded at VBlank.\n"
        "    AnimateSprites();\n"
        "    BuildOamBuffer();\n"
        "    RunTextPrinters();\n"
        "    UpdatePaletteFade();\n"
        "    RunTasks();\n"
        "    PmdSoulGoldPrototype_Tick();\n"
        "}"
    )
    new = (
        "static void RunBattleSoftwareTick(void)\n"
        "{\n"
        "    // G3R4B: native sprite callbacks run first, then PMD ownership clamps\n"
        "    // x2/y2 and presents the PMD frame BEFORE BuildOamBuffer snapshots OAM.\n"
        "    // G3R4 ran the PMD tick after RunTasks, which was too late: player-side\n"
        "    // native species motion had already been captured into the visible OAM.\n"
        "    AnimateSprites();\n"
        "    PmdSoulGoldPrototype_Tick();\n"
        "    BuildOamBuffer();\n"
        "    RunTextPrinters();\n"
        "    UpdatePaletteFade();\n"
        "    RunTasks();\n"
        "}"
    )
    if old not in text:
        raise SystemExit("G3R4 RunBattleSoftwareTick shape not found; refusing blind patch")
    text = text.replace(old, new, 1)
    path.write_text(text, encoding="utf-8")
    print("PATCH src/battle_main.c: PMD tick moved before BuildOamBuffer")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    framework = args.framework_root.resolve()

    run([
        sys.executable,
        str(framework / "tools" / "install_soulgold_g3r4.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(args.assets_staging.resolve()),
        "--framework-root", str(framework),
    ])

    patch_tick_order(soulgold / "src" / "battle_main.c")

    status = soulgold / "PMD_G3R4B_INSTALL_STATUS.txt"
    status.write_text(
        "SoulGold PMD G3R4B OAM timing diagnostic installed.\n"
        "parent=G3R4\n"
        "change=PMD tick after AnimateSprites and before BuildOamBuffer\n"
        "reason=runtime video proved player native y2 motion survived into OAM snapshot\n"
        "shadow_policy=UNCHANGED_FROM_G3R4; PMD separate shadow deferred\n"
        "expected_player_bobbing=NONE_WHILE_PMD_OWNS_PRESENTATION\n"
        "expected_opponent_behavior=UNCHANGED\n"
        "runtime_status=PENDING_USER_ACCEPTANCE\n",
        encoding="utf-8",
    )
    print("G3R4B installed. Gate: player bobbing must disappear without opponent regression.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
