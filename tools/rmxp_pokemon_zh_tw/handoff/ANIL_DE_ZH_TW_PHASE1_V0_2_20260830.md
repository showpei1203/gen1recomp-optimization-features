# Pokémon Anil DE 1.0.23 ZH-TW Phase 1 v0.2

Primary target: AYN THOR + JoiPlay.

Baseline:
- Pokémon Anil DE 1.0.23 ENGLISH
- Pokémon Essentials v21.1
- P0 50-line candidate already passed real-device zh-TW rendering/boot validation on AYN THOR + JoiPlay (2026-08-30).

Current candidate:
- `ANIL_DE_1.0.23_ZH_TW_PHASE1_UI_SYSTEM_v0.2_20260830.zip`
- Drive authority: `RMXP_POKEMON_ZH_TW_TOOLCHAIN/candidates`
- 21,438 total manifest entries
- 873 translated entries in this build
- 823 new Phase 1 UI/system entries + 50 existing P0 entries

New Phase 1 breakdown:
- SCRIPT_TEXTS: 563
- MAP_NAMES: 109
- REGION_LOCATION_NAMES: 66
- TRAINER_TYPE_NAMES: 61
- TYPE_NAMES: 19
- EVENT_TEXTS: 3
- REGION_NAMES: 2

QA:
- DAT rows applied: 873
- Missing DAT keys: 0
- Placeholder/token mismatches: 0
- Baseline Marshal leaves: 21,425
- Target Marshal leaves: 21,425
- Added leaves: 0
- Removed leaves: 0
- Value differences vs English baseline: 869 (four entries intentionally text-identical: HP, HP, PP, ???)

Scope of v0.2:
- Main menu/system UI
- Battle commands and common battle UI
- Bag/Pokédex/storage/options UI
- Types, stats, natures, statuses, weather/terrain/system labels
- Dates/months/seasons
- Kanto locations/routes where DAT-backed
- Common trainer classes

Not yet full translation:
- Full story/NPC dialogue
- Full official zh-Hant species/move/ability/item database
- Image-based English UI
- Plugin/hardcoded residual English

Next gate: AYN THOR + JoiPlay real-device validation of v0.2. Do not promote to full translation until this candidate passes boot, menu, battle, Bag, Pokédex, save/load, and rendering checks.
