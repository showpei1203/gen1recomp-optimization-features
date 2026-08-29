# SoulGoldRecomp S0-C3D Evidence Correction — ROM Mirror Dispatch Hypothesis

Date: 2026-08-29

## Sealed baseline
- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 = FORMAL PASS / SEALED
- S0-C2 = FORMAL PASS / SEALED
- S0-C3 = FAIL / NOT PROMOTED

## User observation from C3D Fix1
- Talking to Mom already feels laggy.
- BGM is audibly dirty/fuzzy before the outdoor crash.
- Exiting the starting house still crashes.

This means the audio issue must remain tracked as an independent pre-transition defect; it can no longer be explained only as a consequence of the outdoor fatal stall.

## First confirmed fatal event in S0-C3D evidence
The diagnostic build completed and ran successfully. Presentation stayed near 59.1-59.8 FPS through n=3600, then collapsed to 13.79 FPS at n=3960.

The first explicit fatal runtime event is:

`runtime_arm: SELF-HEAL bridge for 0x0A23E920 exceeded 200000000 instructions without returning to stop_pc=0x082414FC (current pc=0x00000344). Aborting rather than spinning silently.`

Only after this self-heal runaway does the trace enter BIOS/IRQ/reset-like secondary failure behavior.

Therefore the previous working hypothesis that the IRQ non-return was the initiating defect is superseded. IRQ corruption is currently classified as downstream damage.

## Why 0x0A23E920 is important
Pinned GBARecomp's GBA memory map classifies 0x08/09, 0x0A/0B and 0x0C/0D as Game Pak ROM. Its `resolve_offset()` explicitly normalizes all three waitstate windows with:

`addr & 0x01FFFFFF`

Thus 0x0A23E920 maps to the same physical ROM offset as canonical 0x0823E920.

However pinned `runtime_dispatch()` strips only the THUMB bit and then performs an exact binary search of `kDispatchTable` using the guest PC. It does not canonicalize Game Pak execution aliases before static dispatch lookup. `runtime_has_static_entry()` likewise does an exact address lookup.

This creates a concrete compatibility hypothesis:

**SoulGold reaches executable code through a legitimate Game Pak ROM waitstate alias (0x0Axxxxxx), while the native dispatch table contains only canonical 0x08xxxxxx entries. The exact-address miss falls into the self-heal interpreter and runs away.**

## Not yet promoted as root cause
Before patching dispatch semantics, verify all of the following for exact SoulGold S0-A artifacts:
1. 0x0823E920 is inside the exact ELF/ROM text and is code-like.
2. imported symbols identify a function or valid interior code region at/around 0x0823E920.
3. generated `dispatch_table.cpp` contains a static entry for 0x0823E920 in the required ARM/THUMB mode, or clearly shows the nearest valid entry/resume relationship.
4. stop_pc 0x082414FC resolves to a coherent static return location.

If these hold, build a separate ROM-mirror dispatch candidate. Do not change the sealed S0-B runner directly.

## Audio/performance track
The user reports BGM fuzz/crackle and subjective lag while still indoors, before the fatal outdoor transition. Track this separately as `AUDIO/PERF-01`.

Do not tune audio buffers yet. First separate:
- guest execution/self-heal stalls,
- host presentation cadence,
- audio resampler/queue behavior.

## Next gate
S0-C3E = no-game ROM mirror dispatch probe. It must inspect exact ELF/imported symbols/generated dispatch and produce a downloadable evidence handoff before any runtime patch is promoted.

## Permanent project requirements
1. Every meaningful checkpoint ships a downloadable handoff.
2. Final product ships Traditional Chinese `zh-Hant-TW` using external UTF-8 localization + external CJK glyph assets with English fallback.
