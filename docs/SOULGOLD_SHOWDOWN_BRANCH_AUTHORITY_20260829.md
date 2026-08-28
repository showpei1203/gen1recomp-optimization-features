# SoulGold Showdown Animated Battlers Branch Authority

Date: 2026-08-29
Status: ACTIVE EXPERIMENTAL LANE
Branch: `feature/showdown-animated-battlers`
Repository: `showpei1203/gen1recomp-optimization-features`

## Purpose

Create a parallel SoulGold GBA battle-sprite route using the prepackaged Pokémon Showdown `sprites.zip` animated battlers instead of PMD SpriteCollab action sheets.

This lane exists to answer one narrow question first:

> Can Pokémon Showdown idle GIF animations be converted into GBA-safe battler assets and run as stable front/back battle idle loops in Pokémon SoulGold on mGBA / RetroArch / AYN THOR?

Do not merge this lane into the PMD route until runtime evidence justifies it.

## Source authority

Official package index:
- `https://play.pokemonshowdown.com/sprites/`
- prepackaged archive: `https://www.pokemonshowdown.com/files/resources/sprites.zip`

Primary folders:
- `ani/` = animated front
- `ani-back/` = animated back
- `ani-shiny/` = animated shiny front
- `ani-back-shiny/` = animated shiny back

PokeAPI independently mirrors Showdown community GIFs under its sprite repository and identifies them as Smogon-community sprites.

## SoulGold source baseline

The target source baseline remains:

`b5122bdf188943862c13abe4938e88b7bb3c5c4a`

Important: that SHA belongs to the external SoulGold source lineage and is not a commit in this authority repository. The Showdown branch therefore forks the authority/tooling history while its installer must target a clean checkout of the SoulGold baseline above.

## Separation rule

The Showdown lane MUST NOT require PMD runtime patches to be pre-installed.

Reusable generic lessons are allowed, including:
- battler creation ownership points
- OBJ/VRAM timing knowledge
- 64x64 4bpp GBA constraints
- build/test harness patterns

PMD-specific runtime symbols, action registries, shadow ownership, attack/hurt/sleep bindings, and SpriteCollab metadata are not dependencies of the Showdown lane.

## S0: ingestion contract

S0 owns only source-to-asset conversion.

Input:
- official `sprites.zip`, or
- an extracted source directory containing Showdown animation folders

Output per species/lane:
- 64x64 indexed PNG preview frames
- 2048-byte raw GBA 4bpp frame tiles
- 32-byte 16-entry GBA BGR555 palette
- `manifest.json` preserving GIF frame durations as 60 Hz ticks

Normalization rules:
1. one stable logical canvas for the whole GIF
2. no per-frame bbox recentering, because that creates animation jitter
3. no upscaling
4. oversized sources are nearest-neighbor fitted inside 64x64
5. bottom-center anchoring
6. one shared palette per animation
7. palette index 0 is transparent; visible colors use indices 1..15
8. no dithering

## S0 seed roster

Runtime promotion should begin with a deliberately small coverage set:
- Cyndaquil: starter-sized, direct continuity with the PMD prototype
- Pikachu: compact familiar silhouette
- Charizard: larger winged silhouette
- Onix: extreme long-body stress case

S0 tooling must support arbitrary Showdown file stems, including form names, even though the first runtime ROM should remain small.

## Promotion gates

### S0 PASS
- deterministic synthetic self-test passes
- front and back GIFs ingest without frame-size drift
- each frame emits exactly 2048 bytes of 4bpp tile data
- each palette emits exactly 32 bytes
- timing survives as non-zero 60 Hz ticks

### S1 PASS
- one species front/back compiles into a clean SoulGold baseline
- ROM boots
- no native battler leak before animated asset ownership

### S2 HUMAN RUNTIME PASS
On AYN THOR / RetroArch mGBA:
- player back sprite animates continuously
- enemy front sprite animates continuously
- no frame jitter
- no palette corruption
- no square mask/background artifact
- normal battle flow remains functional

Only after S2 should roster expansion begin.

## Non-goals for this branch right now

- full 1000+ Pokémon import
- attack/hurt/sleep actor animations
- rewriting move FX
- replacing PMD formal authority
- mixing Showdown and PMD assets in the same runtime prototype

The advantage of this lane is simplicity. Keep it simple long enough to measure it.
