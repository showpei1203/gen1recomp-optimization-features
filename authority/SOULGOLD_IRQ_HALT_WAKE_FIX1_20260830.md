# SoulGoldRecomp S0 IRQ HALT Wake FIX1

Date: 2026-08-30

## BIOS-AOT FIX1 status

REJECTED. User reports ordinary/event/battle gameplay remained very laggy.

## Runtime evidence

The BIOS-AOT evidence contains 16 independent depth-1 IRQ failures:

`runtime_irq: handler at depth 1 did not iret after 4000000 dispatches (R15=0x00000018, cpsr=0x60000092)`

The interrupted LR distribution is entirely in the BIOS HALT/IntrWait continuation region:
- `0x00000348` x5
- `0x00000350` x2
- `0x0000035C` x1
- `0x00000360` x1
- `0x00000378` x7

The run linked the generated BIOS corpus successfully and recorded zero BIOS dispatch misses. Therefore the repeated 0x18 no-progress loop is not caused by a missing BIOS dispatch table.

## Source-level root cause

The pinned gbarecomp source establishes the full chain:

1. Writing HALTCNT sets `GbaIo::halted_ = true`.
2. `GbaIo` exposes `clear_halt()` and documents that execution remains halted until a pending IRQ clears the state.
3. Repository search finds no runtime caller of `clear_halt()`.
4. `runtime_tick()` detects wake-from-HALT and models `kIrqWakeDelayCycles`, then enters `runtime_irq()` without clearing the HALT latch.
5. Generated ARM/THUMB code sets R15 to the current guest PC and executes `if (runtime_should_yield()) return;` before each instruction.
6. `runtime_should_yield()` ultimately returns the IO `halted` state.
7. A generated BIOS IRQ vector entered while the stale HALT latch is still set therefore returns before its first instruction executes. PC remains `0x18`, so the IRQ drive loop redispatches it millions of times.

## Narrow repair

After the already-modelled IRQ wake latency and immediately before `runtime_irq(g_cpu.R[15])`, call:

`bus->io().clear_halt();`

This is intentionally narrower than changing global yield semantics.

## Guardrails

- Full static BIOS AOT remains ON so the failing generated 0x18 path is exercised directly.
- Fresh empty heal cache required.
- RAM overlay healing OFF.
- D1 FastUnsafeCopy32 OFF.
- D1 SoundMainRAM OFF.
- ROM mirror dispatch ON.
- No battle/PMD/presentation/LCD changes.

## Handoff

`SOULGOLD_RECOMP_HANDOFF_S0_IRQ_HALT_WAKE_FIX1_20260830.zip`

SHA-256: `b1a2832cec889526d5649ff7eef46b2ebc7768b7e7177f2d25b1be314d04ee3f`
