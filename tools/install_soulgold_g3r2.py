#!/usr/bin/env python3
"""Install SoulGold G3R2 grounded PMD presentation.

G3R2 fixes two runtime/asset ownership mistakes found by human testing:
1. SoulGold can call BattleLoadMonSpriteGfx() AFTER the early CreateSprite prime,
   overwriting PMD HOME with the legacy battle body. Every native mon-gfx load
   in battle_controllers.c is therefore followed by a PMD re-prime hook.
2. G3R2 assets use action-constant PMD shadow-ground alignment; no per-frame
   body-center translation is permitted.

G1 rolling cache and G2 HOME/interruption behavior remain reused.
"""

from __future__ import annotations

import argparse
import re
import shutil
import subprocess
from pathlib import Path

SOULGOLD_REV = "b5122bdf188943862c13abe4938e88b7bb3c5c4a"
PROTOTYPE_INCLUDE = '#include "pmd_soulgold_prototype.h"\n'


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def require_clean_exact_checkout(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD")
    if head != SOULGOLD_REV:
        raise SystemExit(f"SoulGold baseline mismatch: expected {SOULGOLD_REV}, got {head}")
    if git(repo, "status", "--porcelain"):
        raise SystemExit("SoulGold checkout is not clean; refusing to patch local changes")


def copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise SystemExit(f"Missing required source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"COPY {src} -> {dst}")


def patch_battle_main(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text
    if PROTOTYPE_INCLUDE not in text:
        anchor = '#include "battle_main.h"\n'
        if anchor not in text:
            raise SystemExit("battle_main.c include anchor not found")
        text = text.replace(anchor, anchor + PROTOTYPE_INCLUDE, 1)

    fn_start = text.find("static void CB2_InitBattleInternal(void)\n{")
    fn_end = text.find("\n#define BUFFER_PARTY_VS_SCREEN_STATUS", fn_start)
    if fn_start < 0 or fn_end < 0:
        raise SystemExit("CB2_InitBattleInternal boundary not found")
    fn = text[fn_start:fn_end]
    if "    PmdSoulGoldPrototype_Init();\n" not in fn:
        tail = "    gBattleCommunication[MULTIUSE_STATE] = 0;\n}"
        if tail not in fn:
            raise SystemExit("CB2_InitBattleInternal tail not found")
        fn = fn.replace(tail, "    gBattleCommunication[MULTIUSE_STATE] = 0;\n    PmdSoulGoldPrototype_Init();\n}")
        text = text[:fn_start] + fn + text[fn_end:]

    tick_start = text.find("static void RunBattleSoftwareTick(void)\n{")
    tick_end = text.find("\nstatic void AdvanceBattleFrameRng(void)", tick_start)
    if tick_start < 0 or tick_end < 0:
        raise SystemExit("RunBattleSoftwareTick boundary not found")
    fn = text[tick_start:tick_end]
    if "    PmdSoulGoldPrototype_Tick();\n" not in fn:
        tail = "    RunTasks();\n}"
        if tail not in fn:
            raise SystemExit("RunBattleSoftwareTick tail not found")
        fn = fn.replace(tail, "    RunTasks();\n    PmdSoulGoldPrototype_Tick();\n}")
        text = text[:tick_start] + fn + text[tick_end:]

    if text != original:
        path.write_text(text, encoding="utf-8")
        print("PATCH src/battle_main.c: PMD init + software tick")


def patch_battle_controllers(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    original = text
    if PROTOTYPE_INCLUDE not in text:
        anchor = '#include "battle_controllers.h"\n'
        if anchor not in text:
            raise SystemExit("battle_controllers.c include anchor not found")
        text = text.replace(anchor, anchor + PROTOTYPE_INCLUDE, 1)

    # Keep the pre-CreateSprite prime. It is useful for opponent/normal creation
    # paths and prevents frame 0/1 from exposing legacy pixels before a later
    # native writer exists.
    old = (
        "    SetMultiuseSpriteTemplateToPokemon(species, GetBattlerPosition(battler));\n\n"
        "    gBattlerSpriteIds[battler] = CreateSprite"
    )
    new = (
        "    SetMultiuseSpriteTemplateToPokemon(species, GetBattlerPosition(battler));\n"
        "    PmdSoulGoldPrototype_PrimeBattlerBody(battler);\n\n"
        "    gBattlerSpriteIds[battler] = CreateSprite"
    )
    precreate_count = text.count(old)
    text = text.replace(old, new)

    # Definitive G3R2 fix: BattleLoadMonSpriteGfx is a native pixel writer.
    # Follow every call with PMD re-prime. On naked-if call sites the re-prime
    # intentionally runs unconditionally; for non-Cyndaquil it is a no-op, and
    # for Cyndaquil it is harmless/reinforcing even if that particular load was
    # skipped. This avoids altering native control-flow braces.
    pattern = re.compile(
        r"^(?P<indent>[ \t]*)BattleLoadMonSpriteGfx\([^\n]*, (?P<battler>battler|battlerPartner)\);\n",
        re.MULTILINE,
    )

    def repl(match: re.Match[str]) -> str:
        line = match.group(0)
        indent = match.group("indent")
        battler = match.group("battler")
        return line + f"{indent}PmdSoulGoldPrototype_PrimeBattlerBody({battler});\n"

    text, postload_count = pattern.subn(repl, text)
    native_load_count = len(re.findall(r"BattleLoadMonSpriteGfx\(", original))
    if postload_count != native_load_count:
        raise SystemExit(
            f"Native mon-gfx ownership gate FAIL: found {native_load_count} loads but patched {postload_count}"
        )
    if postload_count < 4:
        raise SystemExit(f"Suspiciously low BattleLoadMonSpriteGfx hook count: {postload_count}")

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"PATCH src/battle_controllers.c: precreate={precreate_count}, post-native-load={postload_count}")
    return precreate_count, postload_count


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    g3 = framework / "prototype" / "soulgold_g3"
    g2 = framework / "prototype" / "soulgold_g2"
    require_clean_exact_checkout(soulgold)

    copy_file(g2 / "pmd_gba_runtime.c", soulgold / "src" / "pmd_gba_runtime.c")
    copy_file(g2 / "pmd_gba_runtime.h", soulgold / "include" / "pmd_gba_runtime.h")
    for name in ("pmd_soulgold_adapter.c", "pmd_soulgold_prototype.c"):
        copy_file(g3 / name, soulgold / "src" / name)
    for name in ("pmd_soulgold_adapter.h", "pmd_soulgold_prototype.h"):
        copy_file(g3 / name, soulgold / "include" / name)

    for variant in ("player", "opponent"):
        copy_file(staging / "src" / f"pmd_cyndaquil_{variant}_ambient.c",
                  soulgold / "src" / f"pmd_cyndaquil_{variant}_ambient.c")
        src = staging / "graphics" / "pmd" / "cyndaquil" / variant
        dst = soulgold / "graphics" / "pmd" / "cyndaquil" / variant
        if dst.exists():
            shutil.rmtree(dst)
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src, dst)

    patch_battle_main(soulgold / "src" / "battle_main.c")
    precreate, postload = patch_battle_controllers(soulgold / "src" / "battle_controllers.c")

    status = git(soulgold, "status", "--short")
    (soulgold / "PMD_G3R2_INSTALL_STATUS.txt").write_text(
        "SoulGold G3R2 installed.\n"
        f"baseline={SOULGOLD_REV}\n"
        "scope=Cyndaquil HOME+Idle+Walk+Nod+Pose+Rotate\n"
        "banned_ambient=LookUp,DeepBreath,Sit\n"
        "grounding=PMD tile-space + action-constant shadow-ground anchor\n"
        "per_frame_body_center_translation=FORBIDDEN\n"
        f"precreate_prime_paths={precreate}\n"
        f"post_BattleLoadMonSpriteGfx_prime_hooks={postload}\n"
        "native_mon_gfx_last_writer=PMD_REPRIME_AFTER_NATIVE\n"
        "save_structure=UNCHANGED\n"
        "MAX_MON_PIC_FRAMES=UNCHANGED\n"
        "native_sprite_anims=UNCHANGED\n"
        "G1_renderer_contract=SEALED_REUSED\n"
        "compile_status=PENDING\nruntime_status=PENDING\n\n" + status + "\n",
        encoding="utf-8",
    )
    print("G3R2 candidate installed; next gate is full compile and cold-boot visual acceptance.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
