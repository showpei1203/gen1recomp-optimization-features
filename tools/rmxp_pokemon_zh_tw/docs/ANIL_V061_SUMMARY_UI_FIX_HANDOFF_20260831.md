# ANIL v0.6.1 Summary UI Fix Handoff — 2026-08-31

## Baseline
- Pokémon Anil DE 1.0.23 zh-TW v0.6 UI Integrity Fix
- v0.6 ZIP SHA256: `711b0fb9f022d22b58dcd72adfe5a9d85048f279112e91f49dc3b0512fccab02`

## Runtime evidence from AYN THOR + JoiPlay
After v0.6, battle HP HUD, move-selection UI, and most previously missing UI backgrounds were restored. One isolated regression remained: the Pokémon Summary **Trainer Memo** page (encounter location / level / date / nature) rendered over a black/missing page background.

## Root cause / exact lookup
Both the baseline Summary handler and the current English implementation resolve the Trainer Memo page with suffix `memo`:

`Graphics/UI/Summary/bg_#{suffix}` → `Graphics/UI/Summary/bg_memo`

The remaining page therefore depends on the dedicated asset:

`Graphics/UI/Summary/bg_memo.png`

This asset was not part of the v0.6 resource-path repair because the Summary background lookup is a direct runtime path, not an `_INTL(...)`/message-DAT path.

## Fixed upstream reference extraction
A dedicated GitHub Actions extraction was run against current English Pokémon Indigo / Anil v4.0.2 EN-6.

- Workflow: `.github/workflows/extract-anil-v402-summary-reference.yml`
- Workflow commit: `7c9297821085e8d2adc73885f02124467ad44be2`
- Run: `33339549507` — SUCCESS
- Artifact: `anil-v402-summary-reference`
- Artifact ID: `9740097825`

Recovered fixed asset:
- `Graphics/UI/Summary/bg_memo.png`
- dimensions: 512×384 RGBA
- SHA256: `baaa31a1602d49dc86941c74065a04a80ef11dfb96f6f84b6cf550d452313adc`

The current English v4.0.2 scripts still resolve the same `Graphics/UI/Summary/bg_memo` path, so no Summary code fork is needed.

## v0.6.1 change scope
Minimal targeted repair only:

1. Carry forward v0.6 `Data/Scripts.rxdata` unchanged.
2. Carry forward v0.6 `Data/messages_zh_tw_game.dat` unchanged.
3. Add/overwrite `Graphics/UI/Summary/bg_memo.png` using the fixed current-English asset.
4. Add v0.6.1 audit/readme/checksums.

No other Summary graphics were replaced. This avoids regressing battle HUD, move menu, or other UI areas already confirmed improved in v0.6.

## Artifact
- ZIP: `ANIL_DE_1.0.23_ZH_TW_FULL_BETA_v0.6.1_SUMMARY_UI_FIX_20260831.zip`
- ZIP SHA256: `76bf3698a357f29426ed3210afe503a2f8d36dd3ee18520eb7efe8f7a0905f21`
- ZIP size: `3862669` bytes
- Drive ID: `1TtoMXD02dgSIuCCfdojKCySBXP43k1y3`
- Drive parent (candidates): `1kPLTpmI_0-zemGQmiOXaZVmNM8d-WnYx`

## Static QA
- `bg_memo.png` path exactly matches runtime Summary lookup: PASS
- asset is valid PNG: PASS
- dimensions 512×384: PASS
- asset SHA256 recorded: PASS
- Scripts relative to v0.6: UNCHANGED
- message DAT relative to v0.6: UNCHANGED

## Runtime status
**CANDIDATE / PENDING THOR CONFIRMATION**

Primary test: open Pokémon Summary → Trainer Memo page and verify the blue information background and panels are restored. Then quickly re-check battle HP HUD and move-selection UI to confirm no regression.
