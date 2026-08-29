# SoulGoldRecomp Project Rules v1

Date: 2026-08-29
Status: AUTHORITY
Branch: `feature/soulgold-recomp-s0`

## Project goal

Build a SoulGold-native GBARecomp application/runtime that preserves the SoulGold game while removing the original 32 MiB cartridge as the content ceiling. Large presentation assets and future enhancements must be able to live outside the ROM and be delivered through the recomp/mod asset system.

## Non-negotiable delivery rules

### R1 — Every stage must ship a handoff
Every meaningful development/test stage must produce a user-downloadable handoff artifact. A chat reply, GitHub commit, issue update, or Drive note by itself is not a handoff.

Each handoff must include, at minimum:
- current phase and PASS/FAIL/PREPARED state;
- exact upstream/project pins where applicable;
- what changed since the previous handoff;
- files/scripts the user should run next;
- expected PASS indicators;
- known blockers/risks;
- rollback/reuse instructions;
- next gate.

ROM bytes, copyrighted source-game assets, BIOS bytes, and ROM-derived generated bodies must not be redistributed inside a public handoff unless the user supplied them and redistribution is appropriate. Prefer scripts and evidence.

### R2 — Traditional Chinese is a release requirement
The finished SoulGoldRecomp experience must ship with Traditional Chinese (`zh-Hant-TW`) support. This is a release gate, not a post-release nice-to-have.

Default target policy:
- Traditional Chinese is the primary finished user-facing language.
- English remains available as fallback/reference.
- Canon Pokémon terminology should use Taiwan official Traditional Chinese names where an official term exists.
- SoulGold-specific/fan-authored terms use a reviewed project glossary.
- Translation must cover gameplay text, menus, battle messages, item/move/ability/species terminology, trainer/event dialogue, system prompts, and mod-facing user UI that belongs to SoulGoldRecomp.

### R3 — Do not solve localization by consuming the remaining ROM budget
SoulGold's pinned S0 build already occupies almost the entire 32 MiB image. Traditional Chinese therefore must be designed around the recomp/external-asset architecture rather than depending on stuffing a large CJK font and duplicated text corpus into the cartridge image.

### R4 — Preserve fallback paths
Enhancements should fail safely:
- external asset missing -> original SoulGold asset;
- translation key missing -> English/source fallback plus diagnostic;
- mod disabled -> faithful SoulGold behavior;
- unresolved executable path -> interpreter/self-heal path where supported, until promoted to reviewed static coverage.

## Phase gates

- S0-A: source/symbol/runner preparation — FORMAL PASS on 2026-08-29.
- S0-B: build `gba_recompile`, emit SoulGold native shards, link minimal SoulGoldRecomp runner.
- S0-C: first runtime boot/title-screen validation.
- S1: external asset proof — replace one SoulGold asset from outside ROM with original fallback.
- T0: Traditional Chinese text-engine discovery and stable hook selection.
- T1+: external zh-Hant catalog/font/rendering integration and progressive translation QA.

No later phase may silently invalidate a sealed earlier phase.
