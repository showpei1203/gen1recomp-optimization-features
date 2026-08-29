# SoulGoldRecomp Traditional Chinese Authority v0.1

Date: 2026-08-29
Status: DESIGN AUTHORITY / RELEASE REQUIREMENT
Locale: `zh-Hant-TW`

## Goal

Ship SoulGoldRecomp with a complete Traditional Chinese player-facing experience without making the original 32 MiB ROM the storage boundary for the translation corpus or CJK glyph assets.

## Architecture principle

`SoulGold game logic -> stable text/render hook -> localization resolver -> external zh-Hant catalog + external glyph assets -> renderer`

The original English/source text remains a deterministic fallback.

## Why an external localization layer is required

The pinned S0 SoulGold build nearly fills a 32 MiB ROM. A full Traditional Chinese font plus duplicated translated dialogue would consume substantial cartridge space and reintroduce the exact hardware ceiling SoulGoldRecomp is intended to escape. Recomp therefore owns the localization expansion layer.

## Planned phases

### T0 — Text engine discovery
After S0-C boot is proven:
- enumerate SoulGold/pokeemerald-expansion text-printer entry points from the exact ELF symbols;
- identify dialogue, menu, battle-message, naming, and special glyph paths;
- determine stable native function-entry hooks suitable for translation/render interception;
- collect text layout constraints and variable/control-code behavior.

PASS requires a small runtime proof that can substitute one known string externally without changing the ROM.

### T1 — External catalog
Create an external UTF-8 `zh-Hant-TW` catalog keyed by stable semantic/context IDs rather than raw pointer addresses alone.

Each entry should preserve:
- source string/context;
- Traditional Chinese translation;
- control codes/placeholders;
- speaker/event/menu context where relevant;
- terminology/glossary references;
- QA status.

Missing key behavior: source/English fallback + diagnostic, never blank/crash.

### T2 — Traditional Chinese glyph/render path
Provide external CJK glyph assets and a renderer compatible with SoulGold text boxes and menus. Do not rely on embedding a full CJK font into the ROM.

Requirements:
- Traditional Chinese glyph coverage for the shipped catalog;
- Pokémon symbols/control codes remain compatible;
- pixel-appropriate presentation at native GBA resolution;
- deterministic line breaking and width metrics;
- no dependency on distributing raw font files in project handoffs; generated/rasterized game assets are preferred where licensing permits.

### T3 — Terminology authority
Priority:
1. Taiwan official Pokémon Traditional Chinese terminology when available.
2. Existing official localized place/character terminology when applicable.
3. SoulGold-specific terms use a project glossary with one canonical translation.

Glossary categories:
- species;
- moves;
- abilities;
- items;
- types/statuses/stats;
- locations;
- trainers/classes;
- UI/system vocabulary;
- SoulGold-specific mechanics/content.

### T4 — Full extraction/translation/QA
Coverage gates:
- main story/event dialogue;
- optional NPC dialogue;
- battle messages;
- menus/system prompts;
- Pokédex/species content present in SoulGold;
- item/move/ability descriptions;
- trainer names/classes;
- naming/input screens;
- relevant built-in SoulGoldRecomp UI and mod-facing UI.

QA gates:
- no unresolved required keys;
- no placeholder/control-code corruption;
- no text-box overflow in tested contexts;
- official glossary consistency;
- English fallback still works;
- save compatibility unaffected by display language.

## Release policy

Traditional Chinese support is mandatory for the finished release. It may be implemented progressively after native boot, but a build is not considered final while the zh-Hant release gate is incomplete.
