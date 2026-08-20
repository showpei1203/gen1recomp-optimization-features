# GBC-A2.1 v0.2.01c Native Presentation Reconstruction

Status: TEST-only candidate specification
Date: 2026-08-21
Runtime base: exact PMD v0.2.01b

## Purpose
v0.2.01b proved the A2 event/lifecycle integration but user visual review showed that a move can be runtime-correct and still be visually unlike Pokémon Crystal. v0.2.01c therefore reconstructs the **presentation grammar**, not merely the source tiles.

Authority remains:
Presentation Timeline → HIT_FRAME Authority → PMD Action Binding → GBC VFX consumer.
No GBC effect owns damage, HIT, queue/barrier, native animation, audio-tail, PMD body, depth, or species scale.

## Surf
Crystal's `BattleAnim_Surf` combines two independent visual layers:
1. `BATTLE_BG_EFFECT_SURF` background deformation.
2. One `BATTLE_ANIM_OBJ_SURF` object using BUBBLE graphics.

The Surf object begins around `(88,104)`, rises roughly one logical pixel per frame until y≈8, holds until the script's 128f loop ends, then descends roughly two pixels per frame toward y≈112 after `anim_incobj`. The object uses OAM set 22: 22 8x8 sprites spanning about 176 logical pixels, with BUBBLE vtile base 9 and local tiles 0..3.

v0.2.01c reconstruction:
- background pass before PMD battlers: continuous blue water curtain from immediately below the crest to field bottom;
- ±2px rotating scanline bands approximate Crystal `InitSurfWaves` background deformation;
- foreground pass after battlers: OAM22-inspired 22-tile BUBBLE crest;
- rise/hold/fall follows native 104→8 / hold-to-128 / 2px-per-frame fall toward 112;
- native-like sine bob follows the object function's amplitude-$10 behavior;
- existing authoritative HIT timing is not retimed. v0.2.01b Thor evidence measured HANDOFF→HIT≈182f, already closely matching the native Surf presentation duration.

Required proof:
`SURF_CURTAIN`, `SURF_CREST`, `SURF_RISE`, `SURF_HIT_DRAW`.

## Quick Attack
Crystal hides the user, emits six SPEED_LINE objects, waits 12 frames, then emits the HIT object and shows the user again.

v0.2.01c keeps PMD body ownership unchanged but reconstructs:
- six SPEED-derived golden line objects during the first 12f after HANDOFF;
- compact HIT effect only at authoritative HIT.

Pre-HIT speed lines are expected. Only `QUICK_ATTACK_IMPACT` is forbidden before authoritative HIT.

Required proof:
`QUICK_ATTACK_SPEED_LINES`, `QUICK_ATTACK_IMPACT`, impact frame >= HIT frame.

## Fury Swipes
Crystal emits three CUT_DOWN_LEFT objects per hit; alternate parameter rows emit three CUT_DOWN_RIGHT objects.

v0.2.01c:
- each authoritative hit row displays three target-relative slash objects;
- direction alternates by hit index;
- continuation rows remain allowed to omit HANDOFF and must never re-arm the native barrier.

Required proof:
At least two rows and at least two `FURY_SWIPES_TRIPLE_SLASH` events in the benchmark.

## Psybeam
Crystal cycles object/background palettes and emits 10 WAVE objects at 4-frame intervals, then waits 48 frames.

v0.2.01c:
- 10 foreground psychic wave pulses, 4f apart;
- subtle background gray/yellow vs inverted-inspired color cycling during the native presentation window;
- final target burst remains authoritative-HIT-owned;
- v0.2.01b's 192f pending-HIT grace remains because Thor measured HANDOFF→HIT≈161f.

Required proof:
`PSYBEAM_PULSE_TRAIN`, `PSYBEAM_PALETTE_CYCLE`, `PSYBEAM_HIT_DRAW`.

## TEST fixture
The existing one-shot free-overworld B fixture remains in this TEST build only:
- first valid free-overworld B starts one isolated benchmark battle;
- battle-local clone with Quick Attack / Fury Swipes / Psybeam / Surf;
- no persistent party move/HP/status writes;
- second B after fixture returns must log ONCE_GUARD and must not start another fixture.

**Formal release hard gate:** delete the complete `GBC_A2_FIXTURE` block, B hook, state, and fixture logging before promotion.
