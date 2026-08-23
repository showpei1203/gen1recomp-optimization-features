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

**PMD + StadiumBattleFX Move Presentation Authority: v0.2.18b FORMAL AUTHORITY (2026-08-23).**

Canonical authority document:
`docs/PMD_SBFX_MOVE_PRESENTATION_FORMAL_AUTHORITY_v0.2.18b_20260823.md`

Formal production hashes:
- PMD `main.lua`: `b67b2f57bb955eea1834210a471ddf0c2ef20cd50f82c145e074c9a5e0d36d46`
- PMD `manifest.json`: `f75aca6b3d0a98c56b131cc3cb6730aba772f9499df581b9cc3fdeaf261f1563`
- StadiumFxPlayer: `7e40e164f24e89c0671d6ef8a0b4fd21f68b0443232f68410b2070f100c17cd7`
- Promotion candidate ZIP: `07ee27d1aab71174bd3051e8ff6db2d2b57e4f9da20f022be936e9a7cd59b637`
- Promotion smoke evidence ZIP: `be4a06e20ad0bf468adca0e4cda412930791ce03a310b11b9b96ce6b1d391e94`

This formal authority supersedes `v0.2.17e` for the PMD/StadiumBattleFX integration lane. The v0.2.17e document remains historical/inherited authority.

New sealed rule added by v0.2.18b: true self / own-side support moves use source-only visual ownership; opponent target anchors are forbidden for their self-support VFX. Reflect / Light Screen / Barrier / Recover passed runtime and user visual acceptance.

This source authority does not by itself replace the still-separate full runnable binary baseline authority.

## Current development lane

**Kanto Dynamic Weather + Wild Skies integration** begins from the exact v0.2.18b formal hashes above.

Integration constraints:
- do not regress PMD/Stadium battle presentation ownership;
- preserve DRAMATIC_SHAPE 1.8.2 and Kanto First Person / THOR compatibility unless explicitly superseded;
- Kanto Dynamic Weather 1.0.3 upstream only declares DRAMATIC_SHAPE `>=1.7.2 <1.8.0`, so DS 1.8.2 requires a verified compatibility bridge rather than a dependency-range bypass;
- Wild Skies remains an overworld air-entity lane; weather integration must not steal its encounter/battle ownership;
- combined render integration requires explicit occlusion, draw-order, transition, performance, and AYN Thor validation.

## Lane separation

Optimization and new feature work must be developed and accepted independently first. Combined candidates live under Integration and require a second integrated regression pass.

## Baseline protection

Never modify the only known-good runnable baseline in place. Preserve exact source packages and hashes before experimentation.

Future PMD battle-presentation work must branch from the exact v0.2.18b formal hashes above and preserve its sealed rules unless a later authority explicitly supersedes them.
