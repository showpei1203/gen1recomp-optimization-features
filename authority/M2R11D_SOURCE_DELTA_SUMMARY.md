# M2R11D Source Delta Summary

## HUD directionality
- Replace global `restore_healthbox_ui(...)` with player-only `restore_player_healthbox_ui(...)`.
- Preserve `hud_occ = ((battler & 1u) && player_healthbox_valid) ? &player_healthbox : nullptr;` for opponent FRONT clipping.
- Final player healthbox restore is active for `battle || teardown_ui_hold`.
- Opponent healthbox is not globally restored over player BACK.

## Size-class authority
- Exact ladder: XS=.60, S=.72, M=.84, L=.96, huge/XL=1.08, colossal/XXL=1.20.
- Remove every `scale_mul` from body rules.
- Body type controls geometry only: fit envelope and anchor.
- Exception table may no longer override base scale.
- Marill (183), Sprigatito (1289), Togepi (175) are all XS and resolve to 0.60 front/back, even when a side uses legacy geometry.

## New gates
- `validate_m2r11d_directional_hud.py`
- `validate_m2r11d_size_class_authority.py`
- R-SD-042 directional HUD ownership
- R-SD-043 size-class sole scale authority

Full static stage-prebuild sequence: PASS before handoff packaging.
