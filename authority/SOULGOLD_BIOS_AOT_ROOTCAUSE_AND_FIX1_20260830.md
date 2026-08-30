# SoulGoldRecomp BIOS AOT Root Cause + Fix1

Date: 2026-08-30

> **STATUS CORRECTION — REJECTED.** The BIOS-AOT FIX1 validation remained very laggy from the pre-battle event through battle. Its evidence linked the generated BIOS successfully and recorded zero BIOS dispatch misses, yet still produced 16 depth-1 IRQ handlers stuck at PC `0x00000018` for the 4,000,000-dispatch guard. Therefore missing BIOS AOT was a real Cold-run performance cost but **not the complete/root runtime defect**. Current authority is `SOULGOLD_IRQ_HALT_WAKE_FIX1_20260830.md`, which identifies the stale HALT latch at IRQ wake.

## Historical Cold/Warm observation

Controlled Cold/Warm A/B result:
- A_COLD: pre-battle event very laggy; battle very laggy.
- B_WARM: same binary and same starting save; pre-battle event smooth; battle smooth.

The exact build log for that binary reported:

`BIOS recompiled output absent — placeholder dispatch only.`

Cold-run profiling quantified the major BIOS interpreter bridges:
- `0x00000328`: 83 bridge calls, 781.050 ms total, 9.410 ms avg.
- `0x00000344`: 9 calls, 175.319 ms total, 19.480 ms avg.
- `0x00000140`: 29 calls, 172.402 ms total, 5.945 ms avg.

Those BIOS bridge sites disappeared from the Warm run after A populated the native self-heal cache. This remains valid evidence that missing BIOS static coverage creates Cold-run stalls, but the later FIX1 test proved it was not sufficient to resolve the lag.

By contrast, `SoundMainRAM` (`0x030011E8`) consumed similar aggregate bridge time in Cold and Warm while Warm was smooth, so it remains non-native for BGM correctness.

## Rejected Fix1 build order

1. Build `gba_recompile`.
2. Generate BIOS AOT using the real BIOS and reviewed BIOS config.
3. Hard-gate BIOS dispatch entries `0x18`, `0x140`, `0x328`, `0x344`.
4. Recompile SoulGold with sealed C3H roots.
5. Configure the runner with `-DGBARECOMP_GENERATED_BIOS_DIR=<generated BIOS dir>`.
6. Require `BIOS recompiled output present — linking`.
7. Validate with a fresh empty self-heal cache.

This build order succeeded structurally, but runtime acceptance failed.

## Rejection evidence

The BIOS-AOT run:
- linked generated BIOS output successfully;
- had `BIOS_RUNTIME_MISS_COUNT=0`;
- still produced 16 `runtime_irq` non-return guards at `PC=0x00000018`;
- interrupted LR values clustered entirely in BIOS HALT/IntrWait continuation addresses (`0x348`, `0x350`, `0x35C`, `0x360`, `0x378`).

The current root-cause lane is therefore IRQ wake-from-HALT semantics, not further BIOS coverage expansion.

## Handoff

Rejected artifact:
`SOULGOLD_RECOMP_HANDOFF_S0_BIOS_AOT_FIX1_20260830.zip`

SHA-256:
`1594aaf0b9c5af3a010a631f38266277c938c885abf0ca0ad089791988c8cc17`
