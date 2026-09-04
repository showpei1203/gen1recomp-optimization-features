# SoulGold M6X1R2 Final Showdown Presentation Authority

Status: BUILD/STATIC PASS. Runtime promotion requires AYN THOR acceptance.

## Permanent authority chain
M2R5D -> M2R11E -> M2R12G -> M3S1.

The following are non-regression requirements:
- Native visibility and external presentation visibility are separate concepts.
- monbg may hide native OAM without removing the external Showdown body.
- Provider identity is species + sprite generation; ordinary UI command transitions are not provider changes.
- Presentation epoch begins on the authoritative first-visible generation edge.
- Provider animation timing follows ROM/mGBA frames, not Android wall clock.
- x2/y2 remain battler-animation motion authority.
- Player body must not inherit action-menu BOUNCE_MON; native BOUNCE_HEALTHBOX remains.
- Provider-owned native Pokémon pixels must not be copied into monbg/stat BG masks.
- Stat/body/lower UI are composed in native framebuffer coordinates before final display scaling.
- Lower dialogue/menu UI remains final Z authority where applicable.
- Host raw BattleHealthboxInfo stride/offset writes are forbidden.
- Native intro flash, native underlay, gray healthbox/mask ghost edges and teardown suppression regressions are forbidden.
- FRONT rollout and broad roster expansion stay blocked until the current player-BACK runtime gate passes.

## M6X1R2 Android-specific race rule
A bridge sync may not invalidate the last-known-good drawable snapshot merely because the core thread has started writing the next frame. A newly validated bridge frame atomically replaces the cached snapshot. This prevents one-display-frame Showdown loss during Battle command <-> MOVE command transitions.

## Current stat rule
R1's device-space clipping produced visibly segmented/blocky stat presentation. R2 applies the stat presentation to the same Showdown frame/geometry in native mGBA framebuffer space and scales the completed composition once.

## Canonical build
GitHub Actions Run #9: 33864081085
Build head: 6a96944d054bdb15c11a00904986e4c57f78e881
Bridge EWRAM: 0x02002ad4
ROM: 33,554,432 bytes
ROM SHA-256: 9030606040c40e81dff820489dcd9cd57ea4619e7c1a3b5bfeb7e702c9018c0e
SGXP SHA-256: d149baa6e0c3a9cb57a28841f1687c825090f62234a82f5707a588f3d9313ccb
APK SHA-256: 857e88e09e21d0b0e93223f20cd0641c3bebaae3cf9b20ee1f245131104eab07

Run #9 passed the R2 presentation validator, SoulGold build, exact 32 MiB sealing, SGXP build, patched mGBA ARM64, Android contract audit and APK build. Artifact upload passed. Only the final compact-authority Git persistence step failed after upload because generated_bridge.h still contained the old pre-R2 address; the branch has since been corrected to 0x02002ad4.

## Next runtime gate
Sprigatito player BACK only:
1. Repeated Battle command <-> MOVE command transitions have zero flicker/native flash.
2. Stat decrease is visually continuous, with no segmented/blocky strip artifact.
3. First visible battler frame is Showdown.
4. HUD/dialogue/monbg/stat layering remains correct.
5. Registry/audio sealed metrics remain passing.
