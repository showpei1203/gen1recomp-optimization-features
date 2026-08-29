# SoulGoldRecomp S0-C3G Fix1 — PowerShell HOME collision

Date: 2026-08-29
Branch: `feature/soulgold-recomp-s0`

## Observed failure

C3G exited before any ELF/IWRAM analysis with:

`無法覆寫 HOME 變數，因為它是唯讀或常數。`

## Root cause

PowerShell variable names are case-insensitive. The C3G harness assigned to `$home`, which collides with the built-in read-only automatic variable `$HOME`.

No game was launched and no sealed artifact was modified.

## Fix1

- rename `$home` to `$WslHomePath`;
- scan the harness for assignments to other PowerShell automatic variables before packaging;
- retain exact C3G targets `0x0300012C` and `0x030016AC`;
- retain static-only policy: no game launch, no runtime mutation.

## State

- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 = FORMAL PASS / SEALED
- S0-C2 = FORMAL PASS / SEALED
- S0-C3 = FAIL / NOT PROMOTED
- S0-C3F = FAIL / NOT PROMOTED
- S0-C3G = probe pending after Fix1

Primary finished target remains AYN THOR / Android ARM64. Every meaningful checkpoint must ship a downloadable handoff, and final release must include Traditional Chinese `zh-Hant-TW`.
