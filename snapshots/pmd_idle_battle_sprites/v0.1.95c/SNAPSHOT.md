# PMD Idle Battle Sprites v0.1.95c — Exact Thor Source Snapshot

Captured from the user's live AYN Thor Gen1Recomp installation on 2026-08-19.

## Authority status

- Role: `SOURCE SNAPSHOT / DEVELOPMENT AUTHORITY`
- Not a promoted Gen1Recomp formal game baseline.
- Do not overwrite the live Thor installation from this snapshot without a separately validated candidate.

## Live source

- Package: `io.github.averageconsumer.gen1recomp.androidtest`
- Root: `/storage/emulated/0/Android/data/io.github.averageconsumer.gen1recomp.androidtest/files/save/pokemon-love2d`
- Mod: `/mods/pmd_idle_battle_sprites`
- Mod id: `pmd_idle_battle_sprites`
- Version: `0.1.95c`
- API: `2`
- Priority: `140`
- Category: `GRAPHICS`
- Profile: `content`
- Optional dependency: `kanto_gear`
- Permission: `engine_internals`

## Exact hashes

- `GEN1RECOMP_PMD_EXACT_SOURCE_20260819_185548.zip`
  - SHA-256: `a9cb2426e661b9cbe9c439a84696badbc139f855f93b19b9c1741120fd468b81`
- `main.lua`
  - SHA-256: `11a1b8c3f8cdc098a8f7792b4b5fcb9557f62400999685dcc9337eb893a6f883`
- `manifest.json`
  - SHA-256: `994c87fb3d590e5aceb8e7e0b6e176001c42017a290a06ca4a508236a52530a1`
- `FILE_LIST.txt`
  - SHA-256: `59b30e31ba8823992f3e9891fd5e318bd631f444cce98d6f61d8c4c38b80ec95`

## Google Drive authority

Folder:
`Gen1recomp/02_Current_Development/Features/Battle_Presentation_Timeline/Source_Snapshots/pmd_idle_battle_sprites_v0.1.95c_20260819`

Drive IDs:
- exact ZIP: `19kcezsRaMtTHQQtA5PoUi0JnonOJJ5Ln`
- `main.lua`: `1Swcwv4rillXZ384FMZPYD8AGwsaVyrvz`
- `manifest.json`: `1CcYD9bXggAoMesBfomcJsOF7t3_FDpmm`
- `FILE_LIST.txt`: `1o5Et3iia0XGWTxn8DEY0JVGIHq50bU6h`
- `SHA256.txt`: `19ZZ6pikqIc4lkENmAzD2ZveUpcy7uI38`

## Battle presentation findings

This exact source already contains a substantial presentation synchronization layer:

- semantic move → PMD action-family mapping;
- `nativeSync` timing state;
- `nativeSfxHold` / `nativeFxHold` behavior;
- direct observation of `battle.animPlaying`;
- hit ownership through `BattleState.applyHitFx`;
- hurt recovery tied to battler HP presentation rather than a generic timer.

The next implementation should therefore converge these existing mechanisms into a single **Battle Presentation Timeline Authority** rather than introduce another independent timer.

Primary P0 objective:

`PMD body action → Gen1Recomp native move animation → move SFX → hit frame → target reaction → recovery → completion`

Secondary P0 objective:

Introduce Gen2/GBC-style colored battle animation presentation on the same timeline, without breaking the existing Gen1Recomp renderer or PMD body-action authority.
