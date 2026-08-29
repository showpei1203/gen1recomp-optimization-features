# SoulGoldRecomp G0 Historical Binary Sweep

Date: 2026-08-30

## Trigger
F0 direct execution of `SoulGoldRecomp_c3h/build-c3h/SoulGoldRecomp` is not a valid reproduction of the 02:53 accepted C3H run because the surviving binary has mtime `2026-08-30 02:56:50`, later than the start of the 02:53 evidence run.

F0 also exposed a separate general-runtime degradation class:
- initial cadence near 59 FPS;
- later ~34 FPS then ~15 FPS;
- `SELF-HEAL bridge for 0x08241524 exceeded 200000000 instructions`.

This differs from later battle-specific IRQ non-return regressions.

## Historical candidates
Run the exact surviving binaries that predate the 02:53 run:

A. `SoulGoldRecomp/build-c3f/SoulGoldRecomp`
   - mtime 2026-08-29 20:34:15
   - size 208,473,072 bytes

B. `SoulGoldRecomp/build-c3d/SoulGoldRecomp`
   - mtime 2026-08-29 20:11:00
   - size 208,476,584 bytes

C. `SoulGoldRecomp/build-s0/SoulGoldRecomp`
   - mtime 2026-08-29 18:59:22
   - size 189,473,904 bytes

## Rules
- no compile;
- no patch;
- no recompiler;
- no LCD/presentation experiment;
- same ROM/BIOS/config;
- automatically copy the newest available SoulGold battery save and use the same copied save for all candidates;
- preserve each exact binary SHA-256/mtime/size and runtime logs.

## Acceptance
For each candidate record:
- ordinary gameplay: smooth / lag;
- battle: smooth / lag;
- BGM: normal / abnormal.

The first candidate with smooth ordinary gameplay, smooth battle, and normal BGM becomes the binary-level regression anchor. Freeze that exact executable and its corresponding source-era state before any optimization resumes.

## Package
`SOULGOLD_RECOMP_HANDOFF_S0_G0_HISTORICAL_BINARY_SWEEP_20260830.zip`

SHA-256:
`4d98959c18b7e7498d3b21d8dd890cf24cad77602adb024d3cf1e14b90dac714`
