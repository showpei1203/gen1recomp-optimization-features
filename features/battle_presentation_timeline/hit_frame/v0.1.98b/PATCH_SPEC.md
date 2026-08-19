# v0.1.98b Patch Spec

Source PMD main SHA: `8343074b48a7720b595d74c54a698566e69d0a1e54b15bf455cf1669eea68ece` (`v0.1.98a`)  
Candidate PMD main SHA: `d424b958571ab18fa456710230a39b46686d6533f7b277987920d83d0c19c67c`

Exact candidate source, v0.1.98a rollback, accepted v0.1.97f rollback, diff, SHA gates and collector are archived in Drive ZIP `1UTfiT7rllz4m_RYTBzykivQm2VaPc2eO`.

## Runtime change

Only the existing `combatMotionPose` `postRecovery` impact-hold branch changes.

Before v0.1.98b, the authoritative pose was returned only while:

`impactRec and elapsed < impactHold`

v0.1.98b adds one pending-delivery latch:

`authorityPosePending = cue.hitAuthority and not cue.hitAuthorityPoseLogged`

and permits the impact pose when:

`impactRec and (elapsed < impactHold or authorityPosePending)`

The pending path delivers the already-latched `impactHitFrame` once on the next actual PMD draw, logs `HIT_AUTH DRAW_GUARANTEE`, then the existing recovery code continues normally.

## Safety properties

- no new timer
- no new native queue barrier
- no repeated `armNativeActionSync`
- no replayed SFX
- no damage/status retiming
- no change to `fireHitFrameAuthority`
- no change to `applyHitFx` wrapper
- no DRAMATIC_SHAPE / THOR file changes
- no depth / lighting / shadow / anchor / large-species changes

## Evidence target

Hard PASS remains:

- duplicate HIT authority = 0
- continuation barrier re-arm = 0
- behavioral pose missing = 0
- numeric `ANIM_RELEASE -> HIT` non-zero = 0
- status false HIT authority = false
- all required benchmark coverage present
- at least one multi-hit sequence observed

Collector additionally reports `DRAW_GUARANTEE_DEFERRED` so a recovered formerly-skipped pose can be distinguished from ordinary same-frame/next-frame pose delivery.

Static validation: **28/28 PASS**. Runtime/visual acceptance pending.
