# PMD v0.1.98b HIT_FRAME Authority I

**Status:** Runtime PASS / Formal Authority

v0.1.98b promotes the engine `applyHitFx` event as the sole authoritative HIT_FRAME latch for the tested PMD battle presentation path while preserving all accepted v0.1.97f depth/occlusion compatibility invariants.

## Accepted behavior

- one HIT authority per native hit row;
- multi-hit sequence keeps row ownership without continuation barrier re-arm;
- behavioral contact hits deliver the latched PMD source `hitFrame` on an actual PMD draw;
- Draw Guarantee supplies that authoritative pose exactly once on the next actual draw if battle-frame elapsed already exceeded the short impact hold;
- `sfxSnap` remains legacy compatibility, not HIT authority;
- native damage, native animation, audio lifecycle, DRAMATIC_SHAPE depth, THOR UI wrappers and Large Pokémon presentation bounds remain unchanged.

## Accepted hashes

- PMD `main.lua`: `d424b958571ab18fa456710230a39b46686d6533f7b277987920d83d0c19c67c`
- PMD `manifest.json`: `798346ed03a8a02ad184c769502e23c10a828bd9e81025a8eaf297e94ae415d6`
- Candidate ZIP: `c673f8a1cdb17648325e90882f035942a1fa49f91172bfc7c446d52df0979565`
- PASS Evidence ZIP: `9e4129dd1b30f036498b0c638dc5001626c6362595fdc4802a751687aece6adb`

## Thor final result

`RESULT=PASS`

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

Coverage PASS: Quick Attack, Fury Swipes, Ember, Thundershock, Gust, status-negative.

See `docs/PMD_HIT_FRAME_AUTHORITY_I.md` and `THOR_PASS_20260820_064038.md`.

## Next mainline

PMD Action Binding across melee/contact, projectile, multi-hit, long-SFX/sustained, full-screen/area and status/self families. The Gen2/GBC Colored Move Animation Layer must consume this same Presentation Timeline and may not introduce an independent timing clock.
