# Android MOD Discovery / ADB Gate Authority

Date: 2026-08-22
Status: tooling authority captured from StadiumBattleFX v0.2.06b integration

## Incident chain

The StadiumBattleFX integration verifier required four tooling revisions before installation could proceed:

1. TOOLFIX1 exposed that the verifier had been written as an internal `call` gate and silently exited when launched directly.
2. TOOLFIX2 showed the source gate was unnecessarily narrow: Thor was on exact sealed PMD v0.2.02a, which is a valid accepted source, but the verifier only accepted v0.2.04a.
3. TOOLFIX3 found the correct Android MOD root and confirmed `STADIUM_BATTLE_FX` was present as a direct child, but all 54 manifest probes returned `JSON_PARSE_FAIL`. This proved a Windows BAT + embedded PowerShell `ConvertFrom-Json` parser defect rather than missing or invalid MOD installations.
4. TOOLFIX4 removed the fragile parser and directly probed `mods/STADIUM_BATTLE_FX/manifest.json` using file existence plus raw manifest token/version checks. It correctly detected StadiumBattleFX 2.1.8.1, verifier passed, and the v0.2.06b installer completed.

## Required rules for future Thor / Android MOD tooling

- Do not guess the MOD root. Use the Gen1Recomp Android external-files root confirmed by runtime evidence, or discover and log it explicitly.
- Mirror Gen1Recomp Launcher behavior. Prefer `mods/<manifest.id>/manifest.json` direct probes when the formal MOD id is known.
- Do not invent recursive discovery when the application itself loads direct children.
- Do not use PowerShell `ConvertFrom-Json` embedded inside BAT `for /f` as the primary manifest gate. The 2026-08-22 incident produced 54/54 false parse failures.
- Prefer fail-closed, explainable checks: manifest exists, expected id/name token exists, accepted version token exists.
- Always log the resolved MOD root, direct children, manifest path, and proof used for acceptance.
- A verifier launched by a human must always remain visible on PASS or FAIL and must write a result log. No silent `exit /b` behavior.
- Source gates must accept every exact sealed source explicitly approved for the integration path, not merely the latest Formal build.
- Before any installer write, save an exact pre-integration snapshot and make rollback restore that actual source.
- If a MOD is visible and enabled in the Gen1Recomp Launcher but the verifier cannot find it, classify the first failure as a discovery/tooling defect until filesystem evidence proves otherwise. Do not instruct repeated reinstall attempts first.

## Current successful proof

TOOLFIX4 accepted:
- PMD source: exact v0.2.02a
- DRAMATIC_SHAPE: exact 1.8.2 sealed hashes
- THOR Battle UI: exact 0.3.41 sealed hash
- StadiumBattleFX: 2.1.8.1

The v0.2.06b installer then reported `INSTALL PASS` and hard-proofed zero legacy Custom GBC runtime token refs plus zero legacy GBC data/assets in the installed PMD candidate.

This document is intended to prevent regression in future ADB BAT verifiers and installers across the Gen1recomp project.
