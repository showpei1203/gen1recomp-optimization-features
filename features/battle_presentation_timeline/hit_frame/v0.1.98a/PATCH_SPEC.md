# v0.1.98a Patch Spec

Base PMD main SHA: `a4870ddea71c5679917275a8444d6451405a0634758767e9f8487d1e0180ca49`  
Candidate PMD main SHA: `8343074b48a7720b595d74c54a698566e69d0a1e54b15bf455cf1669eea68ece`

Exact full candidate source, rollback, diff, SHA gate and collector are archived in Drive test ZIP `1LBxOF4CCw504sdIpsVO36tjW197q1SsV`.

## Source changes

1. `startAttackerRecovery`
   - carry `impactHitFrame`, HIT authority frame/sequence/index/total on the existing recovery cue.
   - no new timer.

2. `Volatile.fireHitFrameAuthority`
   - called from `applyHitFx` after native hit processing begins.
   - one key per `sequenceId:hitIndex`.
   - persistent per-battle duplicate latch.
   - logs `HIT_AUTH FIRE` with `behavioral`, `duplicate`, `continuationBarrierRearm`, and `fromAnimRelease`.

3. move queue tagging
   - one `pmdHitSequenceId` per move execution.
   - each native animation row gets `pmdHitIndex/pmdHitTotal`.

4. `BattleState.updateQueue`
   - first/single row may use existing `armNativeActionSync` exactly as before.
   - multi-hit continuation obtains `motionSyncTiming` metadata only.
   - continuation never re-arms the native handoff barrier.

5. `BattleState.applyHitFx`
   - invokes HIT authority latch.
   - passes authoritative source hitFrame metadata into existing impact/recovery presentation.
   - native damage/hit execution remains owned by the original engine function.

6. `combatMotionPose`
   - single-hit contact impact hold prefers the source hitFrame latched by HIT authority.
   - logs one `HIT_AUTH POSE` proof for the authoritative contact pose.

## Explicitly unchanged

- `moveTimingExceptions`
- `motionSyncTiming`
- `armNativeActionSync`
- `playAnimSound`
- audio-tail lifecycle
- `sfxSnap` values and behavior
- battle overlay/render tail
- DRAMATIC_SHAPE files
- THOR Battle UI files
- BATTLE_SCALE / PLAYER_Y_SHIFT / ENEMY_Y_SHIFT
- Presentation/Physical Feet separation
- Presentation Overflow depth policy
- Large Pokémon expanded bounds

Static validation: 19/19 PASS; Lua 5.4 parser load PASS. Runtime/visual acceptance pending.
