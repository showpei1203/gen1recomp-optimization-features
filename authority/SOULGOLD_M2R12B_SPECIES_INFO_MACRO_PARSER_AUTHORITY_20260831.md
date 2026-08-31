# SOULGOLD M2R12B SPECIES_INFO MACRO PARSER AUTHORITY (2026-08-31)

## Root cause
M2R12A correctly followed SoulGold split local includes, but still assumed every SpeciesInfo record was a normal initializer block. Unown is defined as `[SPECIES_UNOWN] = UNOWN_MISC_INFO(...)`, with its constant height/weight inside the macro definition. Therefore direct block parsing found 250/251 heights and missed only species 201.

## Fix
- Collect local multiline `#define NAME(...)` macro bodies that contain constant `.height` / `.weight`.
- Resolve one-line `[SPECIES_X] = MACRO(...)` SpeciesInfo assignments through those macro defaults.
- Preserve normal block parsing and recursive quoted-include parsing.

## Regression R-SD-048
`SPECIES_INFO_PARSER_MUST_RESOLVE_CONSTANT_HEIGHT_FROM_MACRO_INITIALIZERS`

The validator fixture now mirrors both real SoulGold structures simultaneously: split generation includes plus an Unown-style macro SpeciesInfo initializer. 251/251 is required.

## Next gate
After 251/251 size-class generation and 502 provider cache migration pass on the runtime machine, leave provider/scale tuning and move to switch lifecycle + action presentation.