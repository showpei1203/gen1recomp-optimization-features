# v0.1.98b HIT_FRAME Authority I — Accepted Patch Spec

## Status

Runtime PASS / Formal Authority.

## Behavioral contract

- `applyHitFx` is the sole HIT_FRAME latch.
- Native damage and native animation/audio timing remain engine-owned.
- Each native hit row owns at most one HIT authority record.
- Multi-hit continuation rows never re-arm the native presentation barrier.
- Behavioral contact HIT authority must render the latched source `hitFrame` at least once.
- Draw Guarantee may defer that pose until the next actual PMD draw when the short battle-frame impact window expired before draw. It delivers exactly once and does not create a new timer.
- `sfxSnap` remains legacy visual compatibility only.

## Runtime PASS gates

- duplicate HIT authority = 0
- continuation barrier re-arm = 0
- behavioral pose missing = 0
- numeric `ANIM_RELEASE -> HIT` non-zero = 0
- status false HIT authority = false
- benchmark coverage: Quick Attack, Fury Swipes, Ember, Thundershock, Gust, status-negative all true

## Sealed compatibility

No modification or rollback of accepted DRAMATIC_SHAPE / THOR depth integration, Presentation Overflow, player BACK SPRITES shadow policy, Presentation vs Physical Feet Authority separation, or Large Pokémon Expanded Presentation Bounds.

Accepted PMD main SHA: `d424b958571ab18fa456710230a39b46686d6533f7b277987920d83d0c19c67c`.

See `docs/PMD_HIT_FRAME_AUTHORITY_I.md` for the formal authority and `THOR_PASS_20260820_064038.md` for final evidence.
