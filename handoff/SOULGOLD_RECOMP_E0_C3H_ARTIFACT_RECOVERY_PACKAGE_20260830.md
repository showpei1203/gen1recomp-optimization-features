# SoulGoldRecomp E0 C3H Artifact Recovery Package

Date: 2026-08-30

Package:
`SOULGOLD_RECOMP_HANDOFF_S0_E0_C3H_DIRTY_ARTIFACT_RECOVERY_20260830.zip`

SHA-256:
`cacb78e2d8cd7982cb7f0e7adc2522661a71a273373506036701d3b3b8491812`

Purpose:
- stop reconstructing C3H from Git HEAD alone;
- recover a surviving old C3H executable if available;
- otherwise preserve and rebuild from the original dirty gbarecomp working tree;
- capture git status, worktree list, critical runtime diff, source hashes and executable inventory;
- test one battle with no D1 static roots and no P1 LCD/interframe patch.

Launcher:
`tools\\soulgold_recomp\\START_S0_E0_C3H_RECOVERY.bat`

Expected preflight:
`HANDOFF_PREFLIGHT=PASS`

The handoff intentionally contains no PowerShell execution path.

Local package validation before delivery:
- Bash syntax PASS;
- C3F patch Python syntax PASS;
- BAT contains no `powershell.exe` invocation;
- ZIP integrity PASS.
