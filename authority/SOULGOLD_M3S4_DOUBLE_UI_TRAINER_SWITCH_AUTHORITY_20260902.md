# SOULGOLD M3S4 DOUBLE UI + TRAINER-DIRECTION SWITCH AUTHORITY (2026-09-02)

## Objective
Refine the F9 synthetic 2v2 lab after M3S3 user review without reopening accepted single-battle sizing/HUD/shadow work.

## R-SD-085 — Player-right vertical spacing
The synthetic player-right battler must be only slightly higher than player-left.

M3S4 lab offsets:
- P0 Y offset = +6
- P1 Y offset = +2

Therefore P1 is only 4 GBA pixels higher than P0. M3S3 used P1=-12, an 18-pixel difference that looked like two unrelated depth planes.

## R-SD-086 — Opponent withdraw direction
Opponent-side battlers do not use the accepted player-side downward return motion.
During synthetic withdraw they:
- move +28 GBA px toward the right;
- move -12 GBA px upward / rearward;
- shrink from 1.00 to 0.45.

This direction points toward the opponent trainer's upper-right side of the battlefield.

## R-SD-087 — Opponent send-out direction
Incoming opponent battlers begin from the same upper-right / rear vector and return to the target slot while scaling 0.45 -> 1.00.
The visual language is therefore symmetric with the trainer's location: return toward trainer, deploy from trainer.

## R-SD-088 — Exact SoulGold double healthbox geometry
F9 now renders translucent host-side double-HUD occupancy guides using the exact `sBattlerHealthboxCoords[BATTLE_COORDS_DOUBLES]` centers from SoulGold `src/battle_interface.c`:

- P0 / PLAYER_LEFT = (156, 76)
- P1 / PLAYER_RIGHT = (168, 101)
- E0 / OPPONENT_LEFT = (45, 19)
- E1 / OPPONENT_RIGHT = (33, 44)

SoulGold stores each table X coordinate on the left 64x32 healthbox OBJ; `SpriteCB_HealthBoxOther` positions the right half at `main.x + 64`. Therefore the full guide begins 32 px left of the table X and spans the live two-half footprint.

The guide dimensions are derived from the live single-battle native healthbox footprint when available, with a conservative fallback only for guide rendering.

## R-SD-089 — Synthetic guide is not functional native UI proof
The guide exists to test battlefield composition, sprite overlap, and future healthbox occupancy while the current save only has one usable Pokemon.
It does NOT claim:
- real double battle state;
- actual second HP/name/status values;
- real four-healthbox OAM lifecycle;
- production native double runtime PASS.

Native four-healthbox ownership remains a later M3S5 runtime target.

## R-SD-090 — Launcher-stage package contract
The active M3S4 BAT must resolve to `M3S4_STAGE_DOUBLE_UI_TRAINER_SWITCH_LAB.sh` contained in the same handoff package.

## Carry-forward rules
- M3S2 native withdraw/send-out semantics remain authoritative for production.
- M3S3 F9 lab remains host-only and never mutates save/party/ROM.
- Player-side switch motion is unchanged because the user accepted it.
- HUD priority, shadow removal, alpha-mask restoration, and accepted scale rules remain sealed.
