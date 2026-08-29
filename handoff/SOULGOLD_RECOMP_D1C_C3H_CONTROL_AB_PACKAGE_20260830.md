# SoulGoldRecomp D1C C3H Controlled A/B Package

Date: 2026-08-30

Package:
`SOULGOLD_RECOMP_HANDOFF_S0_D1C_C3H_CONTROL_AB_20260830.zip`

SHA-256:
`a7d358be202ac870fe8fe8802f1bbc1275a1c98ed5ae03fc5bdd3dce0e99b9d8`

Purpose:
- use sealed C3H as the known-good battle control;
- rebuild without the P1 LCD host patch;
- no D1 FastUnsafeCopy32 static root;
- no D1 SoundMainRAM static root;
- one runner binary, two presentation runs.

Candidate A:
- 240x160 / scale 1;
- LCD OFF;
- interframe OFF.

Candidate B:
- same runner binary;
- 480x320 / scale 2;
- LCD OFF;
- interframe OFF.

Known failing reference C:
- D1B/P1.1;
- C3H guest roots;
- 480x320 / scale 2;
- LCD + interframe ON;
- user reports battle very laggy.

Decision:
- A smooth + B smooth => P1 LCD/interframe host patch implicated;
- A smooth + B lag => scale2/window host path implicated;
- A lag => reconstructed host/runtime differs from sealed C3H; stop presentation tuning and diff runtime lineage.

Package-level checks performed before delivery:
- bash syntax PASS;
- Python syntax PASS;
- generated-package file sanity PASS;
- static PowerShell quote/bracket balance PASS;
- ZIP integrity PASS.

The Windows launcher still performs the authoritative PowerShell parser preflight using `System.Management.Automation.Language.Parser` before any build/game action.
