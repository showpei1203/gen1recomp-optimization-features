# v0.2.02a Promotion Spec

Purpose: convert the accepted v0.2.01f test state into a formal GBC Layer I runtime build without carrying benchmark-only behavior into release.

Allowed change from v0.2.01f:
- remove GBC_A2 fixture code
- remove free-overworld B interception
- remove battle-local benchmark clone / injected moveset
- remove fixture state and fixture logging

Frozen from v0.2.01f:
- GBC move visuals
- Psybeam seamless 4f WAVE continuation
- Psybeam `beam_release` non-contact semantics
- HIT_FRAME and Action Binding ownership
- damage/status/SFX/audio-tail/barrier behavior
- DRAMATIC_SHAPE / THOR / Depth integration
- GBC assets and `gbc_anim_data.lua`

Promotion requires exact hash gates, no fixture logs, no GBC runtime error, no current app Lua/FATAL/ANR error, and retained sealed dependency hashes.

Native-presentation rule for future catalog expansion: verify Crystal animation script, BG effect, object/frameset/OAM, cadence/waits/loops and palette behavior before implementing a move. Raw PNG appearance alone is not sufficient evidence.
