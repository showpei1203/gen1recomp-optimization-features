// SoulGoldRecomp R1 runner entry.
//
// This intentionally mirrors only the generic EmeraldRecomp runner seam.
// Emerald-specific RAM-dispatch aliases and ROM identity are not copied.
// SoulGold-specific exceptions must be added only after trace evidence proves
// they are necessary.

#include <cstdio>
#include <cstring>

#include "runtime.h"

#ifndef SOULGOLD_RECOMP_DEFAULT_GAME_CONFIG
#define SOULGOLD_RECOMP_DEFAULT_GAME_CONFIG "variants/soulgold/game.toml"
#endif

namespace {

void print_usage() {
    std::printf(
        "SoulGoldRecomp [--bios <path>] [--rom <path>] [game.toml]\n"
        "\n"
        "The ROM must match the exact SoulGold source-build identity used to\n"
        "generate the native guest corpus. Showdown/PMD asset packs are loaded\n"
        "through the SoulGold mod catalog and are not inserted into the ROM.\n");
}

}  // namespace

int main(int argc, char** argv) {
    for (int i = 1; i < argc; ++i) {
        if (std::strcmp(argv[i], "--help") == 0 ||
            std::strcmp(argv[i], "-h") == 0) {
            print_usage();
            return 0;
        }
    }

    gbarecomp::RunOptions opts;
    opts.builtin_game_name = "Pokemon SoulGold v1.0.5 source-build";
    // Identity remains owned by game.toml during R1 bring-up. Once a frozen
    // native release ROM is selected, the runner may bake its SHA-1/CRC32 too.
    opts.builtin_rom_sha1 = nullptr;
    opts.builtin_rom_crc32 = 0;
    opts.mod_game_id = "pokemon-soulgold-v105";
    opts.launcher_region = "Development";
    opts.launcher_game_config = SOULGOLD_RECOMP_DEFAULT_GAME_CONFIG;
    opts.freely_resizable_window = true;
    opts.show_fps_by_default = false;

    return gbarecomp::run_game(argc, argv, opts);
}
