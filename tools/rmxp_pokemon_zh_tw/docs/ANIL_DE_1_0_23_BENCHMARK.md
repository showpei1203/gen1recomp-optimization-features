# Anil DE 1.0.23 benchmark

First real target: `Pokemon Anil DE 1.0.23 ENGLISH.zip`.

Observed:
- Original ZIP: 600,246,034 bytes
- Localization source pack: 9,986,598 bytes
- Original SHA256: `759bf293d9adc45c85f1dd7c5756f097570d8ad464204f313b9b8575e0517fb3`
- Pokémon Essentials: v21.1
- Game version: 1.0.23
- Core scripts: 451
- Plugin packages: 51
- Union message entries: 21,438
- English DB entries changed from default: 19,034
- Spanish-diacritic heuristic hits in English target: 2,804 (~13.1%)
- Translation-only keys: 2

P0 result:
- 50 zh-TW values built into an English-baseline DAT.
- Placeholder QA: 0 issues.
- Target Marshal leaf count unchanged.
- Exact value diff vs English baseline: 50.
- Patched Settings/MessageConfig syntax: PASS.

Remaining gate: real game rendering, especially availability of a CJK system font on Windows/Android/mkxp-z.
