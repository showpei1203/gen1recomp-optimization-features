# SoulGoldRecomp BIOS AOT Root Cause + Fix1

Date: 2026-08-30

## Root cause promoted

Controlled Cold/Warm A/B result:
- A_COLD: pre-battle event very laggy; battle very laggy.
- B_WARM: same binary and same starting save; pre-battle event smooth; battle smooth.

The exact build log for that binary reported:

`BIOS recompiled output absent — placeholder dispatch only.`

Cold-run profiling quantified the major BIOS interpreter bridges:
- `0x00000328`: 83 bridge calls, 781.050 ms total, 9.410 ms avg.
- `0x00000344`: 9 calls, 175.319 ms total, 19.480 ms avg.
- `0x00000140`: 29 calls, 172.402 ms total, 5.945 ms avg.

Those three BIOS bridge sites disappeared from the Warm run after A had populated the native self-heal cache.

By contrast, `SoundMainRAM` (`0x030011E8`) consumed similar aggregate bridge time in Cold and Warm while Warm was smooth, so it is not the cause of the Cold-vs-Warm performance difference and remains non-native for BGM correctness.

Therefore the primary Cold-start event/battle lag root cause is:

**The SoulGold runner was linked with `bios_dispatch_stub.cpp` instead of a statically recompiled BIOS corpus, forcing BIOS paths through the interpreter/self-heal until the cache became warm.**

## Framework contract that confirms the diagnosis

gbarecomp CMake links the real BIOS sources only when `GBARECOMP_GENERATED_BIOS_DIR/bios_recompiled.cpp` exists. Otherwise it explicitly links the placeholder dispatch and prints the missing-BIOS warning.

`gba_recompile --bios` supports generation of:
- `bios_recompiled.cpp`
- `bios_recompiled.h`
- `bios_dispatch_table.cpp`

The reviewed `bios/gba_bios.toml` already contains the needed BIOS roots, including the measured hot PCs `0x140`, `0x328`, and `0x344`, plus the SWI jump table.

## Fix1 build order

1. Build `gba_recompile`.
2. Generate BIOS AOT using the real BIOS and reviewed BIOS config:
   - `--bios bios/gba_bios.bin`
   - `--config bios/gba_bios.toml`
   - `--out <isolated generated BIOS dir>`
3. Hard-gate BIOS dispatch entries `0x18`, `0x140`, `0x328`, `0x344`.
4. Recompile SoulGold with sealed C3H roots.
5. Configure the runner with `-DGBARECOMP_GENERATED_BIOS_DIR=<generated BIOS dir>`.
6. Require CMake to print `BIOS recompiled output present — linking`.
7. Reject any build still printing `BIOS recompiled output absent`.
8. Validate with a fresh empty self-heal cache.

## Guardrails

- D1 FastUnsafeCopy32: OFF.
- D1 SoundMainRAM: OFF.
- RAM overlay healing: OFF.
- ROM mirror dispatch: ON.
- No LCD/presentation change in this fix.
- Acceptance requires cold-cache ordinary/event/battle smoothness and normal BGM.

## Handoff

`SOULGOLD_RECOMP_HANDOFF_S0_BIOS_AOT_FIX1_20260830.zip`

SHA-256:
`1594aaf0b9c5af3a010a631f38266277c938c885abf0ca0ad089791988c8cc17`
