# PMD HIT_FRAME Authority I

**Status:** Runtime PASS / Formal Authority  
**Accepted build:** `pmd_idle_battle_sprites v0.1.98b`  
**Compatibility base:** `DRAMATIC_SHAPE 1.8.2` × `thor_battle_ui 0.3.41`

## Accepted hashes

- PMD `main.lua`: `d424b958571ab18fa456710230a39b46686d6533f7b277987920d83d0c19c67c`
- PMD `manifest.json`: `798346ed03a8a02ad184c769502e23c10a828bd9e81025a8eaf297e94ae415d6`
- Candidate ZIP: `c673f8a1cdb17648325e90882f035942a1fa49f91172bfc7c446d52df0979565`
- PASS Evidence ZIP: `9e4129dd1b30f036498b0c638dc5001626c6362595fdc4802a751687aece6adb`
- DRAMATIC_SHAPE `OverworldBattle.lua`: `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DRAMATIC_SHAPE `BattleScene.lua`: `bca552070e26c9ac6554f8cc387ffb34036a76722b7be9c5d3184974237873cc`
- THOR Battle UI `main.lua`: `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`

## Authority

1. Engine `applyHitFx` is the sole authoritative `HIT_FRAME` latch.
2. Native damage/status resolution remains engine-owned. PMD binds presentation to the engine hit event and does not replace damage timing.
3. Each native hit row owns at most one HIT authority record.
4. Multi-hit uses one sequence with row-level `hitIndex/hitTotal`. Continuation rows must not re-arm the native presentation barrier.
5. A behavioral contact hit must deliver the latched PMD source `hitFrame` at least once on an actual PMD draw.
6. If battle-frame elapsed exceeds the short impact hold before PMD is drawn, Draw Guarantee delivers the latched source `hitFrame` exactly once on the next real PMD draw. This is delivery ownership, not a new timer.
7. `sfxSnap` remains legacy compatibility only and is not HIT authority.
8. Timeline IIc diagnostic tracing remains compatible with this Authority.
9. Observed damaging benchmarks preserve `HIT = ANIM_RELEASE` for the tested path.

## Thor PASS evidence

Collector result: `PASS`

- `HIT_AUTH_FIRES=16`
- `BEHAVIORAL_SINGLE_CONTACT=11`
- `POSE_PROOFS=11`
- `DRAW_GUARANTEE_DEFERRED=3`
- `DUPLICATE_HIT_AUTHORITY=0`
- `CONTINUATION_BARRIER_REARM=0`
- `BEHAVIORAL_POSE_MISSING=0`
- `ANIM_RELEASE_TO_HIT_NONZERO=0`
- `MULTI_HIT_ROWS_SEEN=3`
- `STATUS_FALSE_HIT_AUTH=False`

Coverage PASS:
- Quick Attack
- Fury Swipes
- Ember
- Thundershock
- Gust
- status-negative benchmark

Draw Guarantee proof retained in the same evidence buffer:
- Gust seq11: HIT 736 -> POSE 737 (+1f)
- Gust seq13: HIT 1351 -> POSE 1352 (+1f)
- Gust seq18: HIT 3456 -> POSE 3458 (+2f)

Final promotion proof:
- Ember produced `HIT_AUTH FIRE`, owner=`applyHitFx`, `fromAnimRelease=0`, `duplicate=false`, `continuationBarrierRearm=false`.
- Collector `COVERAGE EMBER=True`.

## Safety / compatibility

- No new application Lua error.
- No `FATAL EXCEPTION`.
- No application ANR.
- DRAMATIC_SHAPE and THOR files remain byte-exact.
- Depth/Occlusion Authority remains sealed and unchanged.
- Presentation Authority remains separate from Physical Feet Authority.
- Player BACK SPRITES policy remains visible legacy overlay + hidden 3D shadow silhouette.
- Large Pokémon Expanded Presentation Bounds remain sealed: `BATTLE_SCALE=0.90`, `PLAYER_Y_SHIFT=6`, `ENEMY_Y_SHIFT=10`, `>=90px` enemy giant bypasses conservative fit/shrink, native scale/overflow preserved, non-bird giant `+6X/-4Y`, Articuno/Zapdos/Moltres shared approved anchor.

## Drive evidence

- v0.1.98b Test Folder: `15HKvj8ByORCz7Hp6piPKbRj1p8GWdo2Q`
- PASS Evidence Folder: `1dmLcX9PHRyUDRmJYnd589qWQ7H6tGDYS`
- PASS Evidence ZIP: `1uv6keWQ-6MZAS6fAPov1bEh6oJpLy5ms`
- Drive Formal Authority Doc: `12zMLx72dnVtRZwsTLbGrc1IJxSyW-EqVYyA9VKtuBcI`

## Next mainline

Proceed to **PMD Action Binding**. Validate melee/contact, projectile, multi-hit, long-SFX/sustained, full-screen/area, and status/self families against this same HIT_FRAME Authority. The Gen2/GBC Colored Move Animation Layer comes only after Action Binding is stable and must consume the same Presentation Timeline rather than create a separate clock.
