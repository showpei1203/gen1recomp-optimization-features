# v0.1.98a Thor Evidence Result

**Status:** Runtime trace FAIL due to 3 missing behavioral pose proofs. HIT ownership itself remains healthy.

## Evidence

Drive Evidence folder: `1uh_VS26HXQ4Y_WO7BFvz2IhuQ9Trg3E7`  
Drive Evidence ZIP: `1-oS6Uc47o0Y79RB8dhKMTOyTRH7NWwge`

Collector summary:

- `RESULT=FAIL`
- `HIT_AUTH_FIRES=21`
- `BEHAVIORAL_SINGLE_CONTACT=15`
- `POSE_PROOFS=12`
- `DUPLICATE_HIT_AUTHORITY=0`
- `CONTINUATION_BARRIER_REARM=0`
- `BEHAVIORAL_POSE_MISSING=3`
- `ANIM_RELEASE_TO_HIT_NONZERO=0`
- `MULTI_HIT_ROWS_SEEN=2`
- all required benchmark coverage present
- `STATUS_FALSE_HIT_AUTH=False`

Missing pose proofs:

1. Quick Attack, HIT_AUTH key `15:1`
2. Gust, HIT_AUTH key `22:1`
3. Gust, HIT_AUTH key `24:1`

## Classification

- No duplicate HIT authority.
- No continuation native-barrier re-arm.
- All numeric `ANIM_RELEASE -> HIT` deltas remain `0f`.
- No new app Lua/FATAL/ANR evidence.
- Accepted DRAMATIC_SHAPE and THOR Battle UI hashes remained exact.
- Depth evidence retained enemy presentation `(80,96)`, physical `(80,106)`, and player legacy-overlay/shadow-only policy.

## Root cause

The authoritative source hit frame is stored correctly at `applyHitFx`, but the existing post-recovery impact hold is battle-frame based. If battle frames advance while the PMD battler is not actually requested for drawing, the short hold can expire before a real `combatMotionPose` draw occurs. HIT authority is latched, but the authoritative source hit frame is not guaranteed to be shown once.

Follow-up candidate: `v0.1.98b` Draw Guarantee.
