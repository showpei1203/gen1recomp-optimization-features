#!/usr/bin/env python3
"""Install the PMD G1 rolling-cache prototype into an exact SoulGold checkout.

This script deliberately targets one pinned SoulGold revision first. It copies
portable/runtime sources, generates Cyndaquil player/opponent Walk assets from a
pinned SpriteCollab checkout, remaps those frames to SoulGold's existing
Cyndaquil palette, and applies only three host lifecycle hooks.

G1 is a renderer/cache proof, not Rich Ambient yet.
"""

from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

SOULGOLD_REVISION = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
SPRITECOLLAB_REVISION = "4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7"


def run(cmd: list[str], cwd: Path | None = None) -> None:
    print("+", " ".join(str(x) for x in cmd))
    subprocess.run(cmd, cwd=cwd, check=True)


def git_head(repo: Path) -> str:
    return subprocess.check_output(
        ["git", "rev-parse", "HEAD"], cwd=repo, text=True
    ).strip()


def replace_once(path: Path, old: str, new: str, label: str) -> None:
    text = path.read_text(encoding="utf-8")
    if new in text:
        print(f"[already] {label}")
        return
    count = text.count(old)
    if count != 1:
        raise RuntimeError(
            f"{label}: expected exactly one anchor in {path}, found {count}. "
            "Refusing a fuzzy patch against an unknown host revision."
        )
    path.write_text(text.replace(old, new, 1), encoding="utf-8")
    print(f"[patch] {label}")


def copy_runtime(framework: Path, soulgold: Path) -> None:
    proto = framework / "prototype" / "soulgold_g1"
    mapping = {
        proto / "pmd_gba_runtime.c": soulgold / "src" / "pmd_gba_runtime.c",
        proto / "pmd_soulgold_adapter.c": soulgold / "src" / "pmd_soulgold_adapter.c",
        proto / "pmd_soulgold_prototype.c": soulgold / "src" / "pmd_soulgold_prototype.c",
        proto / "pmd_gba_runtime.h": soulgold / "include" / "pmd_gba_runtime.h",
        proto / "pmd_soulgold_adapter.h": soulgold / "include" / "pmd_soulgold_adapter.h",
        proto / "pmd_soulgold_prototype.h": soulgold / "include" / "pmd_soulgold_prototype.h",
    }
    for src, dst in mapping.items():
        if not src.exists():
            raise FileNotFoundError(src)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
        print(f"[copy] {src.relative_to(framework)} -> {dst.relative_to(soulgold)}")


def convert_variant(
    framework: Path,
    soulgold: Path,
    spritecollab: Path,
    work: Path,
    variant: str,
    direction: str,
) -> None:
    out = work / variant
    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True, exist_ok=True)

    run([
        sys.executable,
        str(framework / "tools" / "pmd_gba_converter.py"),
        "--source", str(spritecollab / "sprite" / "0155"),
        "--output", str(out),
        "--species", "Cyndaquil",
        "--national-dex", "155",
        "--actions", "Walk",
        "--direction", direction,
        "--anchor-x", "32",
        "--anchor-y", "44",
        "--body-class", "small_quadruped",
        "--ambient-style", "active_prowl",
        "--source-revision", SPRITECOLLAB_REVISION,
    ])

    run([
        sys.executable,
        str(framework / "tools" / "pmd_gba_remap_host_palette.py"),
        "--frames-root", str(out),
        "--host-palette", str(soulgold / "graphics" / "pokemon" / "cyndaquil" / "normal.pal"),
    ])

    host_asset_root = soulgold / "graphics" / "pmd" / "cyndaquil" / variant
    walk_dst = host_asset_root / "walk"
    walk_dst.mkdir(parents=True, exist_ok=True)
    for png in sorted((out / "walk").glob("frame_*.png")):
        shutil.copy2(png, walk_dst / png.name)
    if len(list(walk_dst.glob("frame_*.png"))) != 4:
        raise RuntimeError(f"{variant}: expected 4 Walk frames after conversion")

    descriptor = soulgold / "src" / f"pmd_cyndaquil_{variant}_g1_assets.c"
    run([
        sys.executable,
        str(framework / "tools" / "pmd_gba_emit_c.py"),
        "--ir", str(out / "manifest.ir.json"),
        "--output", str(descriptor),
        "--variant", variant,
        "--asset-root", f"graphics/pmd/cyndaquil/{variant}",
        "--actions", "Walk",
    ])


def patch_host(soulgold: Path) -> None:
    battle_main = soulgold / "src" / "battle_main.c"
    battle_controllers = soulgold / "src" / "battle_controllers.c"
    pokemon = soulgold / "src" / "pokemon.c"

    replace_once(
        battle_main,
        '#include "battle_main.h"\n',
        '#include "battle_main.h"\n#include "pmd_soulgold_prototype.h"\n',
        "battle_main include",
    )
    replace_once(
        battle_main,
        "    AnimateSprites();\n    BuildOamBuffer();",
        "    AnimateSprites();\n    PmdSoulGoldPrototype_Tick();\n    BuildOamBuffer();",
        "RunBattleSoftwareTick PMD ownership slot",
    )

    replace_once(
        battle_controllers,
        '#include "pokemon_animation.h"\n',
        '#include "pokemon_animation.h"\n#include "pmd_soulgold_prototype.h"\n',
        "battle_controllers include",
    )
    replace_once(
        battle_controllers,
        "    ClearBattleAnimationVars();\n    BattleAI_SetupItems();",
        "    ClearBattleAnimationVars();\n    PmdSoulGoldPrototype_Init();\n    BattleAI_SetupItems();",
        "battle prototype init",
    )

    replace_once(
        pokemon,
        '#include "pokemon_animation.h"\n',
        '#include "pokemon_animation.h"\n#include "pmd_soulgold_prototype.h"\n',
        "pokemon include",
    )
    replace_once(
        pokemon,
        "void SetMultiuseSpriteTemplateToPokemon(u16 speciesTag, enum BattlerPosition battlerPosition)\n{\n    if (gMonSpritesGfxPtr != NULL)",
        "void SetMultiuseSpriteTemplateToPokemon(u16 speciesTag, enum BattlerPosition battlerPosition)\n{\n    if (gMain.inBattle && gMonSpritesGfxPtr != NULL)\n        PmdSoulGoldPrototype_InvalidateBattlerSpriteGeneration(GetBattlerAtPosition(battlerPosition));\n\n    if (gMonSpritesGfxPtr != NULL)",
        "central battler sprite generation invalidation",
    )


def write_evidence(soulgold: Path, work: Path) -> None:
    evidence = soulgold / "PMD_G1_INSTALL_EVIDENCE.txt"
    lines = [
        "PMD G1 SoulGold installer evidence",
        f"soulgold_revision={git_head(soulgold)}",
        f"expected_soulgold_revision={SOULGOLD_REVISION}",
        f"spritecollab_revision={SPRITECOLLAB_REVISION}",
        "prototype=Cyndaquil Walk 4F through 2-slot rolling cache",
        "player_direction=UpRight",
        "opponent_direction=DownLeft",
        "palette=SoulGold existing Cyndaquil normal.pal remap (G1 only)",
        f"work_dir={work}",
        "status=INSTALLED / BUILD NOT YET PROVEN",
        "",
    ]
    evidence.write_text("\n".join(lines), encoding="utf-8")
    print(f"[evidence] {evidence}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--framework", type=Path, default=Path(__file__).resolve().parents[1])
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--spritecollab", type=Path, required=True)
    ap.add_argument("--work-dir", type=Path, default=None)
    ap.add_argument("--skip-revision-check", action="store_true")
    args = ap.parse_args()

    framework = args.framework.resolve()
    soulgold = args.soulgold.resolve()
    spritecollab = args.spritecollab.resolve()
    work = (args.work_dir or (framework / ".work" / "soulgold_g1")).resolve()

    if not (soulgold / ".git").exists():
        raise SystemExit(f"Not a git checkout: {soulgold}")
    if not (spritecollab / "sprite" / "0155" / "AnimData.xml").exists():
        raise SystemExit(f"SpriteCollab Cyndaquil source missing under: {spritecollab}")

    head = git_head(soulgold)
    if not args.skip_revision_check and head != SOULGOLD_REVISION:
        raise SystemExit(
            f"SoulGold HEAD {head} != pinned G1 baseline {SOULGOLD_REVISION}. "
            "Refusing to patch an unverified revision."
        )

    work.mkdir(parents=True, exist_ok=True)
    copy_runtime(framework, soulgold)
    convert_variant(framework, soulgold, spritecollab, work, "player", "UpRight")
    convert_variant(framework, soulgold, spritecollab, work, "opponent", "DownLeft")
    patch_host(soulgold)
    write_evidence(soulgold, work)

    print("G1 install complete. Next authority gate: SoulGold compile must PASS.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
