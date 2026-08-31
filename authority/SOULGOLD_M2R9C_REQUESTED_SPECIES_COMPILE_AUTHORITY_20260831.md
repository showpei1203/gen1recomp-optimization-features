# SoulGold M2R9C — Requested Species Path + Compile Order Authority
Date: 2026-08-31
Status: TEST CANDIDATE

## Root cause confirmed
The user-visible M2R9B failure occurred in host C++ preflight, before the game window launched.
The compiler reported Sprite Lab telemetry using selected/provider state before those locals were
declared in `video_cb`.

The immediately preceding M2R9 blocker was also confirmed: `validate_m2r6_provider_registry.py`
contained a stale proof-only requirement that the runtime load path use `proxy.species`. That rule
is incompatible with the visual-only Battle Sprite Lab, whose purpose is to request another
Showdown provider while retaining the real native proxy species.

## R-SD-036
`BATTLE_SPRITE_LAB_REQUESTED_PROVIDER_PATH_MUST_BE_DYNAMIC_AND_COMPILE_SAFE`

Required flow:
`proxy.species -> sprite_lab_display_species -> requested_species[battler] -> load_showdown_clip`

Required safety:
- `proxy.species` is not mutated.
- production provider registry is not revoked by an optional lab-provider failure.
- provider readiness matches the requested loaded provider.
- telemetry is emitted only after requested species/provider readiness are defined.
- normal-mode provider failure still revokes that provider and returns safely to native pixels.

## Retained presentation authority
R-SD-001/002/005/006/007/008/009/010/011/012/013/014/017/018/019/020/021/022/023/024/025/026/027/028/029/030/031/033/034/035 remain in force.

No clean-plate fallback is authorized. No global x2/y2 suppression is authorized.
