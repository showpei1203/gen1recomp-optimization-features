# SoulGold M5A2 Original Action Participant Authority

Date: 2026-09-02

## Decision
Action Presentation remains original-first. SoulGold continues to own action timing, move effects, sound, native battler visibility, position and affine transforms. The external Showdown visual does not invent attack choreography, restart its animation epoch, or create a second clock.

## Why M5A2 exists
M5A1 used the global `gAnimScriptActive` flag as the action observation window. That is correct for timing, but it is global: every visible battler could be logged as if it were an action participant. M5A2 removes that semantic ambiguity by reading SoulGold's own `gBattleAnimAttacker` and `gBattleAnimTarget` variables.

## Implementation
- `gAnimScriptActive` remains the action-window authority.
- `gBattleAnimAttacker` / `gBattleAnimTarget` identify canonical action participants.
- Self-target actions are represented as one battler with attacker+target role, never as a fabricated second actor.
- A non-participant battler can only enter action telemetry if its native proxy actually moves/affines; it is marked auxiliary native motion, not attacker/target.
- Rendering behavior is unchanged from M5A1: current Showdown clip is preserved and native proxy transform/visibility is mirrored.
- No animation epoch reset, no forced attack clip, no second gameplay/presentation clock.

## Runtime telemetry
- `SHOWDOWN_ACTION_CONTEXT`
- `SHOWDOWN_ACTION_BEGIN`
- `SHOWDOWN_ACTION_NATIVE_BODY_MOTION`
- `SHOWDOWN_ACTION_END`

## New regression rules
- **R-SD-114** ACTION_PARTICIPANTS_USE_SOULGOLD_GBATTLEANIM_ATTACKER_TARGET_AUTHORITY
- **R-SD-115** NONPARTICIPANTS_ARE_NOT_LABELLED_ATTACKER_TARGET_WITHOUT_NATIVE_MOTION
- **R-SD-116** ACTION_PARTICIPANT_OBSERVATION_ENDS_WITH_NATIVE_WINDOW_NO_CLIP_REBIND
- **R-SD-117** SELF_TARGET_ACTIONS_SHARE_ONE_CANONICAL_PARTICIPANT_NO_FAKE_SECOND_ACTOR
- **R-SD-118** M5A2_RUNTIME_SYMBOL_AUTHORITY_REQUIRES_ACTION_PARTICIPANTS
- **R-SD-119** ACTIVE_M5A2_LAUNCHER_DECLARED_STAGE_EXISTS_IN_PACKAGE

## Carry-forward
All accepted M3 switch / HUD / double-lab / shadow / scale rules remain active. The enemy double formation HUD-avoidance shift from M5A0 is retained.

## Promotion rule
M5A2 is a semantic and telemetry correctness step. It does not claim runtime Action Presentation PASS until normal-play evidence exists. If representative normal play shows no defect, M5 should be sealed without adding extra choreography.
