# Pokémon Anil DE 1.0.23 zh-TW v0.7 Quality + CJK Wrap Handoff

Status: TEST CANDIDATE / QUALITY FOUNDATION
Date: 2026-08-31
Baseline: v0.6.2 SUMMARY_SUFFIX_ROOT_FIX
Artifact: `ANIL_DE_1.0.23_ZH_TW_v0.7_QUALITY_CJK_WRAP_20260831.zip`
SHA256: `0e2d2e18e81d20af94b2f4b85812f648574ec3cd8db1b94b5983de0aae34b934`
Drive ID: `1ziWsJmjyY6LnC8tj9hDSU3df0deJimtV`

## Scope
- Retains v0.6.2 battle HUD, Move UI, Summary UI, resource-path and `memo` suffix repairs.
- Localizes all 219 `MapInfos.rxdata` entries.
- Adds CJK-aware message wrapping in `DrawText` only.
- Polishes early-game/high-exposure dialogue and battle/system terminology.
- Removes known MT pollution such as wild Pokémon rendered as beasts, Korean/English marker artifacts, gym terminology corruption, bad Kanto place-name transliterations, `B&W software`, and `Indigo core software`.

## Static QA
- manifest entries: 21,438
- zh_tw non-empty: 21,437 (the single empty row has empty source)
- manifest values changed vs v0.6.2: 3,086
- DAT value differences vs v0.6.2: 3,087
- early Map 1-10 EVENT_TEXTS: 344 total / 293 changed
- manual-or-polish status rows: 844
- raw `full_mt_argos_s2twp` status rows: 10,345
- MapInfos: 219 total / 219 changed / unresolved Latin 0
- placeholder QA issues: 0
- robust token / Ruby / HTML issues: 0
- DAT structural issues: 0
- Scripts: 451 -> 451; only index 92 `DrawText` changed
- CJK wrap simulation: PASS (`FAST_NEWLINES=12`, `FMT_NEWLINES=12`)

## Runtime acceptance focus
1. Long Traditional Chinese dialogue wraps without clipping.
2. Wild encounter wording is natural, e.g. `野生的波波` rather than `野獸波波`.
3. Map title overlays use zh-TW names such as 真新鎮 / 常磐市 / 深灰市.
4. Battle HUD, Move selection UI, and Summary UI remain intact.
5. Early Oak/rival/NPC dialogue quality is materially improved.

## Known limitation
v0.7 is not a fully hand-polished whole-game script. About 10k rows still carry original Argos MT status and should be reviewed region-by-region during playthrough.
