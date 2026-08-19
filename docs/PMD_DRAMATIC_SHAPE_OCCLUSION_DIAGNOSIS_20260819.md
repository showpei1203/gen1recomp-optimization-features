# PMD × DRAMATIC_SHAPE Battle Occlusion Diagnosis

Date: 2026-08-19

## Finding

The reported tree/foreground occlusion problem is **not** a Presentation Timeline I/II regression.

Byte-exact comparison:

- Formal PMD source authority: `pmd_idle_battle_sprites v0.1.95c`
- v0.1.95c `main.lua` SHA-256: `11a1b8c3f8cdc098a8f7792b4b5fcb9557f62400999685dcc9337eb893a6f883`
- Current tested PMD candidate: `v0.1.96c`
- v0.1.96c `main.lua` SHA-256: `1169cf78409c9b01e7a06d42e3a91b1702e2a95a82f80b736d2a5a7b7d31556b`

The `battle.overlay` draw-order block is functionally unchanged between the two versions. Both versions draw PMD switch/body sprites as a screen-space overlay and contain no z/depth/occlusion integration. The v0.1.95c source itself states that PMD sprites are drawn later in `battle.overlay`.

## Exact DRAMATIC_SHAPE 1.8.2 source snapshot

Thor exact snapshot captured on 2026-08-19:

- ZIP: `GEN1RECOMP_DRAMATIC_SHAPE_EXACT_SOURCE_20260819_201011.zip`
- ZIP SHA-256: `5a2b6db26bda3a0307b824e226b4126af89a2ef6d6ec8d39f8566c5ba7a9984c`
- Drive ZIP ID: `12H_VEz4gUzbD-6mvKEotryjB7i48UOxI`
- Snapshot folder ID: `1MuzkDSY3xfOZPFMq2u5_3nPekNwrKo_8`
- exact `main.lua` SHA-256: `f8fb8616f30c3a9a7be16dce4b48e706c3d97dedfccbb9d0e6a0e8be56471ac1`
- exact `manifest.json` SHA-256: `b8ef6c5abc8c876fb15171877b27ef2b02728de49875a9e1fa8885e8601b54b2`
- manifest version: `1.8.2`
- priority: `100`
- permission: `engine_internals`

The exact `main.lua` independently confirms the intended 3D battle path:

- `OverworldBattle.install()` owns the engine seams around `OverworldState:pushBattle`, `BattleState:draw`, and `BattleState:drawHUDs`.
- the `pokemon.sprite` hook is explicitly documented as the seam used for every battle Pokémon picture, including Transform.
- `VoxelScene.render(...)` is the depth-buffered 3D world render path.

This is directly incompatible with PMD's current replacement strategy, where the PMD v0.1.95c source explicitly draws the replacement body later from `battle.overlay`.

Important snapshot limitation: the first source-grab package captured `manifest.json` and `main.lua`, but `SOURCE_DUMP.txt` and `SOURCE_INDEX_AND_SHA256.txt` were zero bytes. Therefore no integration patch may be built from guessed library code. `lib/OverworldBattle.lua`, `Voxel3D.lua`, `VoxelScene.lua`, and supporting depth/geometry libraries must be direct-cat captured from Thor first.

## Runtime context

Current evidence confirms:

- `DRAMATIC_SHAPE 1.8.2` loaded
- `pmd_idle_battle_sprites 0.1.96c` loaded
- `thor_battle_ui` reports DRAMATIC_SHAPE 3D battle compatibility enabled

Evidence ZIP:
`GEN1RECOMP_PRESENTATION_TIMELINE_IIc_EVIDENCE_20260819_200104.zip`

SHA-256:
`0420ce211035f86584a1271da20232f7b16d862bf815184c0f4c93b045b3786a`

Drive evidence ID: `1OBxDEWpLRjgfSj04beGNXvraJ1hl5nK7`
Drive diagnosis ID: `1tqwHgGOSDP3DfXw-Shv_OkkwbvQmfiww`

## Classification

`PMD × DRAMATIC_SHAPE Integration Defect`

The PMD renderer replaces the native battler with a 2D overlay. DRAMATIC_SHAPE's battle system is depth-buffer based. A screen-space overlay does not naturally participate in tree/building occlusion.

## Preferred fix

Do **not** mix this into Presentation Timeline II.

Create a dedicated integration candidate that feeds the animated PMD frame into DRAMATIC_SHAPE's per-side battle texture / world billboard path so the battler participates in the 3D depth buffer.

Fallback only if that path is unavailable: use a DRAMATIC_SHAPE foreground/depth occlusion composite after PMD draw.

Avoid hard-coded tree masks, map-specific clip rectangles, or manual y-sort hacks.

## Timeline IIc side result

The same evidence run confirms the IIc trace-integrity fix is working: damaging HIT records now contain concrete `fromHandoff`, `fromLastSfx`, `fromAnimDone`, and `fromAnimRelease` deltas, with observed damaging moves still resolving at `fromAnimRelease=0`.
