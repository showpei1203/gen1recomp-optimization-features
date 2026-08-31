# CURRENT HANDOFF — SoulGold Showdown-first M2R9C

Current candidate: **M2R9C Battle Sprite Lab Compile-Safe Requested-Species Path**
Date: 2026-08-31

## Accepted authority retained
- M1.4 timing/audio = FORMAL PASS / SEALED.
- M2R5D presentation baseline = ACCEPTED.
- M2R8F runtime = ACCEPTED at ~59.7 FPS.
- Gen1–2 Showdown asset cache = 502/502 ready in the existing shared workspace cache.
- Runtime registry authority = 504 provider entries (502 Gen1–2 + Sprigatito front/back).

## M2R9/M2R9B failure chain
1. M2R9 was blocked by the stale `dynamic_runtime_path` validator. It still demanded
   `load_showdown_clip(proxy.species...)`, even though Sprite Lab intentionally routes
   the visual provider through the requested lab species. ROM/runtime acceptance was
   therefore never reached in that run.
2. M2R9B corrected the requested-species provider path, but runtime telemetry referenced
   selected/provider variables before their declarations. Host C++ preflight failed before
   the game window could launch.

## M2R9C fix
- Per-frame selected visual species authority is `requested_species[battler]`.
- `load_showdown_clip(...)` receives the requested visual species, not the native proxy species.
- Native proxy species remains untouched and authoritative for movement/visibility/affine/faint.
- `provider_ready` is evaluated against the loaded requested visual species.
- `SPRITE_LAB_RUNTIME` telemetry executes only after `requested_species`, `provider_ready`, and
  `any_proxy_valid` are materialized.
- The stale provider validator now recognizes the dynamic requested-species route.
- New compile-order gate prevents the same undeclared-variable regression.
- R-SD-036 covers the dynamic requested-species path plus compile-safe telemetry ordering.

## Run
`tools\soulgold_mgba\START_M2R9C_BATTLE_SPRITE_LAB.bat`

## Sprite Lab controls
- F9: ON/OFF
- F10/F11: next/previous geometry preset
- PgUp/PgDn: enemy FRONT species
- Shift+PgUp/PgDn: player BACK species

## Do not regress
- no native intro flash
- no native underlay
- HUD bounce must not move the player Showdown battler
- move animation foreground remains above Showdown battlers
- monbg/stat effects must never restore native battler pixels
- teardown dialogue/UI lifetime and native suppression remain latched until proxy release
- data-driven provider registry and safe native fallback remain mandatory
- no clean-plate architecture
- do not globally ignore x2/y2

Switch lifecycle remains `DEFERRED_NO_SECOND_PARTY_MON`.
