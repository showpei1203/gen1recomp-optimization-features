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

    # Android presentation patch is attached to this already-mandatory workflow
    # step so a transport-only build cannot bypass the final Showdown authority.
    framework = Path(__file__).resolve().parents[1]
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
        "android_presentation_semantics=M6X1_R2_M2R5D_M2R11E_M2R12G_M3S1_FINAL_PORT\n"
        "bridge_snapshot_policy=LAST_KNOWN_GOOD_ATOMIC_SWAP\n"
        "provider_animation_clock=ROM_FRAME\n"
    )
    print("M6X1_LIBRETRO_SYSTEM_RAM_PATCH=PASS")


if __name__ == "__main__":
    main()
