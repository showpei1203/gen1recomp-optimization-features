# Pokémon Anil DE 1.0.23 English — RMXP zh-TW ingest

Date: 2026-08-30
Target: `Pokemon Anil DE 1.0.23 ENGLISH.zip`
Drive location: `Gen1recomp / RMXP_POKEMON_ZH_TW_TOOLCHAIN / source_games`
Observed Drive size: 600,246,034 bytes.

## Status
- Source ZIP confirmed in Drive.
- Public release information identifies the Definitive Edition as Pokémon Essentials v21 generation.
- The connected Drive raw-file download path has a 256 MiB single-file ceiling, so the 600 MB authority ZIP cannot be ingested directly through that connector.

## Workaround added to toolchain
- `07_PREP_LOCALIZATION_SOURCE.bat`
- `toolchain/prep_localization_source.ps1`

The helper reads the original ZIP without modifying it and creates a compact `_LOCALIZATION_SOURCE.zip` containing translation-relevant material such as Data, PBS, Plugins, Fonts, Text_* and root configuration/text files.

## Acceptance sequence
1. Produce `Pokemon Anil DE 1.0.23 ENGLISH_LOCALIZATION_SOURCE.zip` from the authority ZIP.
2. Upload that compact pack beside the original in Drive.
3. Run structure/version detection.
4. Inventory English/Spanish/localization sources and hard-coded plugin strings.
5. Perform 20-50 line zh-TW round-trip.
6. Verify placeholders, fonts, compile path and runtime display.
7. Only after the pilot passes, expand to full-game translation.

The original 600 MB ZIP remains the immutable authority copy.
