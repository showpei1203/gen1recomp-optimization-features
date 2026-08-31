# Pokémon Anil zh-TW v0.7.7 INTERNAL handoff

Date: 2026-08-31
Baseline: v0.7.5 INTERNAL
Status: CHECKPOINT / not required for user public testing

## Completed
- Maps 56–58: 124/124 EVENT_TEXTS human-reviewed, 114 values changed.
- Maps 59–61: 109/109 EVENT_TEXTS human-reviewed, 106 values changed.
- Total Maps 56–61 reviewed: 233/233.
- Reusable known-bad lint v1.2 rerun across all 21,438 manifest rows.
- New lint rules exposed 17 matching corruptions elsewhere in the full game; all 17 fixed in this checkpoint.
- DAT changed vs v0.7.5: 237 values.
- `full_mt_argos_s2twp` remaining: 9,775.
- known-bad HARD issues: 0.
- Marshal structure issues: 0.
- ZIP integrity: PASS.

## Key terminology fixed
- Ariana → 雅典娜
- Archer → 阿波羅
- Lugia → 洛奇亞
- Ninetales → 九尾
- Charmander → 小火龍
- Totodile → 小鋸鱷
- Starmie → 寶石海星
- Bellossom → 美麗花
- Rapidash → 烈焰馬
- Cyndaquil → 火球鼠
- Bulbasaur → 妙蛙種子

## Reusable failures converted to HARD regression rules
- `party pooper` → never `黨拉屎`
- `smarty-pants` → never `聰明的褲子`
- `Drats` → never transliterate as `德拉特斯`
- Pokémon proper-name transliteration blacklist expanded
- one new bad pattern triggers full-manifest scan, not single-entry repair

## Artifact
`ANIL_DE_1.0.23_ZH_TW_v0.7.7_INTERNAL_STORY_POLISH_M56_61_20260831.zip`
SHA256: `6e08c81b40dbfc79c989ef5455c6d9f0fa7bea78302a13a921de562f747e229b`
Drive ID: `1Eorab3q1tWvWzx-s4a9m1uVBVr9b9PKn`

## Next
Map 62 is the next high-priority human-polish batch. It contains Bill / Prof. Oak / Cerulean Cave / Mewtwo exposition and still has many visible MT failures, including Elite Four terminology and psychic-field prose.
