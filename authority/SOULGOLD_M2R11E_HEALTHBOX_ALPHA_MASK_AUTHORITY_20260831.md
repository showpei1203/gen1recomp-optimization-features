# SOULGOLD M2R11E HEALTHBOX ALPHA-MASK AUTHORITY (2026-08-31)

## Symptom
A thin grey row matching the native opponent shadow can intermittently rise from the top edge of the player HUD and cover the external opponent's feet.

## Root Cause
The player healthbox was restored as a rectangular framebuffer region. Healthbox OBJ art has transparent pixels and padding, so native battlefield/shadow pixels visible through those transparent locations were pasted over Showdown.

## Fix
- Build a transparent player-healthbox overlay every frame.
- Restore main/right healthbox sprites only where their OBJ tile sample is opaque.
- Restore the HP bar with a tight in-panel strip.
- Stop rectangular enemy-front clipping; composite actual HUD pixels after external battler rendering.

## Regression
R-SD-044 = PLAYER_HEALTHBOX_RESTORE_USES_OBJ_ALPHA_MASK_NO_BATTLEFIELD_SHADOW_PASTE

## Non-regression
R-SD-042 remains directional: player HUD above opponent FRONT only. Opponent HUD is not globally restored above player BACK.
