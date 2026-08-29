# SoulGold Showdown S1B B-Test Compile PASS — 2026-08-29

## Status

- Branch: `feature/showdown-animated-battlers`
- SoulGold baseline: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- Framework build head: `4c433f6adad3d01b33e1c8df806af8a6ce6cb5a6`
- GitHub Actions run: `33222541401`
- Full SoulGold compile/link: **PASS**
- Showdown-source warning/error audit: **PASS**
- Human runtime / visual validation: **PENDING**

## Deterministic test harness

Temporary S1B-only overworld hook:

- fresh **B** press in a safe overworld state starts the test battle;
- player party slot 1 must already be **Sprigatito**;
- player party is not rewritten to construct the test;
- enemy party is populated in memory with one **Marill** at the same level as the lead;
- battle starts through `DoStandardWildBattle_Debug()`;
- controls are rejected while field controls are locked or script context is active;
- explicit marker: `SHOWDOWN_S1B_TEMP_TEST_HARNESS`;
- formal release requirement: **REMOVE_B_BUTTON_HARNESS**.

Normal battle consequences such as HP/status/EXP changes remain possible because the launched battle is otherwise real gameplay. Human test should use a save-state/backup and reload afterward, or run away without saving test-side changes.

## Animated battler targets

### Player — Sprigatito back

- source: Pokémon Showdown `ani-back/sprigatito.gif`
- source canvas: 45×53
- GBA canvas: 64×64
- scale: 1.0, no scaling
- frames: 51
- loop: 102 × 60 Hz ticks ≈ 1.70 s
- SoulGold host palette source entries: 13
- visible host colors used: 12
- storage policy: short host palette padded to 16 entries for GBA palette storage

### Opponent — Marill front

- source: Pokémon Showdown `ani/marill.gif`
- source canvas: 51×48
- GBA canvas: 64×64
- scale: 1.0, no scaling
- frames: 54
- loop: 108 × 60 Hz ticks ≈ 1.80 s
- SoulGold host palette source entries: 16
- visible host colors used: 15

## Ownership scope

S1B remains deliberately conservative:

- Showdown runtime owns battler pixels during move selection only;
- native SoulGold remains authoritative for send-out, move execution, hit reactions, HP changes, fainting, switching, and battle lifecycle;
- PMD runtime dependency: **NONE**.

## Palette regression fix

S1B exposed a valid SoulGold asset case where `graphics/pokemon/sprigatito/normal.pal` contains 13 JASC entries rather than exactly 16. The ingest tool was generalized to accept host palettes with 2–16 declared entries, use only the declared visible entries for nearest-color matching, and pad missing slots with black only for 16-entry GBA storage. A deterministic 13-entry regression test now covers this behavior.

## ROM evidence

- size: 33,554,432 bytes
- SHA-256: `7dc7515d667c1a5fdd04d413a80ac8d552860427d56afe52ac8a04e17d25c4e5`
- CRC32: `0C2187E3`
- Actions artifact: `SoulGold-Showdown-S1B-Sprigatito-Marill-B-Test-ROM`
- artifact id: `9705778013`

## Human validation checklist

1. Load the existing save with Sprigatito in party slot 1.
2. Stand in normal overworld control and tap B once.
3. Confirm immediate battle against same-level Marill.
4. Confirm native send-out still works.
5. At move selection, verify Sprigatito back and Marill front both animate continuously.
6. Check palette, transparency, clipping, jitter, and positional drift.
7. Select a move and confirm native move/hit ownership resumes correctly.
8. Confirm Showdown idle resumes when move selection returns.
9. Check HP/faint/switch flow and absence of black screen, disappearance, freeze, or crash.

No promotion beyond S1B compile PASS until AYN THOR / RetroArch mGBA human runtime evidence is recorded.
