# SoulGoldRecomp Performance Root Cause Cold/Warm Authority

Date: 2026-08-30

## User observation
During the IRQ root-cause probe, lag started already in the scripted event immediately before battle and remained during battle.

## Correction to prior IRQ diagnosis
The uploaded IRQ probe evidence captured 51,830 IRQ entries. The first 51,829 entries had `should_yield=0` and completed normally. Only the final entry transitioned to `should_yield=1` and then reproduced the `PC=0x00000018` no-progress loop.

Therefore the `0x18` no-progress loop is not established as the cause of gameplay lag. It is consistent with a shutdown/host-quit artifact and must not be repaired as the gameplay-performance root cause.

The decisive final line was:
- halted=0
- should_yield=1
- static18=0
- miss18=0
- call_depth=7

The 512-frame present-in-place call-depth threshold is not implicated by call_depth=7.

## More relevant performance evidence
The same ~56 second session produced 82 distinct self-heal dispatch misses. Only a subset became native overlays. Multiple RAM/IWRAM entries cannot heal while RAM overlay healing remains disabled and may repeatedly bridge through the interpreter.

The IRQ probe also accidentally omitted `SOULGOLD_ROM_MIRROR_ENTRY_DISPATCH=1`, producing avoidable `0x0Axxxxxx` ROM-alias misses. Those alias misses are contamination from the probe and are not accepted as baseline performance evidence.

## Next gate
Use one binary and one starting save in two passes:

A. Cold unique heal cache.
B. Warm reuse of A's heal cache.

Both passes must:
- enable `SOULGOLD_ROM_MIRROR_ENTRY_DISPATCH=1`;
- keep `GBARECOMP_RAM_OVERLAY_HEAL=0`;
- record per-PC interpreter-bridge calls, guest instructions and wall time;
- record background overlay compile wall time;
- record live PC samples;
- record presentation cadence;
- be terminated by the harness from the console rather than by closing the game window, so the shutdown IRQ artifact cannot contaminate the capture.

No behavior repair is authorized until these measurements identify the dominant wall-time source.

Package:
`SOULGOLD_RECOMP_HANDOFF_S0_PERF_ROOTCAUSE_COLD_WARM_20260830.zip`

SHA-256:
`173439499594c5c0ac231972a358a27a60cedce952a7a58e9e5a131c1b764859`
