#!/usr/bin/env python3
"""Install the G4F runtime tile-delta Attack pilot on pinned SoulGold.

Parent behavior is G4B/G3R11. G4F does not activate new species or change move,
status, damage, controller, shadow, marker, or spatial ownership semantics. It
only changes how the two already activated Attack body timelines are stored and
staged.

Critical timing contract:

    PmdGbaRuntime_Prepare()   # decompress/reconstruct only
    AnimateSprites()          # native callbacks/spatial ownership
    PmdSoulGoldPrototype_Tick() # PMD presentation/marker arbitration
    BuildOamBuffer()          # visible snapshot

No StageFrame/decompression call is allowed in the post-Animate PMD runtime
Tick. Human runtime visual acceptance remains a separate gate.
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
        raise SystemExit(f"G4F required file missing: {src}")
    dst.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dst)
    print(f"COPY {src} -> {dst}")


def software_tick_slice(text: str) -> str:
    start = text.find("static void RunBattleSoftwareTick(void)\n{")
    end = text.find("\nstatic void AdvanceBattleFrameRng(void)", start)
    if start < 0 or end < 0:
        raise SystemExit("G4F RunBattleSoftwareTick boundary missing")
    return text[start:end]


def patch_battle_main(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    runtime_include = '#include "pmd_gba_runtime.h"\n'
    proto_include = '#include "pmd_soulgold_prototype.h"\n'
    if runtime_include not in text:
        if proto_include not in text:
            raise SystemExit("G4F battle_main PMD prototype include missing")
        text = text.replace(proto_include, runtime_include + proto_include, 1)

    if "    PmdGbaRuntime_Prepare();\n    AnimateSprites();\n    PmdSoulGoldPrototype_Tick();\n    BuildOamBuffer();\n" not in text:
        anchor = "    AnimateSprites();\n    PmdSoulGoldPrototype_Tick();\n    BuildOamBuffer();\n"
        replacement = (
            "    // G4F: all PMD body decompression/reconstruction is completed\n"
            "    // before native callbacks. Tick remains the post-native, pre-OAM\n"
            "    // presentation clamp proven by G3R4B.\n"
            "    PmdGbaRuntime_Prepare();\n"
            "    AnimateSprites();\n"
            "    PmdSoulGoldPrototype_Tick();\n"
            "    BuildOamBuffer();\n"
        )
        if anchor not in text:
            raise SystemExit("G4F exact AnimateSprites -> PMD Tick -> BuildOamBuffer anchor missing")
        text = text.replace(anchor, replacement, 1)

    fn = software_tick_slice(text)
    prepare = fn.find("PmdGbaRuntime_Prepare();")
    animate = fn.find("AnimateSprites();")
    pmd = fn.find("PmdSoulGoldPrototype_Tick();")
    oam = fn.find("BuildOamBuffer();")
    if not (0 <= prepare < animate < pmd < oam):
        raise SystemExit(f"G4F critical software tick order invalid: {prepare},{animate},{pmd},{oam}")
    if fn.count("PmdGbaRuntime_Prepare();") != 1:
        raise SystemExit("G4F expected exactly one runtime Prepare call")
    path.write_text(text, encoding="utf-8")


def patch_adapter(path: Path) -> None:
    text = path.read_text(encoding="utf-8")
    include = '#include "pmd_g4f_codec.h"\n'
    runtime_include = '#include "pmd_gba_runtime.h"\n'
    if include not in text:
        if runtime_include not in text:
            raise SystemExit("G4F adapter runtime include missing")
        text = text.replace(runtime_include, runtime_include + include, 1)

    start = text.find("static bool32 SoulGold_StageFrame(u8 battler, u8 cacheSlot, const struct PmdGbaFrame *frame)\n{")
    end = text.find("\nstatic void SoulGold_PresentSlot", start)
    if start < 0 or end < 0:
        raise SystemExit("G4F adapter StageFrame boundary missing")

    new_fn = '''static bool32 SoulGold_StageFrame(u8 battler, u8 cacheSlot, const struct PmdGbaFrame *frame)
{
    enum BattlerPosition position;
    u8 *dest;

    if (frame == NULL || cacheSlot >= PMD_GBA_CACHE_SLOTS)
        return FALSE;
    if (frame->gfx == NULL && frame->packed == NULL)
        return FALSE;
    if (gMonSpritesGfxPtr == NULL || battler >= gBattlersCount)
        return FALSE;

    position = GetBattlerPosition(battler);
    dest = gMonSpritesGfxPtr->spritesGfx[position] + cacheSlot * MON_PIC_SIZE;

    /* G4F packed frames reconstruct an exact 0x800-byte body image here.
     * Legacy frames keep the existing BIOS LZ77 path. Runtime guarantees this
     * function is called only by PmdGbaRuntime_Prepare(), before AnimateSprites. */
    if (frame->packed != NULL)
        return PmdG4fCodec_DecodeFrame(battler, frame->packed, dest);

    DecompressDataWithHeaderWram(frame->gfx, dest);
    return TRUE;
}
'''
    text = text[:start] + new_fn + text[end:]
    if text.count("PmdG4fCodec_DecodeFrame") != 1:
        raise SystemExit("G4F adapter packed decode path count mismatch")
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
    g4f = framework / "prototype" / "soulgold_g4f"

    run([
        sys.executable, str(framework / "tools" / "install_soulgold_g4b_generated_registry.py"),
        "--soulgold", str(soulgold),
        "--assets-staging", str(staging),
        "--framework-root", str(framework),
    ])

    # Replace runtime ABI/implementation only after the complete G3R11 parent
    # chain has installed its proven ownership/controller integration.
    copy_file(g4f / "pmd_gba_runtime.h", soulgold / "include" / "pmd_gba_runtime.h")
    copy_file(g4f / "pmd_gba_runtime.c", soulgold / "src" / "pmd_gba_runtime.c")
    copy_file(g4f / "pmd_g4f_codec.h", soulgold / "include" / "pmd_g4f_codec.h")
    copy_file(g4f / "pmd_g4f_codec.c", soulgold / "src" / "pmd_g4f_codec.c")

    # Parent installers know the two legacy Attack source names and therefore
    # already copied the G4F-patched descriptor C files from staging. The new
    # pack descriptor C files are G4F-only and must be added explicitly.
    for slug, variant in (("cyndaquil", "player"), ("marill", "opponent")):
        pack_name = f"pmd_{slug}_{variant}_g4f_pack.c"
        copy_file(staging / "src" / pack_name, soulgold / "src" / pack_name)

    patch_adapter(soulgold / "src" / "pmd_soulgold_adapter.c")
    patch_battle_main(soulgold / "src" / "battle_main.c")

    runtime = (soulgold / "src" / "pmd_gba_runtime.c").read_text(encoding="utf-8")
    battle = (soulgold / "src" / "battle_main.c").read_text(encoding="utf-8")
    adapter = (soulgold / "src" / "pmd_soulgold_adapter.c").read_text(encoding="utf-8")
    registry = (soulgold / "src" / "pmd_soulgold_species_registry.c").read_text(encoding="utf-8")
    cy_attack = (soulgold / "src" / "pmd_cyndaquil_player_attack.c").read_text(encoding="utf-8")
    ma_attack = (soulgold / "src" / "pmd_marill_opponent_attack.c").read_text(encoding="utf-8")

    if runtime.count("sHost->StageFrame(") != 1:
        raise SystemExit("G4F runtime must contain exactly one host StageFrame call")
    prepare_start = runtime.find("void PmdGbaRuntime_Prepare(void)")
    stage_pos = runtime.find("sHost->StageFrame(")
    tick_start = runtime.find("void PmdGbaRuntime_Tick(void)")
    if not (0 <= prepare_start < stage_pos < tick_start):
        raise SystemExit("G4F StageFrame escaped Prepare phase")
    if "PmdG4fCodec_DecodeFrame" not in adapter:
        raise SystemExit("G4F adapter decoder hook missing")
    if registry.count(".species = SPECIES_") != 2 or "return NULL;" not in registry:
        raise SystemExit("G4F changed native-fallback registry activation")
    for name, attack in (("Cyndaquil", cy_attack), ("Marill", ma_attack)):
        if ".packed = &" not in attack or ".4bpp.lz" in attack:
            raise SystemExit(f"G4F {name} Attack did not replace legacy frame blobs")

    fn = software_tick_slice(battle)
    critical = tuple(fn.find(call) for call in (
        "PmdGbaRuntime_Prepare();",
        "AnimateSprites();",
        "PmdSoulGoldPrototype_Tick();",
        "BuildOamBuffer();",
    ))
    if not (0 <= critical[0] < critical[1] < critical[2] < critical[3]):
        raise SystemExit(f"G4F installed timing contract invalid: {critical}")

    (soulgold / "PMD_G4F_INSTALL_STATUS.txt").write_text(
        "SoulGold PMD G4F runtime tile-delta Attack pilot installed.\n"
        "runtime_parent=G4B_G3R11\n"
        "active_profiles=2_CYNDAQUIL_PLAYER_MARILL_OPPONENT\n"
        "new_species_activated=0\n"
        "codec=LZ77_TILE_DICTIONARY_PLUS_HOME_MAP_PLUS_LZ77_CHANGED_TILE_COMMANDS\n"
        "compressed_actions=ATTACK_ONLY_PILOT\n"
        "decode_phase=PMD_GBA_RUNTIME_PREPARE_BEFORE_ANIMATE_SPRITES\n"
        "critical_order=PREPARE_THEN_ANIMATE_THEN_PMD_TICK_THEN_BUILD_OAM\n"
        "pmd_tick_decompression=FORBIDDEN\n"
        "native_move_damage_controller_fx_semantics=UNCHANGED\n"
        "native_fallback=UNCHANGED\n"
        "shadow_path=UNCHANGED_G3R11_FRAME_SYNCHRONOUS_PMDCOLLAB\n"
        "ambient_known_defect=CYNDAQUIL_1PX_SINK_ROOT_CAUSE_UNRESOLVED_DEFERRED\n"
        "compile_status=PENDING\n"
        "runtime_visual_status=PENDING_USER_ACCEPTANCE\n",
        encoding="utf-8",
    )
    print("G4F runtime tile-delta installer PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
