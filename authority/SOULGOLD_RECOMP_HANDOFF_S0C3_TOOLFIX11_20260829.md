# SoulGoldRecomp S0-C3 Toolfix11 Handoff

## Sealed baseline
- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 CART BOOT / RENDER = FORMAL PASS / SEALED
- S0-C2 TITLE FLOW / REAL START INPUT = FORMAL PASS / SEALED

## Failure observed
The first S0-C3 attempt failed before runner launch because PowerShell/WSL stripped nested quotes from the Python DISPLAY probe, causing `NameError: name 'DISPLAY' is not defined`.

## Fix
- remove Python from GUI env probing;
- use `wsl.exe printenv DISPLAY` and `WAYLAND_DISPLAY` directly;
- treat printenv exit 1 as a normal unset variable;
- no changes to sealed runner/ROM/BIOS or interactive acceptance policy.

## Run
Use `tools/soulgold_recomp/START_S0_C3.bat`.

Default controls:
- A=X
- B=Z
- Start=Enter
- Select=Right Shift
- D-pad=Arrow keys
- L=C
- R=V

On clean close the script collects framebuffer, coverage, misses, present cadence and isolated test save, then packages `SOULGOLD_S0_C3_EVIDENCE_*.zip`.

## Permanent requirements
1. Every meaningful checkpoint ships a user-downloadable handoff.
2. Final product must ship Traditional Chinese `zh-Hant-TW` through an external localization/glyph layer with English fallback.
