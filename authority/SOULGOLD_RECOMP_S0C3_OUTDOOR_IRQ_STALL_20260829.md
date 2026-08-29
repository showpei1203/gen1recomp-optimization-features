# SoulGoldRecomp S0-C3 Outdoor Transition Failure Authority

Date: 2026-08-29

## Sealed baseline
- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 cart boot/render = FORMAL PASS / SEALED
- S0-C2 real START/title flow = FORMAL PASS / SEALED
- S0-C3 = NOT PROMOTED

## User-observed failure
Interactive play was viable indoors. Leaving the starting house caused a stall and then a return toward the boot/start flow. BGM had some crackle and presentation felt slightly laggy.

## Recovered runtime evidence
The sealed runner/ROM/BIOS identities remained correct.

Presentation cadence was essentially ~59.3-59.8 FPS through n=4320, then collapsed to 28.42 FPS at n=4680 immediately before the runtime IRQ watchdog started firing.

First fatal signature:

`runtime_irq: handler at depth 1 did not iret after 4000000 dispatches (R15=0x08000000, cpsr=0x0000001F) — abandoning`

After the first abandonment, repeated IRQ attempts became trapped at BIOS IRQ vector `0x00000018` in IRQ mode (`cpsr=0x60000092`) and repeatedly hit the same 4,000,000-dispatch watchdog.

The recovered log contains 154 `runtime_irq ... did not iret` watchdog events before capture ended.

## Root-cause status
The immediate failure is now localized to IRQ drive-to-completion / exception-return handling during the first outdoor transition, not to SDL rendering, user input, ROM identity, BIOS identity, or a generic low-FPS host limitation.

The current runtime watchdog `break`s out of the IRQ drive loop without restoring a coherent pre-IRQ PC/CPSR exception state. That explains why, after the first non-returning IRQ, execution degenerates into reset-vector / IRQ-vector loops and visually appears to return toward the beginning.

The deeper cause of the *first* non-returning IRQ is not yet promoted as known. We still need the active IRQ source plus the recent SWI/IRQ sequence and pre-stall trace before deciding whether the initiating defect is a BIOS/HLE semantic gap, IRQ timing/order issue, RAM-copied handler gap, or guest soft-reset path.

## Performance/audio interpretation
The recovered presentation data does **not** show sustained host rendering starvation before the transition. The severe frame-rate collapse begins at the transition itself. Therefore the large visible stall is downstream of the IRQ failure.

BGM crackle may share the same producer-stall cause, but because the user heard some crackle before/around failure and no audio telemetry survived this run, audio remains a tracked secondary issue rather than a proven independent audio-core defect.

## Next gate: S0-C3D crash-safe IRQ diagnostic
Do not patch around the guest warning or skip IRQs. Build a diagnostic engine from the exact pinned GBARecomp commit in a separate worktree. It must:
1. leave sealed S0-B runner/source untouched;
2. detect repeated identical PC/CPSR state inside `runtime_irq` much earlier than the 4M watchdog;
3. persist IRQ-vector and SWI rings plus a register snapshot before terminating;
4. hard-stop the diagnostic runner instead of `break`-and-continue corruption;
5. package evidence even on the diagnostic exit code.

Only after that capture do we choose the actual runtime fix.

## Permanent project requirements
1. Every meaningful checkpoint ships a downloadable handoff.
2. Final product ships Traditional Chinese `zh-Hant-TW` using an external localization/glyph layer with English fallback.
