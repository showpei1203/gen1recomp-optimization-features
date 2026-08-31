# Pokémon Anil DE 1.0.23 zh-TW v0.7.3 Internal Story Polish Checkpoint

Status: INTERNAL CHECKPOINT / MERGE WITH v0.7 FIELD TEST BEFORE NEXT PUBLIC CANDIDATE
Date: 2026-08-31
Baseline: v0.7 QUALITY_CJK_WRAP

## Progress since v0.7
- Maps 11-27: 164 raw Argos MT EVENT_TEXT rows manually polished.
- Maps 28-32: 88 raw Argos MT EVENT_TEXT rows manually polished.
- Maps 33-40: 95 raw Argos MT EVENT_TEXT rows manually polished.
- Total new manual polish statuses: 347.
- Serialized DAT value differences vs v0.7: 346.
- Maps 11-40 remaining non-ellipsis raw `full_mt_argos_s2twp` EVENT_TEXT rows: 0.
- Overall raw Argos status rows reduced from 10,345 to 9,998.

## Areas covered
- Mt. Moon through Lavender Town main route dialogue.
- Pallet/Viridian interiors and Oak Laboratory.
- Trainer School.
- Pewter interiors and Museum.
- Celadon Game Corner related dialogue.
- Team Rocket, Samson Oak, Lorelei, Wattson and Pokémon terminology normalized to Taiwan zh-TW usage where applicable.

## QA
- placeholder QA: 0 issues
- robust Ruby/HTML/control-token QA: 0 issues
- DAT structure issues: 0
- CJK wrap Scripts unchanged from v0.7
- MapInfos unchanged from v0.7
- v0.6.x UI/resource/suffix fixes retained through v0.7 baseline

## Artifact
- ZIP: `ANIL_DE_1.0.23_ZH_TW_v0.7.3_INTERNAL_STORY_POLISH_M11_40_20260831.zip`
- SHA256: `543c44de6706419035fa34fd3bcdcebfc586f6eb80369f120dd5ac6adb902073`
- Google Drive ID: `1PMMcX7exCdZAki2cHd-sVxwsWcbbp2QW`

## Release policy
Do not ask the tester to replace v0.7 solely for this translation checkpoint. Merge v0.7 Thor/JoiPlay runtime feedback into the next public candidate, then continue story polish from Map 41 onward.
