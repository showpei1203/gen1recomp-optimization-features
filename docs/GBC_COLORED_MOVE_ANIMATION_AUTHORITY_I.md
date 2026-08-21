# GBC Colored Move Animation Layer I — Formal Runtime Authority

Date: 2026-08-21
Accepted build: `pmd_idle_battle_sprites v0.2.02a`
Status: **FORMAL RUNTIME PASS**

## Authority chain

`Presentation Timeline → HIT_FRAME Authority I → PMD Action Binding Authority I → GBC Colored Move Animation Layer I`

The GBC layer is a visual consumer. It does not own damage timing, status timing, HIT timing, native animation lifecycle, audio-tail, queue barriers, depth, or PMD body ownership.

## Accepted hashes

- main.lua `f574c138ca224ba06fb680fef59b5ff8869f6580da3c84398c3796a2c6d5a65e`
- manifest.json `7e823d33645f82758cda4cf8cc28279a2ffb721031821808233e84e259db3eda`
- gbc_anim_data.lua `b8619c28485ae5293f470ab9f00ed8a914a84fc42616e21d578ab6b904a255f0`
- candidate ZIP `2b6407ada7c09d4383a114a52d43771d76eb458b1ff6666199c1b995d1acc3e0`

Sealed dependencies:
- DRAMATIC_SHAPE OverworldBattle `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DRAMATIC_SHAPE BattleScene `bca552070e26c9ac6554f8cc387ffb34036a76722b7be9c5d3184974237873cc`
- THOR Battle UI `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`

## Promotion evidence

Evidence SHA-256: `5d1802169fdf34e798c373afd1602bf865c56ccdda59d83827bf267635ea27d9`

Hard gates:
- RESULT=PASS
- GBC_LAYER_LOAD=True
- GBC_A2_FIXTURE_LOG_LINES=0
- GBC_VFX_ERRORS=0
- CURRENT_FATAL_LOVE_ANR_ERRORS=0
- HASH_GATE=PASS

Depth smoke retained enemy presentation=(80,96), physical=(80,106), overflow=10 and player legacy-overlay / 3D-shadow-only policy.

## Representative accepted behavior

- Ember: colored projectile benchmark.
- Thundershock: sustained/electric benchmark.
- Thunder Wave: status benchmark with no synthesized damage HIT.
- Quick Attack: speed-line lead-in + authoritative-HIT impact; explicit visual acceptance recorded.
- Fury Swipes: alternating multi-hit CUT presentation; explicit visual acceptance recorded.
- Surf: native-style background water curtain + foreground crest/rise-hold-recede; explicit visual acceptance recorded.
- Psybeam: continuous 4f WAVE stream through authoritative HIT; seamless beam explicit visual acceptance recorded. v0.2.01f changes binding to `beam_release`, `contact=false`, `projectile=true`, with zero attacker contact recovery and HIT_AUTH behavioral=false, removing the runtime path responsible for the one-frame attacker/Pikachu flash. No separate post-f textual visual sentence is claimed.

## Formal cleanliness

v0.2.02a removes the complete TEST-only B fixture, battle-local benchmark clone, fixture one-shot state and fixture logging. Formal builds must not reintroduce these test hooks.

## Native-presentation import rule

Future move imports must inspect at minimum:
- animation script
- background effect
- object / frameset / OAM composition
- waits / loops / cadence
- palette behavior
- source/target semantic ownership

Do not import from raw PNG appearance alone.

## Non-regression

Do not reopen or silently alter HIT_FRAME applyHitFx ownership, Action Binding sequence/barrier rules, damage/status timing, audio-tail ownership, DRAMATIC_SHAPE / THOR integration, Depth/Occlusion / Presentation Overflow, Large Pokémon Presentation Bounds, or species presentation scale.

Next development direction: expand the GBC move catalog from v0.2.02a using isolated test candidates; any temporary test access must be removed before formal promotion.
