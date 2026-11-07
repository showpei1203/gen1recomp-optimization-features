# Gen1recomp Optimization / Features

> **GLOBAL HARD RULES 001 (2026-11-07)**：開發工作檔案、原始碼、ZIP、測試證據與備份只永久保存 **Google Drive／GitHub**，使用者 PC 僅必要安裝；若非得產生 PC 臨時檔，必須先取得使用者授權、雲端回讀驗證後清除。先讀 [全專案最高規範](https://docs.google.com/document/d/1NftePmIsggrhnfPcZTZS2G6YBka2yBy_fdw-NBT5D8Y/edit) 及本儲存庫的 [AGENTS.md](AGENTS.md)。歷史封版/正式測試結果不因此變更。

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
