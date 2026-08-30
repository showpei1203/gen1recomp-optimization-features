# Pokémon Anil zh-TW v0.5 Translation Fix handoff

Status: TRANSLATION FIX CANDIDATE / THOR TEST REQUIRED
Date: 2026-08-30
Baseline: v0.4 FULL BETA

## Deliverable
- `ANIL_DE_1.0.23_ZH_TW_FULL_BETA_v0.5_TRANSLATION_FIX_20260830.zip`
- SHA256: `1f4c45502dcff7368dcdc464d2d849584cffd7d31931af1d4dac12eace4b4b03`
- Drive file ID: `1eyPzuJvwnTwyf0JrHeAnkUyLLGpr2XSX`
- Drive folder: candidates `1kPLTpmI_0-zemGQmiOXaZVmNM8d-WnYx`

## Translation re-audit
- Manifest entries: 21,438
- zh_tw non-empty: 21,437 (the single empty row has an empty source)
- DAT values changed versus v0.4: 1,360
- Repaired screenshot-visible Spanish save prompt, mixed English/Chinese pocket message, Options labels/descriptions, Pallet Town and speaker/UI strings.
- Re-audited hardcoded `Translation_Patches` UI and added Summary/Egg/Trainer Notes translations.
- Cleared known `中文(簡體)` / corruption-marker patterns from the zh_tw manifest.

## Format safety
The old QA missed formatted brace tokens such as `{1:03d}` and `{1:.1f}`. v0.5 adds a stronger token audit covering Essentials controls, Ruby interpolation, formatted braces and HTML/RGSS tags.
- Additional formatted-token repairs: 23
- Robust token mismatch: 0
- DAT structural issues vs v0.4: 0
- `Translation_Patches` Ruby syntax: PASS
- `ANIL_ZH_TW_V05_OVERRIDES` Ruby syntax: PASS

## White fog issue
Not changed by v0.5. Exact Thor/JoiPlay reproduction clue from user testing:
- skipping player-name entry avoids the white/fog overlay;
- entering a player name reliably triggers it;
- the fog temporarily disappears while the save screen is open.

Next visual pass should inspect the player-name entry return path, fade/tone state, viewport/picture disposal and any screen overlay state. Keep this separate from v0.5 translation validation.
