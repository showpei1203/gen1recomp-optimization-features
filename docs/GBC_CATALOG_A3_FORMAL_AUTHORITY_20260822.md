# GBC Catalog Expansion A3 Formal Authority

Status: FORMAL PASS
Formal runtime version: pmd_idle_battle_sprites v0.2.04a

## Authority chain
Presentation Timeline -> HIT_FRAME Authority I -> PMD Action Binding Authority I -> GBC Colored Move Animation Layer I -> GBC Catalog Expansion A3

## Accepted A3 moves
- Tackle
- Scratch
- Bubble
- Bubblebeam

## Accepted behavior
- Tackle: family=lunge semantics with safe Charge/Attack body source; broken action=lunge body route prohibited.
- Scratch: one coherent Swing/CUT action. At native HANDOFF, PMD source pose is held on the authoritative source hit frame until engine applyHitFx; no second attacker beat.
- Bubble: projectile semantic, contact=false, projectile=true, 3-bubble train.
- Bubblebeam: projectile semantic, contact=false, projectile=true, 9-bubble train followed by target-side WATER deformation; never Surf full-screen curtain.

## Formal promotion proof
- RESULT=PASS
- GBC_LAYER_LOAD=True
- GBC_VFX_ERRORS=0
- GBC_A3_FIXTURE_LOG_LINES=0
- CURRENT_ERROR_FILTER_LINES=0
- HASH_GATE=PASS

Evidence ZIP SHA-256: `dd3f2aa65da2c982137ef31b0b965fea2f405d524a9e0bc606fabc4ad78daeb1`
Drive Evidence ZIP: `1BHoU1hxf10-5ff0Aup2XwynueHmGiM6t`

## Accepted hashes
- main.lua `f9aede365165dcdb014a5d5937bfa47f578d92b464c838577e1c115ef7a02643`
- manifest.json `87c53c38b7ae1cb597a5a34eb1c986c33ace0d03d8eaa17d6a41d02eb16adf9c`
- gbc_anim_data.lua `379686463280b6a967db229fdeb96323502fe87d4e83e3d2f0bc2964eb7121ae`
- promotion package `f1c1c9cfa21a817144528c6000a17c9d664376bad0e85fc55d9ae146c9938b00`

## Promotion cleanliness
The complete TEST-only GBC_A3_FIXTURE block, free-overworld B benchmark hook, fixture state/functions/logging are absent from formal source.

## Batch catalog development rule after A3
Future catalog work defaults to Batch-by-Presentation-Family, not one-move-per-candidate manual testing.

1. Group moves by shared presentation family/renderer semantics.
2. Reused families should prefer declarative per-move parameters over bespoke rendering code.
3. Automated regression must cover every move in each batch: lifecycle, semantic routing, HIT ownership, duplicate/re-arm gates, image load/draw, cleanup and hashes.
4. Human visual acceptance is required for every genuinely new presentation family, bespoke BG/multi-phase/unusual-timing move, automated outlier, and representative samples from reused families.
5. Pure parameterizations of a sealed family do not each require a separate user test cycle unless automation or visual sampling finds an anomaly.
6. Formal promotion is per batch after TEST-only benchmark access is removed and promotion smoke passes.

Water Gun remains deferred until exact water binary source is authoritative.
