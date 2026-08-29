# SoulGoldRecomp D1C C3H A/B FIX1 — Build Throttle

Date: 2026-08-30

## Observed failure

User reported that the D1C C3H A/B package did not launch the game.

Evidence archive:
- `SOULGOLD_S0_D1C_C3H_AB_EVIDENCE_20260830_065356.zip`

Evidence confirms:
- `A_RUN_EXIT_CODE=-999`
- `B_RUN_EXIT_CODE=-999`
- neither Candidate A nor Candidate B launched
- runner build aborted at `69/138`
- failing command used `cmake --build ... -j 12`
- immediately afterward another WSL call failed with a `Wsl/Service/0x80072746`-class service error

No normal C++ compiler error was captured before the process aborted. This pattern is consistent with host/WSL resource or service failure under high parallel build load, although the evidence does not prove OOM specifically.

## FIX1

Package:
`SOULGOLD_RECOMP_HANDOFF_S0_D1C_C3H_CONTROL_AB_FIX1_BUILD_THROTTLE_20260830.zip`

SHA-256:
`1d2ce9c8ae87aa0283700d1d398461d123d032ad298fe8a79b80f73b33c9f23c`

The C3H-controlled experiment is unchanged. Only build execution is hardened:

1. runner/compiler build first tries `-j4`;
2. on failure retries `-j2`;
3. on failure retries `-j1`;
4. each failed attempt records WSL memory/CPU resource snapshots;
5. the existing PowerShell parser/preflight gate remains required before any build/game action.

## A/B interpretation remains unchanged

Candidate A:
- unpatched C3H host path
- 240x160 / scale 1
- LCD OFF

Candidate B:
- exact same runner binary
- 480x320 / scale 2
- LCD OFF

Known failing reference C:
- D1B/P1.1
- scale 2
- LCD/interframe ON
- battle very laggy

Decision:
- A smooth + B smooth => P1 LCD/interframe host patch implicated
- A smooth + B lag => scale2/window host path implicated
- A lag => reconstructed host/runtime differs from sealed C3H; stop presentation tuning and diff runtime lineage
