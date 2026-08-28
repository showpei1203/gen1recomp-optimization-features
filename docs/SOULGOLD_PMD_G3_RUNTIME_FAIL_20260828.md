# SoulGold PMD G3 Runtime Failure — 2026-08-28

Status: **G3 COMPILE PASS / USER RUNTIME FAIL / G3R1 REPAIR ACTIVE**

## User runtime evidence

The delivered G3 ROM was reported to still:

1. show the legacy SoulGold Cyndaquil battle body during battle entry;
2. show no visible PMD shadow;
3. visually resemble prior LookUp/Sit-style ambient behavior.

A normal battery save (`.sav`) cannot restore compiled-out animation tables, remove PMD shadow pixels, or revert renderer code. Save structure is unchanged. Cross-build emulator save states are not valid renderer evidence because they restore RAM/VRAM/CPU state and must not be used for G3R1 acceptance.

## What the previous CI actually proved

The previous G3 CI proved source generation, installation, compilation, and ROM production. It did **not** prove that the send-out prime targeted the exact active image buffers or that the linked executable visibly exercised the intended G3 assets. Compile PASS was therefore overstated as functional success.

## Confirmed source facts

- G3 ambient manager contains only HOME / Idle / Walk / Nod / Pose / Rotate.
- LookUp / DeepBreath / Sit are not scheduled by the G3 manager.
- PMDCollab SpriteBot confirms that Shadow.png green/red/blue pixels are converted to black shadow pixels according to ShadowSize; Cyndaquil ShadowSize is 1.
- The G3 converter follows that same marker rule.

## Root-cause candidate with concrete code evidence

SoulGold `SetMultiuseSpriteTemplateToPokemon()` can source its template from more than one MonSpritesGfx manager. The original G3 `PmdSoulGold_PrimeBodyFrame()` incorrectly required `gMonSpritesGfxPtr != NULL` and wrote through that global manager only.

This means the prime call could be located immediately before `CreateSprite()` yet still return FALSE or target the wrong manager during send-out.

## G3R1 repair

G3R1 primes `gMultiuseSpriteTemplate.images[0..1]` directly after `SetMultiuseSpriteTemplateToPokemon()` and before `CreateSprite()`. This is the authoritative frame-image array for the exact Pokémon sprite about to be created, independent of which MonSpritesGfx manager supplied it.

The normal G1/G2 runtime rolling-cache path remains sealed and unchanged.

## Strengthened gates

G3R1 CI must now fail unless all of the following hold:

- each emitted shadowed PMD frame has a positive alpha-mask delta versus an otherwise-identical body-only conversion;
- final ELF contains Nod/Pose/Rotate player and opponent action symbols;
- final ELF contains send-out prime symbols;
- final ELF does not contain LookUp/DeepBreath/Sit PMD action symbols;
- installed PMD sources and SoulGold host patch are preserved in evidence;
- linker map and `nm` symbol evidence are preserved;
- diagnostic ROM is delivered under a unique G3R1 filename, not a reused LIVE basename.

## Promotion rule

G3 remains **FAILED at runtime** until the user verifies the new uniquely named G3R1 ROM in a cold boot using the normal in-game `.sav`. CI/compile success alone cannot promote this phase.
