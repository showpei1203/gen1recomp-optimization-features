# CURRENT_HANDOFF

Date: 2026-08-30
Version: v0.1.0
Strategy: Essentials-first (v17-v21+ primary target)

Next acceptance target:
1. Feed one actual Pokémon Essentials fangame folder to `detect`.
2. Use that game's native Extract Text output.
3. Round-trip 20-50 lines and compile the translated language data in-game.
4. Verify Traditional Chinese font rendering and placeholder integrity.
5. Expand the official zh-TW terminology corpus.
6. Add a custom adapter only if that game is non-standard or heavily modified.

Formal rule: normal Essentials projects use the native localization path first; binary surgery is fallback, not baseline.
