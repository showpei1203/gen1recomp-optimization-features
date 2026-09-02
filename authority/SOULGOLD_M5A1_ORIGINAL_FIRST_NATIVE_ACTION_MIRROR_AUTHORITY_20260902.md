# SOULGOLD M5A1 ORIGINAL-FIRST NATIVE ACTION MIRROR AUTHORITY — 2026-09-02

## User-approved direction
Action Presentation should stay faithful to the original SoulGold presentation.
The external Showdown sprite is not allowed to invent a separate attack choreography merely because an animated asset exists.

## Core rule
**SoulGold owns the action. Showdown mirrors the body.**

SoulGold remains authority for:
- action start/end timing,
- move animation and visual effects,
- sound timing,
- native battler displacement,
- x/y/x2/y2 motion,
- affine scale/rotation,
- visibility,
- hit/damage/gameplay timing.

The Showdown overlay only mirrors the native proxy transform already produced by SoulGold.

## Clip policy
M5A1 deliberately does NOT bind a forced attack clip.
- Keep the currently loaded Showdown front/back clip.
- Do not restart its animation epoch when an action begins.
- Do not substitute an action clip solely because `gAnimScriptActive` became true.
- If SoulGold does not move/affine the native battler, the Showdown body also does not invent body motion.

This avoids a second visual choreography that can drift away from move effects and sound.

## Existing foundation retained
- `gAnimScriptActive` remains the observation window.
- native proxy x/y/x2/y2/affine remains transform authority.
- M3 withdraw/send-out presentation remains separate lifecycle authority.
- HUD ownership, shadow suppression, size/shape rules remain unchanged.

## Runtime telemetry
- `SHOWDOWN_ACTION_BEGIN ... showdown_clip_policy=preserve_current_clip`
- `SHOWDOWN_ACTION_NATIVE_BODY_MOTION ... presentation_mode=native_mirror clip_rebind=0 animation_epoch_reset=0`
- `SHOWDOWN_ACTION_END ... action_clip_binding_next=0 preserve_current_clip=1`

## Regression contracts
- **R-SD-109** ORIGINAL_SOULGOLD_ACTION_PRESENTATION_IS_PRIMARY_AUTHORITY
- **R-SD-110** SHOWDOWN_ACTION_BODY_ONLY_MIRRORS_NATIVE_PROXY_TRANSFORM
- **R-SD-111** ACTION_WINDOW_MUST_NOT_RESTART_SHOWDOWN_ANIMATION_EPOCH
- **R-SD-112** DEFAULT_ACTION_POLICY_MUST_NOT_FORCE_ACTION_CLIP_REBIND
- **R-SD-113** ACTIVE_M5A1_LAUNCHER_DECLARED_STAGE_EXISTS_IN_PACKAGE

## Future exception policy
If a later visual defect clearly cannot be represented by native motion alone, a small optional enhancement category may be proposed. Such an enhancement must be:
1. explicitly justified by a visible defect,
2. gated by asset availability,
3. subordinate to SoulGold timing,
4. removable without changing gameplay.

There is no per-move choreography roadmap by default.
