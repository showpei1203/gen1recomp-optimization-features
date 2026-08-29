# Pokémon SoulGold PMD Animated Prototype — G4F Spatial Ownership Handoff

Date: 2026-08-29
Branch: `feature/pmd-portable-battle-framework`

## New cross-project runtime evidence

A separate PMD integration lane reproduced and fixed the same apparent player-side vertical bob/sink symptom using Sprigatito as the player battler.

Observed behavior in that lane:
1. the player battler and its HP/status box moved together;
2. the bottom battle UI stayed fixed;
3. the successful ordering was `AnimateSprites -> presentation spatial ownership -> BuildOamBuffer`;
4. while the PMD/Showdown body owned idle presentation, both battler native `x2/y2` and healthbox native offset were neutralized back to their fixed positions.

This changes the SoulGold diagnosis. The unresolved Cyndaquil ambient ~1px sink must no longer be treated primarily as PMDCollab frame-anchor geometry. The stronger hypothesis is a native spatial-ownership leak that survives `AnimateSprites()` and affects the battler plus healthbox family before OAM capture.

The exact patch from the other lane is still pending upload and must be compared before this is promoted as final root cause.

## Pinned SoulGold source evidence

SoulGold pin: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`.

`battle_interface.c` defines the healthbox family as three sprites:
- main/left healthbox: `gHealthboxSpriteIds[battler]`
- right healthbox half: `gSprites[main].oam.affineParam`
- health bar sprite: `gSprites[main].hMain_HealthBarSpriteId`

The right healthbox callback copies `x2/y2` from the main healthbox. The health-bar callback likewise copies the main healthbox `x2/y2`.

Therefore, because `AnimateSprites()` has already run before the PMD presentation hook, resetting only the main healthbox after `AnimateSprites()` is insufficient for the current frame. A SoulGold post-AnimateSprites neutralizer must write the full already-animated family for that frame:
- battler body sprite `x2/y2`
- main healthbox `x2/y2`
- right healthbox half `x2/y2`
- health bar sprite `x2/y2`

This must occur before `BuildOamBuffer()`.

## Candidate ownership rule

Only neutralize native spatial offsets while PMD owns a stationary presentation state.

Eligible candidate states:
- HOME
- ambient Idle/Walk/Nod/Rotate when no native spatial action owns the battler
- persistent Sleep / EventSleep / Wake only when their current ownership policy allows PMD presentation and no native move spatial owner is active

Do NOT neutralize during:
- native move spatial ownership (`sPmdNativeSpatialOwnership[battler] == TRUE`)
- native send-out / switch / return-to-ball choreography
- native faint choreography
- reactive/native movement that PMD explicitly chose to preserve
- healthbox slide-in/out or other healthbox-owned transition windows

Hurt requires explicit review: the PMD body owns Hurt pixels, but SoulGold healthbox hit feedback must remain native. Any neutralization must preserve healthbox hit-feedback semantics.

## Ordering authority

Preserve the proven G3R4B insertion point:

`AnimateSprites()`
`-> PmdSoulGoldPrototype_Tick()` / PMD presentation ownership
`-> stationary-spatial neutralization when eligible`
`-> BuildOamBuffer()`
`-> RunTextPrinters()`
`-> UpdatePaletteFade()`
`-> RunTasks()`

Do not move PMD correction after `BuildOamBuffer()`.

## G4F blocker

Do not activate the 901-species single-OBJ roster globally until this spatial-ownership issue is structurally resolved. Scaling first would replicate the same player-side offset defect across the generated roster.

Current corrected full-roster geometry authority remains:
- 901 species: lossless single-OBJ on both sides
- 25 species: multi-OBJ required
- 99 species: native fallback due missing/invalid core PMD source

Fallback rule remains unchanged: missing/invalid/unhandled PMD source uses the original SoulGold battler sprite.

## Next implementation sequence

1. Receive and inspect the exact successful S1E spatial-ownership patch from the other project.
2. Map its battler/healthbox logic to pinned SoulGold source semantics, not by blind textual copy.
3. Implement a SoulGold `PmdSoulGold_ApplyStationarySpatialOwnership()` equivalent at the G3R4B post-`AnimateSprites()` / pre-`BuildOamBuffer()` point.
4. Neutralize the entire healthbox family for the already-animated frame, not only the main healthbox.
5. Add CI source invariants proving native move spatial ownership bypasses neutralization.
6. Preserve all existing move/Hurt/sendout/switch choreography.
7. Build a ROM and mark runtime visual status PENDING until later device/video acceptance.
8. Only after this gate, continue G4F codec runtime loader and generated 901-species activation.

## Known defect status

`Cyndaquil ambient single-frame ~1px downward sink`

Old status: `DEFERRED_ROOT_CAUSE_UNRESOLVED`

New status: `DEFERRED_STRONG_NATIVE_SPATIAL_OWNERSHIP_HYPOTHESIS_PENDING_EXACT_PATCH_CROSSCHECK`

Do not claim fixed until SoulGold runtime evidence confirms battler and healthbox remain stationary while PMD owns idle presentation.
