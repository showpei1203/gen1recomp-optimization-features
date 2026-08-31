# Pokémon Anil zh-TW v0.7.5 INTERNAL Story Polish Map 41–54

Baseline: v0.7.4 INTERNAL REUSABLE QA

## Scope
- Map 41–54 EVENT_TEXT: 186 rows manually reviewed.
- 152 EVENT_TEXT values changed.
- 20 additional cross-section official terminology / MT corruption fixes.
- DAT values changed vs v0.7.4: 172.
- Scripts.rxdata and MapInfos.rxdata unchanged from v0.7.4.

## Quality / QA
- Manifest entries: 21,438.
- Remaining `full_mt_argos_s2twp`: 9,900.
- Reusable quality lint v1.1 HARD issues: 0.
- Marshal section/type/key structure issues: 0.
- ZIP integrity: PASS.

## Reusable process changes
1. English-edition `translation` is the semantic/token authority when source-language text diverges.
2. DAT patch is now section/map/key based, never old-value global replacement.
3. Proper-noun and Pokémon-term MT corruptions are data-driven in `quality/known_bad_patterns.tsv`.
4. `toolchain/zh_tw_quality_lint.py` accepts `--patterns` and has expanded control token coverage.

## Artifact
- File: `ANIL_DE_1.0.23_ZH_TW_v0.7.5_INTERNAL_STORY_POLISH_M41_54_20260831.zip`
- SHA256: `684a2e73ea4ac1e7ed1157bba672211c4d7ff59c6ec6595318118d54c9486a19`
- Google Drive ID: `1edN2PbcAabOEfzSWrOYc_G15w_K8k5jX`
- Drive parent: candidates `1kPLTpmI_0-zemGQmiOXaZVmNM8d-WnYx`

## Next
Continue manual story polish from Map 56 onward. Map 55 has no EVENT_TEXTS in the manifest. Merge user v0.7 field-test regressions into the next public candidate instead of forcing frequent test installs.
