#!/usr/bin/env python3
from pathlib import Path
import argparse,subprocess,sys

MARKER = "M6X1_LIBRETRO_SYSTEM_RAM_EWRAM_V1"

OLD_DATA = '''void* retro_get_memory_data(unsigned id) {
\tswitch (id) {
\tcase RETRO_MEMORY_SAVE_RAM:
\t\treturn savedata;
\tcase RETRO_MEMORY_RTC:
'''

NEW_DATA = '''void* retro_get_memory_data(unsigned id) {
\tswitch (id) {
\tcase RETRO_MEMORY_SAVE_RAM:
\t\treturn savedata;
\tcase RETRO_MEMORY_SYSTEM_RAM:
#ifdef M_CORE_GBA
\t\tif (core->platform(core) == mPLATFORM_GBA) {
\t\t\t/* M6X1_LIBRETRO_SYSTEM_RAM_EWRAM_V1: expose GBA EWRAM only. */
\t\t\treturn ((struct GBA*) core->board)->memory.wram;
\t\t}
#endif
\t\tbreak;
\tcase RETRO_MEMORY_RTC:
'''

OLD_SIZE = '''size_t retro_get_memory_size(unsigned id) {
\tswitch (id) {
\tcase RETRO_MEMORY_SAVE_RAM:
'''

NEW_SIZE = '''size_t retro_get_memory_size(unsigned id) {
\tswitch (id) {
\tcase RETRO_MEMORY_SYSTEM_RAM:
#ifdef M_CORE_GBA
\t\tif (core->platform(core) == mPLATFORM_GBA) {
\t\t\treturn GBA_SIZE_EWRAM;
\t\t}
#endif
\t\tbreak;
\tcase RETRO_MEMORY_SAVE_RAM:
'''


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--mgba", required=True)
    args = ap.parse_args()
    root = Path(args.mgba)
    p = root / "src" / "platform" / "libretro" / "libretro.c"
    text = p.read_text()

    if MARKER in text:
        print("M6X1 mGBA system RAM bridge already installed")
    else:
        if OLD_DATA not in text:
            raise SystemExit("retro_get_memory_data anchor not found")
        if OLD_SIZE not in text:
            raise SystemExit("retro_get_memory_size anchor not found")
        text = text.replace(OLD_DATA, NEW_DATA, 1)
        text = text.replace(OLD_SIZE, NEW_SIZE, 1)
        p.write_text(text)

    out = p.read_text()
    required = [
        MARKER,
        "case RETRO_MEMORY_SYSTEM_RAM:",
        "return ((struct GBA*) core->board)->memory.wram;",
        "return GBA_SIZE_EWRAM;",
    ]
    missing = [x for x in required if x not in out]
    if missing:
        raise SystemExit("M6X1 system RAM patch verification failed: " + repr(missing))

    framework = Path(__file__).resolve().parents[1]

    # R3 stat fidelity: generate Android textures directly from the exact pinned
    # SoulGold stat-change source assets already checked out by CI. Nothing is
    # hand-redrawn and nothing is downloaded at runtime.
    soulgold = Path.cwd() / 'soulgold'
    stat_prep = Path(__file__).with_name('prepare_m6x1_native_stat_assets.py')
    subprocess.run([
        sys.executable,str(stat_prep),'--soulgold',str(soulgold),
        '--android-root',str(framework/'android'/'m6x1')
    ],check=True)

    # Android presentation patch is attached to this already-mandatory workflow
    # step so a transport-only build cannot bypass the final Showdown authority.
    android_patch = Path(__file__).with_name('apply_m6x1_android_presentation_v2.py')
    subprocess.run([sys.executable,str(android_patch),'--root',str(framework/'android'/'m6x1')],check=True)

    status = root / "M6X1_LIBRETRO_SYSTEM_RAM_PATCH_STATUS.txt"
    status.write_text(
        "M6X1_LIBRETRO_SYSTEM_RAM_PATCH=PASS\n"
        "retro_memory_id=RETRO_MEMORY_SYSTEM_RAM\n"
        "gba_region=EWRAM\n"
        "gba_base=0x02000000\n"
        "gba_bytes=262144\n"
        "core_clock_changes=NONE\n"
        "audio_core_changes=NONE\n"
        "android_presentation_semantics=M6X1_R3_NATIVE_SOULGOLD_STAT_FIDELITY\n"
        "bridge_snapshot_policy=LAST_KNOWN_GOOD_ATOMIC_SWAP\n"
        "provider_animation_clock=ROM_FRAME\n"
        "stat_source=PINNED_SOULGOLD_TILEMAP_GFX_PALETTE\n"
        "stat_mask=SHOWDOWN_FRAME_ALPHA\n"
    )
    print("M6X1_LIBRETRO_SYSTEM_RAM_PATCH=PASS")


if __name__ == "__main__":
    main()
