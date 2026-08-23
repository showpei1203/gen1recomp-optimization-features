# Baseline Status

## Known lineage

- Gen1Recomp version lineage: `0.1.75`
- Working game lineage: `Kanto.5`
- THOR optimization lineage: `THOR Performance v1.0`
- Known setting: `area_dexnav=false`

## Formal lane authorities

### PMD + StadiumBattleFX Move Presentation Authority

Status: **FORMAL AUTHORITY**

Promoted: `2026-08-23`

Version: `v0.2.17e`

Formal hashes:
- PMD `main.lua`: `726cf94166333ea49512e05925fad3f6925ff796c669bd729d29801125103490`
- PMD `manifest.json`: `b2b0844ba43dbdc05efd57453353ad5c6f1aca003b470c53e90037f0b0d5009c`
- StadiumFxPlayer: `5d5d774994f107c567d413f4b195a6806875a729d5a1e7578b83c57e782a3c4f`
- Promotion-candidate ZIP: `95658c9f4bf18025c2b1ae6c479f65c532e64833cc0660918ed6ad675cbab781`
- Promotion-smoke evidence ZIP: `ec062594438447b7c1aca219ce46c3c7178bf95349235874dd4e5cbfbf7c1563`
- Formal Authority archive ZIP: `b1ae2db1f6c1d66c147210af9715f0c89c415793cb9d1a9c07b879865c461526`

Canonical document:
`docs/PMD_SBFX_MOVE_PRESENTATION_FORMAL_AUTHORITY_20260823.md`

This supersedes `v0.2.13a` for the PMD/StadiumBattleFX integration lane. The v0.2.13a Integration I authority remains historical/inherited documentation.

This is a formal **integration-lane source authority**. It does not by itself claim that the full runnable Gen1Recomp binary has been imported and hash-pinned in Drive.

## Historical recovery / evidence packages to migrate

Priority order for legacy binary migration into Google Drive:

1. `GEN1RECOMP_EMERGENCY_RECOVERY_SPEED_1X_3D_BASELINE_20260816.zip`
2. `GEN1RECOMP_KANTO5_HANDOFF_S3_S5_TTO043_FORMAL_20260816.zip`
3. `GEN1RECOMP_S3_1_RUNTIME_DRIFT_COLLECTOR_20260815.zip`
4. `GEN1RECOMP_DEBUG_20260815_124645.zip`
5. `S6_0d_WILD_SOURCE_BASELINE_EVIDENCE_20260816_201153.zip`
6. `S6_1a_FAILURE_20260816_210123.zip`

These names are migration targets, not automatically formal full-binary baselines. The exact current playable package must be pinned by SHA-256 after binary import and device confirmation.

## Full runnable binary baseline state

`PENDING_BINARY_IMPORT_AND_HASH_PIN`
