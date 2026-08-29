# SoulGoldRecomp S0-C3H Fix5 — Zero-Match Gate Correction

Date: 2026-08-30
Branch: `feature/soulgold-recomp-s0`

## Evidence reviewed

`SOULGOLD_S0_C3H_EVIDENCE_20260830_024828.zip`

## What Fix4 actually did

Fix4 successfully passed the PowerShell parser precheck, rebuilt the candidate GBARecomp recompiler, applied the previously confirmed ROM-mirror runtime patch, prepared the separate candidate runner tree, and installed the continuation-root overlay.

The Fix4 overlay itself is correct and contains exactly two `[[extra_func]]` declarations and zero `[[resume_range]]` declarations:

- `0x03000000`, ARM, source `0x09E864A0`, `IntrMain`
- `0x0300012C`, ARM, source `0x09E865CC`, `IntrMain_RetAddr`

## Why the game still did not launch

Fix4 stopped before `gba_recompile` during its own overlay sanity check:

`STEP=VERIFY_C3H_FIX4_OVERLAY`

`grep -c [[resume_range]] ... :: 0`

GNU `grep -c` prints a numeric count of `0` when there are no matches, but exits with status 1. The Fix4 sanity check used the generic `Scalar()` wrapper, which treats every non-zero process status as a failure. Therefore the desired state, zero `resume_range` declarations, was incorrectly rejected.

This means the Fix4 continuation-root control-flow model has **not yet reached codegen** and is neither confirmed nor disproved by this run.

## Fix5

Fix5 changes only the harness sanity check:

- overlay count checks now use the existing `GrepCount()` helper;
- `GrepCount()` treats grep status 1 as the valid zero-match case;
- expected overlay gate is:
  - `OVERLAY_EXTRA_FUNC_COUNT=2`
  - `OVERLAY_RESUME_RANGE_COUNT=0`
  - `C3H_FIX5_OVERLAY_GATE=PASS`

No address, source mapping, ROM-mirror behavior, IRQ behavior, audio behavior, or sealed baseline changes.

## Candidate model retained

- C3F ROM-mirror native entry correction remains enabled in the separate candidate GBARecomp worktree.
- `IntrMain` remains a real ARM native root at `0x03000000` from ROM source `0x09E864A0`.
- `IntrMain_RetAddr` remains a real ARM native continuation root at `0x0300012C` from ROM source `0x09E865CC`.
- No `resume_range` is used.
- Codegen hard gate still requires both roots as `resume=0` and rejects a `resume=1` dispatch at `0x0300012C`.

## Sealed state

- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 = FORMAL PASS / SEALED
- S0-C2 = FORMAL PASS / SEALED
- S0-C3 = FAIL / NOT PROMOTED
- S0-C3G = STATIC PROBE PASS
- S0-C3H Fix4 = HARNESS FAIL BEFORE CODEGEN
- S0-C3H Fix5 = next candidate

## Permanent project requirements

1. Every meaningful checkpoint ships a downloadable handoff.
2. Final product ships Traditional Chinese `zh-Hant-TW` through an external localization/glyph layer with English fallback.
3. Primary finished hardware target is AYN THOR / Android ARM64; correctness fixes must remain platform-neutral C/C++ unless isolated behind a host adapter.
