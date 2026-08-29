# SoulGoldRecomp S0-C3 Outdoor Transition Failure — Runtime Evidence Pending

Date: 2026-08-29

## Sealed baseline
- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 CART BOOT / RENDER = FORMAL PASS / SEALED
- S0-C2 TITLE FLOW / REAL START INPUT = FORMAL PASS / SEALED

S0-C3 is **not** promoted.

## User-observed S0-C3 runtime result
Interactive flow progressed through title/new-game and was playable indoors. On leaving the starting house and transitioning to the outdoor map:

1. the game stalled;
2. it then returned to the beginning/boot flow;
3. BGM had intermittent crackle;
4. presentation showed noticeable lag;
5. the normal S0-C3 evidence ZIP was not produced.

## Current interpretation
Treat the outdoor event as a guest runtime reset/crash candidate until logs prove otherwise. Do not blame game data or patch the SoulGold script/map yet.

The previously sealed S0-C2 coverage was already NOT_STATIC and showed high-frequency interpreter bridges in RAM-executed code, notably:
- 0x03000000 ARM
- 0x0300012C ARM
- 0x030011E8 THUMB
plus multiple RAM jump-table candidates.

Those gaps are plausible contributors to loading hitches / performance stalls and may expose additional outdoor-only execution paths. They are not yet proven as the direct reset cause.

## Audio / lag policy
Do not tune audio buffers as the primary fix before execution coverage is understood. Pinned GBARecomp's audio implementation explicitly treats a reset/loading hitch/long producer stall as a possible queue underrun/crackle condition. First capture the transition execution failure, then close the relevant static/runtime gaps; only afterward perform controlled audio-path A/B tests.

## Evidence recovery policy
The original S0-C3 harness only finalized its ZIP after a normal interactive shutdown. That is insufficient for reset/crash diagnosis.

Next action is a recovery collector that does **not rerun the game**. It gathers:
- newest Windows S0_STAGE_C3 log;
- any existing WSL _s0c3 framebuffer / coverage / miss / cadence / save artifacts;
- a manifest describing what survived.

After reviewing recovered evidence, build a crash-safe S0-C3D diagnostic harness with live/partial evidence and, if needed, self-heal verbose tracing around the outdoor transition.

## Permanent project requirements
1. Every meaningful checkpoint ships a user-downloadable handoff.
2. Finished product must ship Traditional Chinese zh-Hant-TW using the external localization/glyph architecture with English fallback.
