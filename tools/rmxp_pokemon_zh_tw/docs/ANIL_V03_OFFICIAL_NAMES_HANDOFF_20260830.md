# Pokémon Anil DE 1.0.23 zh-TW v0.3 handoff

Primary target: **AYN THOR + JoiPlay**.

## Baseline
- Pokémon Anil DE 1.0.23 ENGLISH
- Pokémon Essentials v21.1
- P0 50-line Traditional Chinese DAT + language/font bridge: real-device PASS on AYN THOR/JoiPlay (2026-08-30)
- v0.2 UI/System candidate: 873 populated zh-TW manifest entries

## v0.3 candidate
`ANIL_DE_1.0.23_ZH_TW_PHASE2_OFFICIAL_NAMES_v0.3_20260830.zip`

- Manifest entries: 21,438
- zh-TW populated entries: 5,222
- Newly added in v0.3: 4,349
- DAT applied keys: 5,222
- Missing DAT keys: 0
- Placeholder/token mismatches: 0
- Marshal leaf count: 21,425 -> 21,425
- Added/removed leaves: 0 / 0
- Exact value differences vs English baseline: 5,218

### New v0.3 coverage
- SPECIES_NAMES: 1,025
- SPECIES_CATEGORIES: 706
- MOVE_NAMES: 845
- ABILITY_NAMES: 305
- ITEM_NAMES: 743
- ITEM_NAME_PLURALS: 725

### Deliberately unresolved official/custom-name residuals
310 total:
- SPECIES_NAMES: 2 (`Royaleon`, `Cefireon`)
- SPECIES_CATEGORIES: 32
- MOVE_NAMES: 6
- ABILITY_NAMES: 17
- ITEM_NAMES: 122
- ITEM_NAME_PLURALS: 131

Do not guess custom/fan-made names just to reduce the residual count. Resolve them with game context or a project-specific glossary.

## Localization authority
A reproducible GitHub Actions workflow now builds the reusable zh-Hant corpus from `PokeAPI/pokeapi` CSV data:

`.github/workflows/build-pokeapi-zh-hant-corpus.yml`

PokeAPI language id `4` is `zh-hant` / `zh-TW`. The generated corpus includes species, move, ability, item names, and species genus/category data. Chinese plural item labels reuse the singular Chinese name.

## Next real-device gate
On AYN THOR + JoiPlay verify:
1. Traditional Chinese remains selectable.
2. Pokédex species names/categories render correctly.
3. Summary species/ability/move names render correctly.
4. Battle move names render correctly.
5. Bag/shop/item acquisition names render correctly.
6. No tofu boxes/mojibake/overflow that blocks use.
7. Save/load still works.

After PASS, move to descriptions and story/NPC translation batches, then Plugin/hardcoded/image residual scan.
