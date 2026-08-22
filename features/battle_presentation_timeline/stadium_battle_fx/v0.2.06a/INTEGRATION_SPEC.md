# P0 StadiumBattleFX Integration I — PMD v0.2.06a TEST

Base: exact PMD v0.2.04a A3 Formal Authority.

## Direction

Custom GBC move-VFX ownership is removed from PMD rather than hidden behind a setting. StadiumBattleFX 2.1.8 is the external move-effects provider for this integration test.

Upstream StadiumBattleFX release commit: `6965f2535cebaf3151033a5db409d40608ddcc0d`.

StadiumBattleFX and the Pokemon Stadium ROM are not redistributed by this project.

## Removed from PMD

- `gbc_anim_data.lua`
- `assets/gbc_anim/*`
- GBC asset loader/cache
- GBC lifecycle START/HANDOFF/NATIVE_RELEASE/ANIM_RELEASE/HIT/COMPLETE consumer
- GBC native visual suppression wrappers
- GBC background/foreground draw calls
- Custom GBC fallback runtime

## Preserved

- Presentation Timeline
- HIT_FRAME Authority I / engine `applyHitFx` sole HIT latch
- PMD Action Binding Authority I
- Psybeam `beam_release` non-contact semantic
- Tackle safe body route
- Bubble/Bubblebeam projectile routing
- Scratch HANDOFF→authoritative-HIT contact hold
- DRAMATIC_SHAPE 1.8.2 Depth/Occlusion compatibility
- THOR Battle UI 0.3.41 compatibility code
- Large Pokémon presentation rules

## TEST fixture

One free-overworld B press creates one battle-local benchmark with Quick Attack / Ember / Fury Swipes / Surf. This samples contact, projectile, multi-hit and full-screen effects in one run. Second B after return is ONCE_GUARD. Fixture must be removed before any promotion.

## Thor visual gate

- Stadium effects attach to the visible PMD attacker/defender correctly.
- No obvious effect clipping.
- No Custom-GBC/native/Stadium double VFX.
- THOR Battle UI HP/HUD/stage presentation remains visible and non-overlapping.
- Battle Cinematics is intentionally excluded from Integration I.

Formal Authority remains v0.2.04a until this candidate passes runtime + visual acceptance.