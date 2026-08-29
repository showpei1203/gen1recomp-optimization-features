# SoulGoldRecomp D1B/P1.1 Runtime Failure and D1C C3H-Controlled A/B Authority

Date: 2026-08-30

## User result

D1B/P1.1 Fix1 launched successfully after the new handoff preflight and the user reports that battle is still **very laggy**.

Evidence package:
- `SOULGOLD_S0_D1B_P11_EVIDENCE_20260830_063201.zip`
- SHA-256 `b23f73fa570cff3fba3c65e6d47a342cdede51ffa77c313e02e5dcbef4a18457`

## Structural gates proven by the evidence

The candidate actually used the intended D1B isolation state:
- C3H `IntrMain` root count = 1;
- C3H `IntrMain_RetAddr` root count = 1;
- FastUnsafeCopy32 static native root count = 0;
- SoundMainRAM static native root count = 0;
- `S0_D1_HOT_RAM.toml` is comment-only / no-op;
- D1B codegen gate = PASS.

Therefore the D1A battle regression is not explained by either D1 native root alone. FastUnsafeCopy32 is no longer the primary causal suspect.

## Runtime evidence

Before the battle failure the presenter is generally near 59.5-59.7 FPS.
Near the observed regression the cadence reaches 31.56 FPS.

The runtime then repeatedly reports:
- depth-1 IRQ handler did not iret after 4,000,000 dispatches;
- R15 / PC = `0x00000018`;
- CPSR = `0x60000092`;
- LR = `0x00000348` in the captured trace.

D1B is therefore REJECTED.

## Corrected known-good control: C3H

The user explicitly recalled that an earlier build had normal battle performance, likely the first build where BGM was reported normal.

The sealed C3H authority confirms this is the correct known-good control:
- BGM normal / clean;
- no perceived lag;
- indoor traversal works;
- outdoor traversal works;
- scripted events work;
- battle entry works;
- ~201 sec capture;
- mean ~59.67 FPS;
- median ~59.81 FPS.

C3H is therefore not merely an interaction-correct guess. It is the last recorded known-good runtime control before D1 changes.

## Regression chronology

1. `C3H`: BGM clean, no perceived lag, battle entry accepted.
2. `D1P1`: added FastUnsafeCopy32 + SoundMainRAM native roots; large static-coverage gain, but BGM corruption/noise -> REJECTED.
3. `D1A/P1.1`: SoundMainRAM native rolled back; BGM recovered; battle lag/abnormal audio appeared.
4. `D1B/P1.1`: FastUnsafeCopy32 also rolled back; correctness/codegen returned to C3H roots; battle still very laggy.

This narrows the next investigation to post-C3H host/presentation/runtime differences rather than D1 guest native roots.

## D1C controlled A/B

Build one unpatched C3H-equivalent host/runtime from the same pinned base and C3H roots, then run two presentation modes against the same guest correctness:

### Candidate A — C3H replay control
- no P1 LCD host patch;
- LCD OFF;
- interframe OFF;
- scale 1 / 240x160;
- C3H roots only.

### Candidate B — scale-only isolation
- exact same unpatched runner binary as A;
- LCD OFF;
- interframe OFF;
- scale 2 / 480x320.

The already-tested D1B/P1.1 candidate is the failing Candidate C reference:
- C3H roots only;
- P1 LCD host patch present;
- LCD ON;
- interframe ON;
- scale 2 / 480x320;
- battle very laggy.

## Decision matrix

- A smooth + B smooth + C lag => P1.1 LCD/interframe host patch is causally implicated.
- A smooth + B lag + C lag => 2x/window/host timing path is causally implicated.
- A lag => the reconstructed runner differs materially from the sealed C3H runtime despite matching guest roots; diff host/runtime source, instrumentation, and build lineage before any further presentation work.

Do not return to IRQ-semantics redesign unless Candidate A itself reproduces the lag. The known-good C3H control must remain the anchor.

## Permanent release contract

- one shared core;
- Showdown and PMD content providers;
- Traditional Chinese `zh-Hant-TW` required;
- desktop viewport target remains 480x320;
- mGBA-like LCD appearance remains a target, but may not alter battle timing correctness;
- primary finished device remains AYN THOR / Android ARM64.
