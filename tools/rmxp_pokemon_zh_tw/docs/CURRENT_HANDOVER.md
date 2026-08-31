# CURRENT HANDOVER — RMXP Pokémon zh-TW / Pokémon Anil

Latest saved checkpoint: **Pokémon Anil DE 1.0.23 zh-TW v0.8.7 INTERNAL**

Read first:
- Versioned handover: `ANIL_V087_HANDOVER_20260831.md`
- Mandatory handover policy: `PROJECT_HANDOVER_POLICY_v1_20260831.md`
- Reusable localization rules: `REUSABLE_ZH_TW_LOCALIZATION_RULES_v1_7_20260831.md`
- Translation lessons: `ANIL_TRANSLATION_LESSONS_V087_20260831.md`

Artifact:
- `ANIL_DE_1.0.23_ZH_TW_v0.8.7_INTERNAL_HANDOVER_M81_85_QA17_20260831.zip`
- SHA256: `e70ef156bcd3816705f397af7985b2647f419bc828abf2312748214ada7abe19`
- Drive ID: `1lLSG-Ews7kPdcZxMsHSmq55l2DklrtgS`
- Reusable Rules v1.7 Drive ID: `1Cs_YArXIB0kPgsZT0CETXTBi5atkr5ib`

Completed since v0.8.5:
- Map 81: 35/35 human reviewed.
- Map 82–85: 65/65 human reviewed.
- 164 runtime DAT values changed vs v0.8.5.
- `頁:1` format corruption: 38 -> 0.
- `(法語)` contamination: 7 -> 0.
- Opaque A-Z label corruption exposed by new contract: 16 -> 0.
- v1.7 source-aware contracts added for Silph Scope, Rocket Grunt(s), Super Secret Key and Hall of Fame.
- Remaining `full_mt_argos_s2twp`: 9,186.

Current QA:
- 21,438 manifest rows
- 21,437 non-empty zh_tw
- v1.7 lint: HARD=0, WARN=0
- manifest -> DAT mismatches=0
- Marshal structure issues=0
- ZIP integrity=PASS

Current exact next start:
1. Resume at Map 86 EVENT_TEXT review.
2. Discover exact-English repeats before per-map edits.
3. Run v1.7 full-manifest QA after every batch.
4. Merge new device feedback before next public candidate.
5. Refresh HANDOVER at every checkpoint.
