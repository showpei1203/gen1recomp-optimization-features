# SOULGOLD M3S6 ORIGINAL DOUBLE-HUD SAFE GUIDE AUTHORITY
Date: 2026-09-02

## User feedback promoted
The synthetic player-side double-HUD guide was overlapping the real bottom command HUD and could interfere with operation. The user explicitly requested comparison against SoulGold's original double-battle UI behavior.

## Root cause
M3S5 used the correct SoulGold double-healthbox *centers*, but derived guide width/height from the currently active **single-battle** `read_healthbox_union()` result. That mixed coordinate authority from doubles with footprint authority from singles. The synthetic guide could therefore become taller than the original double healthbox and invade the command/message area.

## Original SoulGold authority
SoulGold defines double healthbox centers in `src/battle_interface.c`:
- P0 / PLAYER_LEFT: `(156, 76)`
- P1 / PLAYER_RIGHT: `(168, 101)`
- E0 / OPPONENT_LEFT: `(45, 19)`
- E1 / OPPONENT_RIGHT: `(33, 44)`

The healthbox base OAM is `64x32`. The full healthbox uses a left 64x32 OBJ plus a companion right half whose callback follows the main sprite at `x + 64`. Therefore the canonical full footprint is **128x32 GBA pixels**.

SoulGold's battle message/command window begins at `tilemapTop = 15`, i.e. **Y = 120 px**. With P1 centered at Y=101 and a 32-pixel healthbox height, the native double player-right healthbox occupies approximately Y=85..117, deliberately leaving the bottom UI untouched.

## M3S6 rules
### R-SD-097 — Double HUD guide footprint comes from native double OAM, not current singles HUD
Synthetic double guides use fixed `128x32` GBA geometry. `read_healthbox_union(0/1)` is not allowed to set synthetic double-guide dimensions.

### R-SD-098 — Synthetic guide may never enter the native command/message region
Synthetic guide drawing is clipped at `Y < 120`. The guide is visual QA only and must never reduce readability or usability of the real bottom HUD.

### R-SD-099 — Synthetic HUD guide remains non-interactive wireframe
The guide stays outline-only, low alpha, with a small center tick. It is never a filled panel, never an input target, and never proof of functional native double UI.

### R-SD-100 — Native double UI remains SoulGold-owned
M3S5 native-double detection remains intact and read-only. When a genuine 4-battler double battle exists, the real SoulGold healthboxes are observed rather than replaced.

## Expected result
- Player P1 guide no longer overlaps the bottom Battle / Bag / Pokemon / Run command area.
- P0/P1/E0/E1 guide geometry now matches the original SoulGold healthbox construction rather than the current single-battle HUD dimensions.
- Synthetic lab remains useful for occupancy testing without blocking operation.
