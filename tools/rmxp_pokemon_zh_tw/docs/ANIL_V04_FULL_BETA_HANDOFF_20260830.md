# Pokémon Anil DE 1.0.23 zh-TW FULL BETA v0.4

## Artifact
- File: `ANIL_DE_1.0.23_ZH_TW_FULL_BETA_v0.4_20260830.zip`
- SHA256: `62cc29c5f3cd37966e44ff98de1c4e702d6e219336ab147881165ba3ee4c8595`
- Drive file ID: `1QZxMwKUFKf3rFmx7tt8MHwvQ-wzzP--d`

## Coverage
- Manifest rows: 21,438
- Non-empty `zh_tw`: 21,437
- The only empty row has an empty source value.
- v0.3 curated / official-name overlays preserved: 5,222
- Official zh-Hant exact-text overlays: 141
- Taiwan terminology cleanup rows: 1,091
- Battle `Run` command normalized to `逃走`.

## Format repair
The first full MT candidate exposed a wider class of markup corruption that the original placeholder QA did not detect. A second protected-token pass identified and retranslated 842 candidates while shielding Essentials controls, Ruby interpolation, HTML-like tags and control bytes.

Repair workflow:
- `.github/workflows/repair-anil-full-zh-tw-v04.yml`
- Commit: `d6e7576fd9c25052e4fb0b215adcd4b747fffe85`
- Workflow run: `33309026262`
- Repair artifact: `anil-full-zh-tw-token-repaired-v04`
- Repair candidates: 842
- Robust token issues after repair: 0
- Unexpected ASS subtitle/font markup after repair: 0

## QA
- Essentials placeholder QA: 0 issues
- Robust protected-token / Ruby interpolation / HTML-tag QA: 0 issues
- `messages_zh_tw_game.dat` successfully rebuilt with 21,437 populated values
- No removed keys and no array/type structure changes against the English DAT.
- 12 additional `SCRIPT_TEXTS` hash keys are intentionally retained. They exist in the source/default message union but not in `messages_english_game.dat`; including them prevents fallback to untranslated default/Spanish strings.

## Runtime files
- `Data/Scripts.rxdata`
- `Data/messages_zh_tw_game.dat`

## Acceptance target
Primary: JoiPlay / Android. Secondary: Windows.

Test boot and language selection, early story/NPC dialogue, menu, Pokédex, move/ability/item descriptions, battle commands, Bag/shop, save/load, and physical controls.

## Quality status
This is a **FULL COVERAGE BETA**, not a claim that every project-specific sentence has been human-edited. The remaining work is gameplay-driven language-quality revision, hardcoded/plugin/image-text residual discovery, overflow checks, and terminology polishing based on runtime screenshots.
