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

**PMD + StadiumBattleFX Move Presentation Authority: v0.2.17e FORMAL AUTHORITY (2026-08-23).**

Canonical authority document:
`docs/PMD_SBFX_MOVE_PRESENTATION_FORMAL_AUTHORITY_20260823.md`

Formal production hashes:
- PMD `main.lua`: `726cf94166333ea49512e05925fad3f6925ff796c669bd729d29801125103490`
- PMD `manifest.json`: `b2b0844ba43dbdc05efd57453353ad5c6f1aca003b470c53e90037f0b0d5009c`
- StadiumFxPlayer: `5d5d774994f107c567d413f4b195a6806875a729d5a1e7578b83c57e782a3c4f`
- Formal Authority archive ZIP: `b1ae2db1f6c1d66c147210af9715f0c89c415793cb9d1a9c07b879865c461526`

This formal authority supersedes `v0.2.13a` for the PMD/StadiumBattleFX integration lane. The v0.2.13a document remains historical authority for the Integration I closure and its inherited rules.

This source authority does not by itself replace the still-separate full runnable binary baseline authority.

## Lane separation

Optimization and new feature work must be developed and accepted independently first. Combined candidates live under Integration and require a second integrated regression pass.

## Baseline protection

Never modify the only known-good runnable baseline in place. Preserve exact source packages and hashes before experimentation.

Future PMD battle-presentation work must branch from the exact v0.2.17e formal hashes above and preserve its sealed rules unless a later authority explicitly supersedes them.
