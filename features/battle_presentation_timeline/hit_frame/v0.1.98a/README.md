# PMD v0.1.98a HIT_FRAME Authority I

**Status:** TEST-only candidate. STATIC PASS. Thor runtime + visual acceptance pending.

## Base

Accepted compatibility state:

- `pmd_idle_battle_sprites v0.1.97f`
- `DRAMATIC_SHAPE 1.8.2`
- `thor_battle_ui 0.3.41`

Accepted SHA gate:

- PMD main: `a4870ddea71c5679917275a8444d6451405a0634758767e9f8487d1e0180ca49`
- PMD manifest: `87d9caf6d33d1082c86fa3804422827bb0f5e8437825e14be409c98240015051`
- DS OverworldBattle: `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DS BattleScene: `bca552070e26c9ac6554f8cc387ffb34036a76722b7be9c5d3184974237873cc`
- THOR Battle UI: `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`

## Candidate SHA

- PMD main: `8343074b48a7720b595d74c54a698566e69d0a1e54b15bf455cf1669eea68ece`
- PMD manifest: `ad68bbfb35f3fb79253b5a1427b0817cde67dd7e69db43aefa19b75bf0f07d93`
- Test ZIP: `e7177ae2ac624f7dea85d918888d101a52178438705d2d1ffc495b08b4e4f88d`

Drive test folder: `1GyR8XjUppvtn5SC3EK40kMx7v1u1nU4Y`  
Drive ZIP: `1LBxOF4CCw504sdIpsVO36tjW197q1SsV`

## Scope

This candidate modifies PMD only. DRAMATIC_SHAPE and THOR Battle UI must remain byte-exact.

1. `applyHitFx` is the sole HIT_FRAME latch.
2. Each move execution gets one `hitSequenceId`; each native hit row gets one `hitIndex/hitTotal` owner.
3. Single-hit contact recovery consumes the exact PMD source `hitFrame` latched from the active move row at `applyHitFx`.
4. Multi-hit continuation rows use `motionSyncTiming` for metadata only and must not call `armNativeActionSync` again.
5. `sfxSnap` remains unchanged as legacy visual compatibility, not HIT authority.
6. Timeline IIc, audio-tail, native damage, depth, lighting, shadow, Presentation Overflow and Large Pokémon Presentation Bounds remain sealed.

## Collector hard checks

- duplicate HIT authority = 0
- continuation barrier re-arm = 0
- behavioral contact pose missing = 0
- numeric `ANIM_RELEASE -> HIT` non-zero = 0
- status move false HIT authority = false

Required runtime coverage: Quick Attack, Fury Swipes, Ember, Thundershock, Gust, plus Sand Attack or Thunder Wave. Missing coverage is `INCOMPLETE`, not PASS.

## Promotion rule

Do not merge/promote as accepted Authority until Thor runtime evidence and visual smoke regression pass. Depth/Occlusion work remains closed unless a real regression is observed.
