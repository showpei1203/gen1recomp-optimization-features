# PMD v0.1.98b HIT_FRAME Authority I Draw Guarantee

**Status:** TEST-only candidate. STATIC PASS. Thor runtime + visual acceptance pending.

## Source

Direct continuation from Thor-tested `v0.1.98a`.

v0.1.98a proved:

- 21 HIT_AUTH fires
- duplicate HIT authority = 0
- continuation barrier re-arm = 0
- all numeric `ANIM_RELEASE -> HIT` deltas = 0f
- all required benchmark coverage present

Its only hard failure was 3 missing behavioral `HIT_AUTH POSE` proofs: one Quick Attack and two Gust occurrences.

## Root cause

`applyHitFx` correctly latched the source hit frame, but the existing `postRecovery` impact hold used battle-frame elapsed. If battle frames advanced while the PMD battler was not actually drawn, the short hold could expire before the next `combatMotionPose` call, skipping the authoritative pose entirely.

## v0.1.98b change

When a behavioral HIT authority is pending and no authority pose has yet been delivered, the next actual PMD draw returns the latched source hit frame exactly once even if the original impact hold has already expired. The normal recovery path resumes immediately afterward.

This adds no new timer and does not retime native animation, audio, damage, or queue ownership.

## Candidate SHA

- PMD main: `d424b958571ab18fa456710230a39b46686d6533f7b277987920d83d0c19c67c`
- PMD manifest: `798346ed03a8a02ad184c769502e23c10a828bd9e81025a8eaf297e94ae415d6`
- Test ZIP: `c673f8a1cdb17648325e90882f035942a1fa49f91172bfc7c446d52df0979565`

Drive test folder: `15HKvj8ByORCz7Hp6piPKbRj1p8GWdo2Q`  
Drive ZIP: `1UTfiT7rllz4m_RYTBzykivQm2VaPc2eO`

## Explicitly unchanged

- `fireHitFrameAuthority`
- `BattleState.applyHitFx` wrapper
- `moveTimingExceptions`
- `motionSyncTiming`
- `armNativeActionSync`
- `playAnimSound`
- audio-tail lifecycle
- `sfxSnap` legacy compatibility
- multi-hit one-row/one-owner safety
- DRAMATIC_SHAPE / THOR Battle UI
- Presentation vs Physical Feet Authority
- Presentation Overflow
- Large Pokémon Expanded Battle Presentation Bounds

Static validation: **28/28 PASS**.

Do not promote until Thor runtime evidence returns `BEHAVIORAL_POSE_MISSING=0` with the same ownership, multi-hit, timeline, status, and render invariants intact.
