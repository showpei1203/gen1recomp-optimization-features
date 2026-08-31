# CURRENT HANDOVER — RMXP Pokémon zh-TW / Pokémon Anil

Latest saved checkpoint: **Pokémon Anil DE 1.0.23 zh-TW v0.8.5 INTERNAL**

Read first:
- Versioned handover: `ANIL_V085_HANDOVER_20260831.md`
- Versioned handover commit: `a70926f37c132a3a46f2f32b1e4ab1b2fa15bb5a`
- Mandatory handover policy: `PROJECT_HANDOVER_POLICY_v1_20260831.md`
- Reusable localization rules: `REUSABLE_ZH_TW_LOCALIZATION_RULES_v1_6_20260831.md`
- Rules v1.6 commit: `24ba65803cb3061913b6bf1bd18698f7020e5972`
- Translation lessons: `ANIL_TRANSLATION_LESSONS_V085_20260831.md`

Artifact:
- `ANIL_DE_1.0.23_ZH_TW_v0.8.5_INTERNAL_HANDOVER_M72_80_QA16_20260831.zip`
- SHA256: `81d590b02496a350112ada835b08b8a642ee0f55b5f89f92d3191522b307ea06`
- Drive ID: `1BGbIIJrHkPKcYFkY_YAhk31MyctiD6AL`

Completed in v0.8.5:
- Map 72–80 EVENT_TEXT: 212/212 human reviewed.
- 436 runtime DAT values changed vs v0.8.4 after map polish + global/source-aware cleanup.
- Source-aware QA v1.6 introduced and all current HARD/WARN findings cleared.
- Remaining `full_mt_argos_s2twp`: 9,285.

Current QA state:
- 21,438 manifest rows
- 21,437 non-empty zh_tw
- source-aware/known-bad lint v1.6: HARD=0, WARN=0
- manifest -> DAT mismatches=0
- Marshal structure issues=0
- ZIP integrity=PASS

SEALED:
- Do not translate resource paths, UI suffixes or opaque internal labels.
- Preserve battle HUD / Move menu / Summary UI repairs.
- Preserve CJK formatter wrapping and exact-version MapInfos.
- DAT patch must be key-based.
- `Pokévial` / `PokéRider` are protected custom brands.
- `P0/P1/P2/P3` remain unchanged unless UI semantics are proven.

Current exact next start:
1. Resume from Map 81 EVENT_TEXT review.
2. Run repeated exact-English phrase discovery before per-map edits.
3. Run source-aware lint after every batch and clear HARD/WARN before checkpoint.
4. Merge new public-v0.7 device feedback before next public candidate.
5. Refresh HANDOVER at every development checkpoint, including INTERNAL checkpoints.
