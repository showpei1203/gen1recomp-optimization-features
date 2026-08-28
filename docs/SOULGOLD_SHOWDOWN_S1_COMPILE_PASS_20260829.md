# SoulGold Showdown S1 Compile PASS

Date: 2026-08-29
Branch: `feature/showdown-animated-battlers`
Status: COMPILE/LINK PASS, HUMAN RUNTIME VISUAL PENDING

## Authority

- External SoulGold baseline: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- Compile-tested framework commit: `2d1fbfa738a9dd6f1cc75353ba8896953ac412a7`
- Current branch also includes collision regression commit: `b64532da73aa1abe8133b0ac375f95dbbe0103d7`
- GitHub Actions run: `33221436055`
- Source archive: official Pokémon Showdown `sprites.zip`
- PMD runtime dependency: NONE

## S1A scope

Only Cyndaquil is bound in runtime.

- opponent: `sprites/ani/cyndaquil.gif`
- player: `sprites/ani-back/cyndaquil.gif`
- runtime ownership: move-selection-only
- palette policy: remap Showdown visible pixels to existing SoulGold Cyndaquil palette entries 1..15
- transparent index: 0
- fixed GBA canvas: 64x64

This scope is intentionally conservative. Native SoulGold remains authoritative during send-out, switch, move animation, hit, and faint paths while the first Showdown body loop is being proven on hardware.

## Actual official asset results

### Front

- source canvas: 38x45
- scale: 1.0
- GBA canvas: 64x64
- frames: 50
- duration per frame: 2 ticks at 60 Hz
- full loop: 100 ticks, approximately 1.667 seconds

### Back

- source canvas: 45x45
- scale: 1.0
- GBA canvas: 64x64
- frames: 49
- duration per frame: 2 ticks at 60 Hz
- full loop: 98 ticks, approximately 1.633 seconds

No source downscaling is required for Cyndaquil.

## CI result

All S1 build-gate stages passed:

1. exact SoulGold baseline checkout
2. deterministic S0 conversion self-test
3. official Showdown archive retrieval
4. exact `ani` / `ani-back` lane selection
5. Cyndaquil front/back asset staging
6. isolated Showdown runtime installation
7. PMD dependency separation audit
8. complete SoulGold compile/link
9. Showdown compiler warning/error audit
10. build evidence upload
11. test ROM artifact upload

Build result:

- ROM: `Soulgold_Beta_1.gba`
- size: 33,554,432 bytes
- SHA-256: `ace151dccc926cd0ba2c3a54222d99da002446deb59d26311fc9308d2c42ee82`
- CRC32: `00411CA4`

## Incident closed during S1

The official archive contains both:

- `sprites/ani/cyndaquil.gif`
- `sprites/gen5ani/cyndaquil.gif`

and corresponding back folders.

The original suffix matcher incorrectly treated `gen5ani/...` as an `ani/...` match. The ingester now compares the final directory component exactly. A deterministic ZIP regression test includes both families and confirms `ani` and `ani-back` are selected without collision.

## Promotion state

S0 conversion: PASS
S1 compile/link: PASS
S2 human runtime visual: PENDING

S1 is not yet a formal runtime pass. A successful ROM build proves integration integrity, not that the animated body is visually correct on mGBA/AYN THOR.

## S2 acceptance checklist

Use the generated S1 ROM in RetroArch + mGBA on AYN THOR and enter a battle containing Cyndaquil.

Required observations:

- player Cyndaquil back sprite becomes the Showdown animated loop at move selection
- opponent Cyndaquil front sprite becomes the Showdown animated loop at move selection
- animation loops continuously and at plausible speed
- no left/right or up/down frame jitter
- no palette corruption
- no square background/mask artifact
- move selection remains responsive
- attack animation still runs normally
- after a move, Showdown idle ownership returns cleanly
- HP/status/hit/faint/switch paths remain functional
- no crash or invisible battler

Only after S2 human runtime PASS should we expand to Pikachu, Charizard, Onix, or broader roster automation.
