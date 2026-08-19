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

## Lane separation

Optimization and new feature work must be developed and accepted independently first. Combined candidates live under Integration and require a second integrated regression pass.

## Baseline protection

Never modify the only known-good runnable baseline in place. Preserve exact source packages and hashes before experimentation.
