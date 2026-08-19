# Gen1recomp Optimization / Features

Persistent development repository for Gen1recomp optimization, compatibility work, and feature expansion.

## Authority model

- **Google Drive**: binary baseline, runnable builds, test packages, logs, handoff packages, large assets, archives.
- **GitHub**: source/config/tooling changes, reviewable patches, documentation mirrors, history.
- **Linear**: intentionally not used for this project.

## Development lanes

1. `optimization/` — startup, map transition, rendering, caching, loading, performance.
2. `features/` — new gameplay or presentation mechanisms.
3. `integration/` — MOD compatibility and combined candidates.
4. `tests/` — regression harnesses, profiling helpers, validation scripts.
5. `docs/` — project authority and engineering notes.

## Baseline rule

Do not overwrite or silently mutate the current playable baseline. Every optimization or feature must be tested as a candidate and promoted only after regression, visual compatibility, and device acceptance.

Current legacy baseline lineage: Gen1Recomp 0.1.75 / Kanto.5 with THOR Performance v1.0. Exact binary baseline is being migrated into Google Drive and will be pinned by hash after import.
