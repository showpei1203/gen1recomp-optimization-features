# SoulGoldRecomp S0-C3F Evidence Result — ROM Mirror Fix Advances to IWRAM Failure

Date: 2026-08-29
Status: AUTHORITY
Branch: `feature/soulgold-recomp-s0`

## Sealed baseline
- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 = FORMAL PASS / SEALED
- S0-C2 = FORMAL PASS / SEALED
- S0-C3 = FAIL / NOT PROMOTED
- S0-C3E = STATIC PROBE PASS (`CANONICAL_STATIC_ENTRY_CONFIRMED`)
- S0-C3F = CANDIDATE FAIL / NOT PROMOTED

## User observation
- Leaving the starting house still fails.
- Indoor/early gameplay still feels laggy.
- BGM is somewhat better than before, but remains audibly dirty / less clear than normal emulator playback.

## What C3F proved
The entry-only ROM mirror candidate is active and is not a no-op. Runtime log records 64 early mirror dispatch hits, including repeated valid alias-to-canonical conversions around:

- `0x0A23D5E0 -> 0x0823D5E0`
- `0x0A23D608 -> 0x0823D608`

The former C3D fatal event:

`SELF-HEAL bridge for 0x0A23E920 exceeded 200000000 instructions...`

is absent from the C3F evidence. This means the ROM-mirror dispatch correction successfully advances execution past the previously confirmed mirror defect.

## New first explicit failure
C3F now fails later on an IWRAM dispatch path:

`runtime_arm: SELF-HEAL bridge hit interpreter Undefined at pc=0x030016AC while bridging dispatch miss 0x0300012C.`

Runtime exits with code 6.

This reclassifies the next blocker as an IWRAM copied-code / static-resume / interpreter-coverage problem. Do not remove the ROM mirror candidate merely because the game still fails; the failure frontier moved.

## Performance evidence
Presentation cadence remains approximately 59.4–59.8 FPS through n=3240. At n=3600, during the new failure path, cadence collapses to ~14.02 FPS with median present gap ~59.6 ms.

Historical S0-C2 coverage already identified high-frequency runtime bridges at IWRAM addresses including `0x0300012C`, making this path a plausible contributor to ongoing indoor performance/audio degradation as well as the transition failure.

## SoulGold source context
SoulGold's `crt0.s` places `IntrMain` in `.iwram.code`, and `InitializeWorkingMemory` DMA-copies the entire `.iwram` image from `__iwram_lma` in ROM into `__iwram_start` at runtime. The modern linker script places `.iwram` at `0x03000000` and reserves its ROM load image through `.data.iwram`.

Therefore `0x0300012C` and `0x030016AC` must be investigated as exact IWRAM code addresses using the pinned SoulGold ELF, static dispatch table, generated code, and ROM load image before changing interpreter semantics.

## Audio/performance track
`AUDIO/PERF-01` remains OPEN.

The slight BGM improvement under C3F suggests removing mirror self-heal traffic helped some runtime pressure, but audio is still clearly inferior to emulator playback. Do not mark audio fixed and do not hide it by buffer-only tuning.

Next audio gate, after crash-path stabilization, should compare:
- default callback DRC path;
- existing `GBARECOMP_AUDIO_DIRECT` diagnostic path;
- guest interpreted/self-heal load;
- host cadence;
- later Android/AYN THOR device audio.

## Primary release target
Primary finished platform is **AYN THOR / Android ARM64**.

PC/WSL remains development/diagnostic only. Runtime correctness fixes must be platform-neutral C/C++ unless cleanly isolated behind a host adapter. No correctness fix may depend on Win32, DWM, PowerShell, or WSL.

## Next gate
S0-C3G = no-game IWRAM static/resume/interpreter probe for:
- dispatch miss `0x0300012C`;
- undefined interpreter PC `0x030016AC`;
- `.iwram` VMA/LMA mapping;
- nearest ELF symbols and function ownership;
- exact/near dispatch entries and resume flags;
- actual ARM/THUMB instruction bytes/mnemonic at `0x030016AC`;
- generated recompiler references.

Do not patch interpreter or fabricate a return until C3G identifies the exact instruction and control-flow ownership.

## Permanent requirements
1. Every meaningful checkpoint ships a downloadable handoff.
2. Finished product ships Traditional Chinese `zh-Hant-TW` via external localization/glyph assets with English fallback.
3. Primary finished hardware target is AYN THOR / Android ARM64.
