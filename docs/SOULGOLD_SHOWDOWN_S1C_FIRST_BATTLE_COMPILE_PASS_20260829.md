# SoulGold Showdown S1C First-Battle Compile PASS — 2026-08-29

## Status

**COMPILE / LINK / CI PASS. HUMAN RUNTIME PENDING.**

S1C replaces the temporary S1B overworld B-button harness with SoulGold's normal new-game starter and first-battle path.

## Source authority

- Authority branch: `feature/showdown-animated-battlers`
- Framework build commit: `45cd3969963cb9d72935bdeb682f68a9170021c1`
- Pinned SoulGold baseline: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- Official Showdown source: `https://www.pokemonshowdown.com/files/resources/sprites.zip`
- GitHub Actions run: `33223841442`

## S1C normal-flow contract

1. New Game and opening events remain native SoulGold flow.
2. `src/overworld.c` is **not modified**.
3. The temporary `B_BUTTON` / `ShowdownSoulGoldPrototype_TryStartTestBattle` harness is removed from the prototype API and runtime.
4. In the normal starter chooser, the left starter slot is changed from Treecko to `SPECIES_SPRIGATITO`.
5. `CB2_GiveStarter` retains the native first-battle path, but immediately before that path it replaces the enemy party with one Lv5 `SPECIES_MARILL`.
6. Showdown runtime binds only:
   - player-side Sprigatito -> Showdown `ani-back/sprigatito.gif`
   - opponent-side Marill -> Showdown `ani/marill.gif`
7. S1C still takes battler body ownership only during move selection. Native SoulGold remains authoritative for send-out, move execution, hit reactions, fainting, switching and battle effects.
8. PMD runtime dependency remains `NONE`.

## CI result

Workflow: `SoulGold Showdown S1C First-Battle Build Gate`

PASS gates:

- deterministic S0 ingest regression
- official Showdown source download
- Sprigatito-back asset preparation
- Marill-front asset preparation
- S1C installer
- Sprigatito starter marker
- Marill first-battle marker
- no B-test symbol in Showdown prototype
- zero diff to `src/overworld.c`
- no PMD runtime symbols
- full SoulGold compile/link
- warning/error audit for Showdown, starter chooser and battle setup patches
- ROM artifact upload

## ROM evidence

- ROM size: `33554432` bytes
- SHA-256: `774f6e3abf2faa2b5f7eea737625a53f72850e3a0d2fae9ff02099f24921fcd7`
- CRC32: `2DC74B5B`
- GitHub artifact: `SoulGold-Showdown-S1C-Sprigatito-Marill-First-Battle-ROM`
- Artifact ID: `9706210887`

## Required human runtime gate

Start a fresh New Game on AYN THOR / RetroArch mGBA and verify:

- opening events do not freeze
- starter chooser opens normally
- left starter is Sprigatito and can be selected
- first battle is against Lv5 Marill
- Sprigatito back Showdown idle animates during move selection
- Marill front Showdown idle animates during move selection
- no palette corruption, square mask, frame jitter, disappearance, black screen or crash
- selecting a move returns ownership to native SoulGold correctly
- returning to move selection resumes Showdown idle correctly

Do not promote S1C to formal baseline until this human runtime gate passes.
