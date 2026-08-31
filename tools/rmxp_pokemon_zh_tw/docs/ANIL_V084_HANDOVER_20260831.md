# Pokémon Anil zh-TW v0.8.4 INTERNAL HANDOVER

## Identity
- Project: Pokémon Anil DE 1.0.23 Traditional Chinese localization
- Checkpoint: v0.8.4 INTERNAL — Map71 + exact-English template cleanup
- Date: 2026-08-31
- Status: INTERNAL CHECKPOINT

## Authority / baseline
- Game authority: Pokémon Anil DE 1.0.23 English / Essentials v21.1.
- Runtime lineage preserves v0.6/v0.7 UI repairs, CJK wrapping, MapInfos and Summary memo fix.
- Immediate data baseline: v0.8.2.1 work master/DAT (Maps 1–70 polish lineage).
- English-edition `translation` is semantic/control-code authority; source-language text is context only.

## Artifact
- Filename: `ANIL_DE_1.0.23_ZH_TW_v0.8.4_INTERNAL_HANDOVER_M71_TEMPLATE_20260831.zip`
- SHA256: `970cfdf00e60ef4dfe4f91275d3fef0fdb2788d515bde6e1df381f3656b263f3`
- Size: 3,944,307 bytes
- Drive ID: `1CaOcA6j5xRrohGST3JA1W21cZdjpcsMR`
- Drive parent: candidates `1kPLTpmI_0-zemGQmiOXaZVmNM8d-WnYx`

## Completed this checkpoint
1. Cleared the last v1.4 HARD lint residue: `波克矇` -> natural `寶可夢` Pokédex sentence.
2. Map 71 EVENT_TEXT: 39/39 manually reviewed, 35 values changed.
3. Added 29 vetted exact-English phrase templates.
4. Exact-English templates matched 410 rows and changed 393 rows.
5. Professor Samson legendary-hunt templates standardized across 222 rows to `成也・大木博士`.
6. Photographer Seymour repeated event templates standardized across 179 rows.
7. Nine Poké Ball feature/item strings standardized to Taiwan terminology, including `精靈球` and `月之石`.
8. Remaining `full_mt_argos_s2twp`: 9,507 rows.

## QA
- Manifest entries: 21,438.
- Non-empty zh_tw: 21,437 (one source entry intentionally empty).
- known-bad HARD lint v1.5: 0 issues.
- Placeholder/Ruby/HTML/control-token sequence: 0 mismatch via reusable lint.
- Keyed DAT apply: 393 replacements for v0.8.4 delta.
- Manifest -> DAT verification: 21,437 checked, 0 mismatch.
- Marshal structure compare vs previous DAT: changed=393, issues=0.
- ZIP integrity: PASS.
- AYN THOR/JoiPlay: v0.8.4 INTERNAL not yet physically validated.

## SEALED / do not regress
- Never translate Graphics/Audio/Data/Plugins resource paths.
- Never translate Modular UI internal suffixes such as `memo`.
- Preserve v0.6 battle HUD / move menu / Summary UI repairs.
- Preserve v0.7 CJK formatter wrapping; do not reintroduce global Bitmap draw_text hooks.
- Map titles remain sourced from localized exact-version MapInfos.rxdata.
- DAT changes are key-based; never global-replace an old Chinese value.
- Repeated human templates may be global only when keyed by exact English-edition `translation` phrase.
- Official Taiwan Pokémon terminology wins over machine transliteration.
- Every development turn/checkpoint from this point MUST prepare a handover according to `PROJECT_HANDOVER_POLICY_v1_20260831.md`.

## Known issues / unverified
- User is still physically testing public v0.7; later feedback must be merged before the next public candidate.
- White-fog behavior after protagonist name entry has not been revalidated on this latest lineage. Do not claim formal fix without device confirmation.
- 9,507 rows still retain original Argos-MT status and need continued prioritised human polishing.

## Next exact starting point
1. Continue EVENT_TEXT human review from Map 72 onward, prioritising maps with remaining `full_mt_argos_s2twp` rows.
2. Run repeated-phrase discovery before map-by-map work so duplicated feature dialogue is fixed once through exact-English templates.
3. Merge any new v0.7 device feedback before publishing the next public test candidate.
4. Refresh `docs/CURRENT_HANDOVER.md` and include `handoff/CURRENT_HANDOVER.md` in every subsequent ZIP.

## Resume files
- `translation/ANIL_DE_1.0.23_ZH_TW_MASTER_v0.8.4.tsv`
- `Data/messages_zh_tw_game.dat`
- `translation/V083_PATCH.json`
- `translation/V084_EXACT_ENGLISH_TEMPLATE_PATCH.json`
- `reusable_rules/known_bad_patterns_v1_5.tsv`
- `reusable_rules/zh_tw_quality_lint.py`
- `reusable_rules/REUSABLE_ZH_TW_LOCALIZATION_RULES_v1_5.md`
- `evidence/V084_MANIFEST_DAT_VERIFY.txt`
- `evidence/V084_STRUCTURE_QA.txt`
