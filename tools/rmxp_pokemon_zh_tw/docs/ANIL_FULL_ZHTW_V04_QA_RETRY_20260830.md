# Pokémon Anil DE 1.0.23 — Full zh-TW v0.4 QA retry

Date: 2026-08-30
Primary runtime: AYN THOR + JoiPlay

## Completed full-MT run

Workflow run `33300147895` completed the full translation stage for the Essentials v21.1 union manifest.

Observed translation stats:

- union entries: 21,438
- non-empty `zh_tw`: 21,437
- unique MT segments: 19,388
- translation failures: 0
- rows containing CJK output: 21,304

The strict placeholder QA gate then reported 18 mismatches and intentionally stopped packaging. No candidate was promoted from this failed QA run.

## Correct response

Do not weaken the final release gate. The next build preserves the intermediate MT artifact even when placeholder QA reports issues, so the exact 18 rows can be inspected and repaired instead of losing the completed one-hour translation workspace.

Retry workflow commit: `98e3684dced8128a3067c04c549eea76851e2891`.
Retry workflow run: `33303064682`.

## Finalizer order after artifact retrieval

1. Load full-MT 21,438-entry manifest.
2. Inspect and repair all placeholder/control-code mismatches to zero.
3. Treat source/translation-empty rows as intentional empty values, not missing translation.
4. Overlay curated v0.3 values (5,222 entries) so MT never replaces validated UI/official terminology.
5. Overlay exact-match official zh-Hant Pokédex/move/ability/item description corpus where available.
6. Re-run placeholder QA with zero mismatches required.
7. Rebuild `messages_zh_tw_game.dat` from the English DAT baseline.
8. Keep the already validated Traditional Chinese language/CJK font patch in `Scripts.rxdata`.
9. Compare Marshal structure and produce hashes/logs.
10. Package `ANIL_DE_1.0.23_ZH_TW_FULL_BETA_v0.4_20260830.zip` for AYN THOR/JoiPlay testing.

The v0.3 package remains the quality authority for its 5,222 populated `zh_tw` rows until explicitly superseded by reviewed translations.
