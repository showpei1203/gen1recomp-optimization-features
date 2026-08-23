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
Version: `v0.2.18b`

Formal hashes:
- PMD `main.lua`: `b67b2f57bb955eea1834210a471ddf0c2ef20cd50f82c145e074c9a5e0d36d46`
- PMD `manifest.json`: `f75aca6b3d0a98c56b131cc3cb6730aba772f9499df581b9cc3fdeaf261f1563`
- StadiumFxPlayer: `7e40e164f24e89c0671d6ef8a0b4fd21f68b0443232f68410b2070f100c17cd7`
- Promotion-candidate ZIP: `07ee27d1aab71174bd3051e8ff6db2d2b57e4f9da20f022be936e9a7cd59b637`
- Promotion-smoke evidence ZIP: `be4a06e20ad0bf468adca0e4cda412930791ce03a310b11b9b96ce6b1d391e94`

Canonical document:
`docs/PMD_SBFX_MOVE_PRESENTATION_FORMAL_AUTHORITY_v0.2.18b_20260823.md`

This supersedes `v0.2.17e` for the PMD/StadiumBattleFX integration lane. v0.2.17e remains historical/inherited documentation.

v0.2.18b adds Self-Support Source Ownership IV: true self / own-side support VFX are source-only; opponent target VFX ownership is forbidden; Reflect / Light Screen / Barrier / Recover passed runtime and AYN Thor visual acceptance.

## Current development lane

`Kanto Dynamic Weather + Wild Skies integration`

Known starting environment from the v0.2.18b AYN Thor smoke:
- DRAMATIC_SHAPE `1.8.2`
- Kanto First Person THOR compatibility `1.60.0b-thor`
- Wilds of Kanto / overworld_wild_spawns `2.1.0`
- StadiumBattleFX `2.1.8.1`
- PMD `0.2.18b`

Kanto Dynamic Weather `1.0.3` upstream declares DRAMATIC_SHAPE `>=1.7.2 <1.8.0`. The current DS 1.8.2 stack therefore requires a verified compatibility bridge rather than a dependency-range-only change.

## Historical recovery / evidence packages to migrate

1. `GEN1RECOMP_EMERGENCY_RECOVERY_SPEED_1X_3D_BASELINE_20260816.zip`
2. `GEN1RECOMP_KANTO5_HANDOFF_S3_S5_TTO043_FORMAL_20260816.zip`
3. `GEN1RECOMP_S3_1_RUNTIME_DRIFT_COLLECTOR_20260815.zip`
4. `GEN1RECOMP_DEBUG_20260815_124645.zip`
5. `S6_0d_WILD_SOURCE_BASELINE_EVIDENCE_20260816_201153.zip`
6. `S6_1a_FAILURE_20260816_210123.zip`

These names are migration targets, not automatically formal full-binary baselines. The exact current playable package must be pinned by SHA-256 after binary import and device confirmation.

## Full runnable binary baseline state

`PENDING_BINARY_IMPORT_AND_HASH_PIN`
