#!/usr/bin/env python3
"""Install SoulGold v1.0.5 Showdown S1E first-visible/spatial-ownership candidate."""
from __future__ import annotations

import argparse
import shutil
import subprocess
from pathlib import Path

SOULGOLD_REV = "77ec3fc6275bb94dd703f4c1976f1457cc44a60b"
INCLUDE_LINE = '#include "showdown_soulgold_prototype.h"\n'


def git(repo: Path, *args: str) -> str:
    return subprocess.check_output(["git", *args], cwd=repo, text=True).strip()


def require_clean_exact_checkout(repo: Path) -> None:
    head = git(repo, "rev-parse", "HEAD")
    if head != SOULGOLD_REV:
        raise SystemExit(f"SoulGold baseline mismatch: expected {SOULGOLD_REV}, got {head}")
    if git(repo, "status", "--porcelain"):
        raise SystemExit("SoulGold checkout is not clean; refusing to patch over local changes")


def copy_file(src: Path, dst: Path) -> None:
    if not src.is_file():
        raise SystemExit(f"Missing required source file: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"COPY {src} -> {dst}")


def ensure_include(text: str, anchor: str) -> str:
    if INCLUDE_LINE in text:
        return text
    if anchor not in text:
        raise SystemExit(f"include anchor not found: {anchor.strip()}")
    return text.replace(anchor, anchor + INCLUDE_LINE, 1)


def patch_battle_main(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text
    text = ensure_include(text, '#include "battle_main.h"\n')

    fn_start = text.find("static void CB2_InitBattleInternal(void)\n{")
    fn_end = text.find("\n#define BUFFER_PARTY_VS_SCREEN_STATUS", fn_start)
    if fn_start < 0 or fn_end < 0:
        raise SystemExit("CB2_InitBattleInternal boundary not found")
    init_fn = text[fn_start:fn_end]
    if "    ShowdownSoulGoldPrototype_Init();\n" not in init_fn:
        tail = "    gBattleCommunication[MULTIUSE_STATE] = 0;\n}"
        if tail not in init_fn:
            raise SystemExit("CB2_InitBattleInternal tail anchor not found")
        init_fn = init_fn.replace(tail, "    gBattleCommunication[MULTIUSE_STATE] = 0;\n    ShowdownSoulGoldPrototype_Init();\n}")
        text = text[:fn_start] + init_fn + text[fn_end:]

    tick_start = text.find("static void RunBattleSoftwareTick(void)\n{")
    tick_end = text.find("\nstatic void AdvanceBattleFrameRng(void)", tick_start)
    if tick_start < 0 or tick_end < 0:
        raise SystemExit("RunBattleSoftwareTick boundary not found")
    tick_fn = text[tick_start:tick_end]

    # Spatial ownership must run after native AnimateSprites callbacks but before
    # BuildOamBuffer snapshots the frame. A post-RunTasks write is one frame too
    # late for OAM and was the key S1D ownership gap exposed by the user video.
    spatial_anchor = "    AnimateSprites();\n    BuildOamBuffer();\n"
    spatial_hook = "    AnimateSprites();\n    ShowdownSoulGoldPrototype_PrepareOam();\n    BuildOamBuffer();\n"
    if "    ShowdownSoulGoldPrototype_PrepareOam();\n" not in tick_fn:
        if spatial_anchor not in tick_fn:
            raise SystemExit("RunBattleSoftwareTick AnimateSprites/BuildOamBuffer anchor not found")
        tick_fn = tick_fn.replace(spatial_anchor, spatial_hook, 1)

    if "    ShowdownSoulGoldPrototype_Tick();\n" not in tick_fn:
        tail = "    RunTasks();\n}"
        if tail not in tick_fn:
            raise SystemExit("RunBattleSoftwareTick tail anchor not found")
        tick_fn = tick_fn.replace(tail, "    RunTasks();\n    ShowdownSoulGoldPrototype_Tick();\n}")

    text = text[:tick_start] + tick_fn + text[tick_end:]
    if text != original:
        path.write_text(text, encoding="utf-8")
        print("PATCH src/battle_main.c: init + pre-OAM spatial ownership + runtime tick")


def patch_battle_gfx_sfx_util(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    original = text
    text = ensure_include(text, '#include "battle.h"\n')

    fn_start = text.find("void BattleLoadMonSpriteGfx(struct Pokemon *mon, enum BattlerId battler)\n{")
    fn_end = text.find("\nvoid BattleGfxSfxDummy2(u16 species)", fn_start)
    if fn_start < 0 or fn_end < 0:
        raise SystemExit("BattleLoadMonSpriteGfx boundary not found")
    fn = text[fn_start:fn_end]
    hook = "    ShowdownSoulGoldPrototype_PrimeLoadedBattlerBody(battler);\n"
    if hook not in fn:
        close = fn.rfind("\n}")
        if close < 0:
            raise SystemExit("BattleLoadMonSpriteGfx closing brace not found")
        fn = fn[:close] + "\n\n" + hook + fn[close:]
        text = text[:fn_start] + fn + text[fn_end:]

    if text != original:
        path.write_text(text, encoding="utf-8")
        print("PATCH src/battle_gfx_sfx_util.c: post-native-load Showdown frame-0 prime")


def patch_battle_controllers(path: Path) -> tuple[int, int]:
    text = path.read_text(encoding="utf-8")
    original = text
    text = ensure_include(text, '#include "battle_controllers.h"\n')

    template_anchor = "    SetMultiuseSpriteTemplateToPokemon(species, GetBattlerPosition(battler));\n"
    template_hook_line = "    ShowdownSoulGoldPrototype_PrimeTemplateBody(battler, species);\n"
    template_hook = template_anchor + template_hook_line
    template_existing = text.count(template_hook_line)
    if template_existing == 0:
        template_paths = text.count(template_anchor)
        if template_paths != 2:
            raise SystemExit(f"Expected exactly 2 battler Pokemon template paths, got {template_paths}")
        text = text.replace(template_anchor, template_hook)
    else:
        if template_existing != 2:
            raise SystemExit(f"Expected exactly 2 existing Showdown template hooks, got {template_existing}")
        template_paths = template_existing

    start_anchor = "    StartSpriteAnim(&gSprites[gBattlerSpriteIds[battler]], 0);\n"
    created_hook_line = "    ShowdownSoulGoldPrototype_PrimeCreatedSpriteBody(battler, species);\n"
    create_anchor = "    gBattlerSpriteIds[battler] = CreateSprite(&gMultiuseSpriteTemplate,\n"
    created_existing = text.count(created_hook_line)
    if created_existing == 0:
        created_paths = 0
        search_from = 0
        for chain_index in range(2):
            template_pos = text.find(template_hook, search_from)
            if template_pos < 0:
                raise SystemExit(f"Showdown creation chain {chain_index + 1}: template hook not found")

            create_pos = text.find(create_anchor, template_pos + len(template_hook))
            if create_pos < 0 or create_pos - template_pos > 1200:
                raise SystemExit(f"Showdown creation chain {chain_index + 1}: CreateSprite anchor not found near template")

            next_template = text.find(template_hook, template_pos + len(template_hook))
            start_pos = text.find(start_anchor, create_pos + len(create_anchor))
            if start_pos < 0 or start_pos - create_pos > 1600:
                raise SystemExit(f"Showdown creation chain {chain_index + 1}: StartSpriteAnim anchor not found near CreateSprite")
            if next_template >= 0 and start_pos > next_template:
                raise SystemExit(f"Showdown creation chain {chain_index + 1}: crossed into next template path")

            insert_pos = start_pos + len(start_anchor)
            text = text[:insert_pos] + created_hook_line + text[insert_pos:]
            created_paths += 1
            search_from = insert_pos + len(created_hook_line)
    else:
        if created_existing != 2:
            raise SystemExit(f"Expected exactly 2 existing created-sprite Showdown hooks, got {created_existing}")
        created_paths = created_existing

    if text.count(created_hook_line) != 2:
        raise SystemExit(f"Expected exactly 2 authoritative created-sprite Showdown hooks, got {text.count(created_hook_line)}")

    if text != original:
        path.write_text(text, encoding="utf-8")
        print(f"PATCH src/battle_controllers.c: template={template_paths}, created-VRAM={created_paths}")

    return template_paths, created_paths


def patch_starter_choose(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = (
        "static const u16 sStarterMon[STARTER_MON_COUNT] =\n"
        "{\n"
        "    SPECIES_TREECKO,\n"
        "    SPECIES_TORCHIC,\n"
        "    SPECIES_MUDKIP,\n"
        "};"
    )
    new = (
        "static const u16 sStarterMon[STARTER_MON_COUNT] =\n"
        "{\n"
        "    SPECIES_SPRIGATITO, // SHOWDOWN_S1E_V105_TEST_STARTER\n"
        "    SPECIES_TORCHIC,\n"
        "    SPECIES_MUDKIP,\n"
        "};"
    )
    if "SHOWDOWN_S1E_V105_TEST_STARTER" not in text:
        if old not in text:
            raise SystemExit("starter roster anchor not found")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


def patch_first_battle(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    old = (
        "    starterMon = GetStarterPokemon(gSpecialVar_Result);\n"
        "    ScriptGiveMon(starterMon, 5, ITEM_NONE, ITEM_NONE);\n"
        "    Achievement_Unlock(ACH_RECEIVE_STARTER);"
    )
    new = (
        "    starterMon = GetStarterPokemon(gSpecialVar_Result);\n"
        "    ScriptGiveMon(starterMon, 5, ITEM_NONE, ITEM_NONE);\n"
        "\n"
        "    // SHOWDOWN_S1E_V105_FIRST_BATTLE_MARILL: deterministic visual proof only.\n"
        "    ZeroEnemyPartyMons();\n"
        "    CreateRandomMon(&gEnemyParty[0], SPECIES_MARILL, 5);\n"
        "    gEnemyPartyCount = 1;\n"
        "\n"
        "    Achievement_Unlock(ACH_RECEIVE_STARTER);"
    )
    if "SHOWDOWN_S1E_V105_FIRST_BATTLE_MARILL" not in text:
        if old not in text:
            raise SystemExit("CB2_GiveStarter anchor not found")
        path.write_text(text.replace(old, new, 1), encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--soulgold", type=Path, required=True)
    ap.add_argument("--assets-staging", type=Path, required=True)
    ap.add_argument("--framework-root", type=Path, default=Path(__file__).resolve().parents[1])
    args = ap.parse_args()

    soulgold = args.soulgold.resolve()
    staging = args.assets_staging.resolve()
    framework = args.framework_root.resolve()
    runtime = framework / "prototype" / "soulgold_showdown_s1"
    proto = framework / "prototype" / "soulgold_showdown_s1e"
    require_clean_exact_checkout(soulgold)

    for name in ("showdown_gba_runtime.c",):
        copy_file(runtime / name, soulgold / "src" / name)
    for name in ("showdown_gba_runtime.h",):
        copy_file(runtime / name, soulgold / "include" / name)
    for name in ("showdown_soulgold_adapter.c", "showdown_soulgold_prototype.c"):
        copy_file(proto / name, soulgold / "src" / name)
    for name in ("showdown_soulgold_adapter.h", "showdown_soulgold_prototype.h"):
        copy_file(proto / name, soulgold / "include" / name)
    for name in ("showdown_sprigatito_back_idle.c", "showdown_marill_front_idle.c"):
        copy_file(staging / "src" / name, soulgold / "src" / name)

    for species in ("sprigatito", "marill"):
        src_graphics = staging / "graphics" / "showdown" / species
        dst_graphics = soulgold / "graphics" / "showdown" / species
        if not src_graphics.is_dir():
            raise SystemExit(f"Missing staged graphics: {src_graphics}")
        if dst_graphics.exists():
            shutil.rmtree(dst_graphics)
        dst_graphics.parent.mkdir(parents=True, exist_ok=True)
        shutil.copytree(src_graphics, dst_graphics)

    patch_battle_main(soulgold / "src" / "battle_main.c")
    patch_battle_gfx_sfx_util(soulgold / "src" / "battle_gfx_sfx_util.c")
    template_paths, created_paths = patch_battle_controllers(soulgold / "src" / "battle_controllers.c")
    patch_starter_choose(soulgold / "src" / "starter_choose.c")
    patch_first_battle(soulgold / "src" / "battle_setup.c")

    status = git(soulgold, "status", "--short")
    (soulgold / "SHOWDOWN_S1E_V105_INSTALL_STATUS.txt").write_text(
        "SoulGold Showdown S1E v1.0.5 first-visible/spatial candidate installed.\n"
        f"baseline={SOULGOLD_REV}\n"
        "baseline_version=v1.0.5\n"
        "player_target=Sprigatito back Showdown idle\n"
        "opponent_target=Marill front Showdown idle\n"
        "starter_flow=normal starter chooser; left option Sprigatito\n"
        "first_battle_enemy=Lv5 Marill\n"
        "entry_ownership=post-BattleLoad RAM prime + template prime + post-CreateSprite OBJ prime\n"
        f"template_prime_paths={template_paths}\n"
        f"created_sprite_vram_prime_paths={created_paths}\n"
        "idle_ownership=move-selection Showdown pixels + pre-BuildOamBuffer spatial last-writer\n"
        "idle_body_pos2=zeroed only while Showdown CanPresent\n"
        "idle_healthbox=canonical coords + zero pos2 only while Showdown CanPresent\n"
        "native_sendout_move_hit_faint_spatial=UNCHANGED\n"
        "b_button_harness=REMOVED\n"
        "overworld_patch=NONE\n"
        "PMD_RUNTIME_DEPENDENCY=NONE\n\n" + status + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
