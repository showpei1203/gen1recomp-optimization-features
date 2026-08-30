# Pokémon Anil zh-TW v0.6 UI Integrity Fix Handoff

Status: **TEST CANDIDATE**. Pending AYN THOR + JoiPlay runtime validation.

Baseline: Pokémon Anil DE 1.0.23 English / Pokémon Essentials v21.1.

## Artifact

- ZIP: `ANIL_DE_1.0.23_ZH_TW_FULL_BETA_v0.6_UI_INTEGRITY_FIX_20260831.zip`
- Size: `3,783,594 bytes`
- SHA256: `711b0fb9f022d22b58dcd72adfe5a9d85048f279112e91f49dc3b0512fccab02`
- Google Drive file ID: `1STECay3ROCJp08o2qfHPuIzo3m10RkzM`
- Google Drive parent: candidates folder `1kPLTpmI_0-zemGQmiOXaZVmNM8d-WnYx`

## Confirmed v0.5 root cause

The v0.5 full MT layer translated some `SCRIPT_TEXTS` values that are not prose. They are runtime asset paths passed through `_INTL`.

Examples of broken v0.5 values included:

- `Graphics/Translations/English/cursor_command` -> translated Chinese path text
- `Graphics/Translations/English/databox_normal` -> translated Chinese path text
- `Graphics/Translations/English/databox_normal_foe` -> translated Chinese path text
- `Graphics/Translations/English/types` -> translated Chinese path text
- `Graphics/Translations/English/overlay_hp_back` -> translated Chinese path text
- Naming, Party, Pokédex, Bag and other UI asset paths were affected too.

Once translated, the engine could not resolve those bitmap paths. This directly explains the missing battle HP databox/HUD backgrounds and is a strong explanation for the broken battle move-menu presentation and other missing UI graphics.

## v0.6 repairs

1. Restored all **60** runtime `Graphics/Audio/Data` message values to their exact English-runtime asset values.
2. Cross-audited all `_INTL("Graphics/..." / Audio / Data)` references in extracted Scripts and PluginScripts. Runtime resource mismatch after repair: **0**.
3. Removed the v0.5 `ANIL_ZH_TW_V05_OVERRIDES` script and its global `Bitmap#draw_text` monkeypatch.
4. Fixed two direct `Overworld` item-pickup strings so literal Essentials `\\n` and `\\c[]` controls survive Ruby parsing. This targets the visible control-code boxes reported during Berry/item pickup.
5. Repaired Ruby interpolation and protected tokens that MT had altered, including `#{pokemon.name}`, `#{pokemon.species}` and `$PokemonGlobal` expressions.
6. Targeted translation cleanup:
   - Professor Oak / Prof. Oak -> `大木博士` across 105 relevant rows checked
   - `PP: {1}/{2}` -> `PP：{1}/{2}`
   - `Exp. Share` -> `學習裝置`
   - Pallet Town -> `真新鎮`
   - Laboratory (Pallet lab map) -> `大木研究所`
   - removed known `(英語)`, `中文(簡體)`, `序言:` and mangled Oak-name debris

## Static QA

- Manifest entries: **21,438**
- `zh_tw` nonempty: **21,437** (the remaining source value is intentionally empty)
- v0.6 values different from v0.5: **1,085**
- Runtime resource paths repaired from v0.5: **60 / 60**
- Runtime resource path mismatches after repair: **0**
- Essentials placeholder QA issues: **0**
- Robust token / Ruby interpolation / markup QA issues: **0**
- DAT structure equals v0.5: **PASS**
- Scripts count: **451**, same as English source
- `Main` remains last: **PASS**
- Compared with English source, only these scripts differ as intended: `Settings`, `MessageConfig`, `Overworld`, `Translation_Patches`
- v0.5 global Bitmap override present: **false**
- Direct item-message safe control strings: **2**

## Runtime acceptance targets

1. Player and foe HP databox/HUD backgrounds are restored.
2. Battle move menu backgrounds/cursors and four-move layout are restored.
3. Pokémon Summary/Detail background and page UI are restored.
4. Item/Berry pickup no longer shows raw control-code boxes.
5. Professor Oak appears as `大木博士` in the reported early scenes.
6. PP and Exp. Share UI text are correct.
7. Retest the protagonist-name-entry path. v0.6 also restores Naming UI runtime assets (`overlay_controls`, `icon_mode`), so the white-fog bug may change, but it is **not yet claimed fixed without device validation**.

## Important localization rule added by this regression

Never machine-translate runtime file paths or internal UI resource identifiers merely because they appear in an Essentials message table. Runtime resources must be classified/protected before translation. QA must audit resource-path identity independently from placeholder QA.
