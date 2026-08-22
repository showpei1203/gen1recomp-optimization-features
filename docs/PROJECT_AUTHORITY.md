# Gen1recomp Project Authority

## Persistent sources

### Google Drive
Canonical home for:
- current runnable binary baseline
- test builds
- evidence / performance / regression / visual logs
- handoff packages
- large assets and archives

Drive project root: `Gen1recomp`

### GitHub
Canonical home for:
- source code and config changes
- reviewable patches
- test/profiling tooling
- lightweight documentation mirror
- commit history

Repository: `showpei1203/gen1recomp-optimization-features`

### Linear
Not used for Gen1recomp.

## Promotion rule

A candidate becomes formal baseline only when all relevant checks pass:
1. runtime functional regression
2. visual compatibility
3. map / render stability
4. input authority sanity
5. performance comparison where optimization is claimed
6. AYN Thor device acceptance when device-specific behavior is involved

A user may explicitly approve a narrowly-scoped deterministic promotion exception after the exact coordinate/code path has been statically proven. Such an exception must be recorded in the dedicated Formal Authority document and must never be silently treated as missing evidence later.

## Current formal integration authority

**PMD + StadiumBattleFX Integration I: v0.2.13a FORMAL AUTHORITY (2026-08-22).**

Canonical authority document:
`docs/PMD_SBFX_INTEGRATION_FORMAL_AUTHORITY_20260822.md`

Formal production hashes:
- PMD `main.lua`: `7365476702ab294ad75b5c52e9e69dff9710c608ea57dc806e540e7b1650d406`
- PMD `manifest.json`: `20eec657f82f85d486bcd25b714e03d0d4ac4873dd638cf363d75879ee718c4a`
- StadiumFxPlayer: `7c8c52373f894b8b821f582b875748631897d8daf89366d0aa49ba7af668b279`

This formal authority supersedes the former `v0.2.04a` formal baseline for the PMD/StadiumBattleFX integration lane only. It does not by itself replace the still-separate full runnable binary baseline authority.

## Lane separation

Optimization and new feature work must be developed and accepted independently first. Combined candidates live under Integration and require a second integrated regression pass.

## Baseline protection

Never modify the only known-good runnable baseline in place. Preserve exact source packages and hashes before experimentation.

Future PMD battle-presentation work must branch from the exact v0.2.13a formal hashes above and preserve its sealed rules unless a later authority explicitly supersedes them.
