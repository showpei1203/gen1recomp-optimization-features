# Baseline Status

## Known lineage

- Gen1Recomp version lineage: `0.1.75`
- Working game lineage: `Kanto.5`
- THOR optimization lineage: `THOR Performance v1.0`
- Known setting: `area_dexnav=false`

## Formal lane authorities

### PMD + StadiumBattleFX Integration I

Status: **FORMAL AUTHORITY**

Promoted: `2026-08-22`

Version: `v0.2.13a`

Formal hashes:
- PMD `main.lua`: `7365476702ab294ad75b5c52e9e69dff9710c608ea57dc806e540e7b1650d406`
- PMD `manifest.json`: `20eec657f82f85d486bcd25b714e03d0d4ac4873dd638cf363d75879ee718c4a`
- StadiumFxPlayer: `7c8c52373f894b8b821f582b875748631897d8daf89366d0aa49ba7af668b279`
- Promotion-candidate delivery ZIP: `07970c40683f5c70da3b25602c8661ac13cc7aa1673d1036d3f541c97b38902e`

Canonical document:
`docs/PMD_SBFX_INTEGRATION_FORMAL_AUTHORITY_20260822.md`

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
