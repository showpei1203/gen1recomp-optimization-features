# GBC-A1 v0.2.00a Runtime Patch Spec

Status: TEST-only / Thor runtime + visual evidence pending
Base: pmd_idle_battle_sprites v0.1.99b Action Binding Authority I

## Scope
Adds an additive colored GBC-derived VFX consumer for EMBER, THUNDERSHOCK, and THUNDER_WAVE. Existing native move animation remains visible in A1.

## Ownership
Authority chain remains:
Presentation Timeline -> HIT_FRAME -> PMD Action Binding -> GBC VFX.

GBC code does not own damage, HIT, queue barrier, native AnimPlayer lifetime, SFX/audio-tail, PMD body timing, depth, or species scale.

## Runtime files
- pmd_idle_battle_sprites/main.lua
- pmd_idle_battle_sprites/manifest.json
- pmd_idle_battle_sprites/gbc_anim_data.lua
- assets/gbc_anim/fire_red.png
- assets/gbc_anim/lightning_yellow.png
- assets/gbc_anim/explosion_gray.png

## Event adapters
The GBC consumer observes existing Action Binding lifecycle events: START, HANDOFF, NATIVE_RELEASE, ANIM_RELEASE, HIT, COMPLETE.

- Damage-move visual HIT is recorded only when existing Action Binding HIT fires.
- THUNDER_WAVE does not synthesize a GBC HIT.
- GBC-specific failures are fail-open: the colored layer disables itself and sealed native presentation remains active.

## Anchors / draw order
- Recent PMD legacy screen-space presentation centers are cached as visual anchors.
- Fallback coordinates use approved presentation composition, not DRAMATIC_SHAPE physical-feet coordinates.
- GBC VFX draws above PMD body and before existing battle.drawAnimLayer.
- No DRAMATIC_SHAPE or THOR file is modified.

## A1 visual definitions
- EMBER: three red/orange 8px projectiles travel attacker->target; authoritative HIT produces a short burst.
- THUNDERSHOCK: gray core plus yellow lightning objects around target through sustained presentation.
- THUNDER_WAVE: expanding/pulsing yellow lightning ring, no damage HIT.

## Promotion gate
Static validation is necessary but insufficient. Thor must prove:
- no GBC_VFX ERROR;
- Ember START/HANDOFF/DRAW/HIT/COMPLETE;
- Thundershock START/HANDOFF/DRAW/HIT/COMPLETE;
- Thunder Wave START/HANDOFF/DRAW/ANIM_RELEASE/COMPLETE with no GBC HIT;
- sealed ACTION_BIND/HIT_AUTH hard gates remain zero;
- no depth/UI/body regression;
- visual acceptance is recorded separately from runtime PASS.
