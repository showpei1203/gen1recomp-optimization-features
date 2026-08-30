# MASTER_PROJECT_STATE

Project: RMXP Pokémon Traditional Chinese Localization Toolchain
Version: v0.1.0
Date: 2026-08-30
Status: INITIAL BASELINE / SOURCE READY

## Formal strategy
**Essentials-first.** The primary target is Pokémon fangames made with Pokémon Essentials, especially v17-v21+.

Authority:
- Google Drive: complete ZIP, handoff, test evidence, future game-specific extracted text/builds.
- GitHub: source code, tools, docs, glossary source, diffs.

Current capability:
- Essentials extracted text -> TSV -> glossary seed -> QA -> translated text rebuild.
- Project English candidate scan.
- Scripts.rxdata source dump helper.

Fallback policy:
- Do not directly rewrite MapXXX.rxdata by default.
- Only add binary/custom adapters after a real target proves the standard Essentials pipeline is insufficient.

Not yet claimed:
- No real-game acceptance test yet.
- No generic MapXXX.rxdata binary rewrite.
- Glossary is a seed, not a full official corpus.
