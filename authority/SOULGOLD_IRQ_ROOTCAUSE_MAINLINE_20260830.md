# SoulGoldRecomp IRQ Root-Cause Mainline

Date: 2026-08-30

## User direction
Historical-binary archaeology is closed. Do not spend further checkpoints searching old binaries. Mainline is now the reproducible current battle-lag defect.

## Exonerated primary causes
- P1 LCD filter / interframe persistence.
- 1x vs 2x host presentation scale.
- D1 FastUnsafeCopy32 static native root.
- D1 SoundMainRAM static native root.

## Reproducible current defect
Recent D1B/D1C/E0 controlled runs show battle onset entering `runtime_irq()` at depth 1, then remaining at:
- PC `0x00000018`
- IRQ-mode CPSR (observed `0x60000092`)
- unchanged architectural state across repeated `runtime_dispatch(0x18)` calls.

The existing guard allows up to 4,000,000 dispatch attempts, consuming CPU and manifesting as severe battle lag. This is a runtime correctness defect, not a rendering-load problem.

## Root-cause gate before repair
`S0_IRQ_ROOTCAUSE_PROBE` adds observation only and aborts after 32 already-proven unchanged IRQ-vector dispatches. It records:
- BIOS 0x18 static-entry presence;
- dispatch-miss(0x18) count;
- live HALT state;
- `runtime_should_yield()` result in the broken state;
- IE / IF / IME;
- BIOS instruction word at 0x18;
- SP / LR / call depth;
- debug-break and force-interpreter-hook state.

No behavioral fix is to be promoted until this evidence identifies the exact early-return layer.

## Working hypothesis, not yet promoted as fact
The static BIOS IRQ entry may be returning from its generated prologue because `runtime_should_yield()` still observes a stale HALT state while `runtime_irq()` is already active. This is testable by the probe and must not be patched until confirmed.
