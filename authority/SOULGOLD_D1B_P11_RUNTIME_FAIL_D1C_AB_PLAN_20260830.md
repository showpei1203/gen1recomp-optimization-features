# SoulGoldRecomp D1B/P1.1 Runtime Failure and D1C A/B Authority

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

## D1C runtime-only A/B

Do not rebuild or change guest correctness. Reuse the exact D1B runner:

`b474d25455f34a9a9681fc30094b51470c08d0dc83a39da4f599f702c7d1acdb`

Candidate A:
- same D1B/C3H correctness;
- scale 2 / 480x320;
- LCD filter OFF;
- interframe OFF.

If A still lags, Candidate B:
- exact same binary/correctness;
- scale 1 / 240x160;
- LCD filter OFF;
- interframe OFF.

Decision matrix:
- A smooth => P1.1 LCD execution path is primary causal candidate;
- A lag + B smooth => scale2/window/host timing is primary causal candidate;
- A lag + B lag => presentation filter and scale2 are exonerated; audit runtime IRQ return semantics and re-audit whether C3H was battle-performance validated rather than only interaction-correct.

## Permanent release contract

- one shared core;
- Showdown and PMD content providers;
- Traditional Chinese `zh-Hant-TW` required;
- desktop viewport target remains 480x320;
- mGBA-like LCD appearance remains a target, but may not alter battle timing correctness;
- primary finished device remains AYN THOR / Android ARM64.
