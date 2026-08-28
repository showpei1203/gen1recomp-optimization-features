# SoulGold PMD G3R1 Candidate — 2026-08-28

Status: **CI / BINARY PASS — USER RUNTIME ACCEPTANCE PENDING**

G3 itself remains a runtime FAIL. G3R1 is a repair candidate and is not promoted until human battle testing passes.

## ROM

- unique filename: `SoulGold-PMD-G3R1-dfe16d16.gba`
- bytes: `33554432`
- SHA-256: `dfe16d16d1ce37193182e03a5eedba5f965ac2630cfa07892a1bca5cd6a20454`
- CRC32: `F9C901AB`
- workflow run: `33154721662`
- framework commit: `e1d7701c05315011df2d126dfec7e46ad9bec68b`
- SoulGold source: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- SpriteCollab source: `4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- save structure: unchanged

## G3R1 repair

The original G3 send-out prime assumed `gMonSpritesGfxPtr` was the manager owning the image buffers at send-out. SoulGold can instead select its sprite template from another MonSpritesGfx manager. G3R1 therefore primes the exact `gMultiuseSpriteTemplate.images[0..1]` selected immediately after `SetMultiuseSpriteTemplateToPokemon()` and before `CreateSprite()`.

Both resident image slots receive PMD HOME body+shadow, preventing native frame index 0/1 changes from exposing the legacy body if the runtime path behaves as expected.

## CI gates passed

- strict directional asset gate: PASS
- G3R1 active-template send-out-prime source gate: PASS
- full SoulGold compile/link: PASS
- PMD source warning/error audit: PASS
- final ELF required symbol gate: PASS
- final ELF banned LookUp/DeepBreath/Sit action-symbol gate: PASS
- linker map preservation: PASS
- installed source/host patch evidence preservation: PASS
- PMD shadow per-frame pixel alpha-delta gate: PASS

## Linked PMD ambient authority

Allowed and linked:

- Idle
- Walk
- Nod
- Pose
- Rotate

Banned from final PMD action symbols:

- LookUp
- DeepBreath
- Sit

## PMD shadow pixel evidence

Every generated shadowed frame was compared with an otherwise-identical body-only conversion. Every frame added opaque shadow pixels before palette remap.

Player ranges:

- Idle: 21–27 extra pixels/frame
- Walk: 22–27
- Nod: 40–48
- Pose: 36–39
- Rotate: 5–51

Opponent ranges:

- Idle: 47
- Walk: 36–47
- Nod: 36–43
- Pose: 36–39
- Rotate: 5–51

## Runtime acceptance procedure

- Keep and use the normal in-game `.sav`; no restart is required.
- If the emulator matches save files by basename, copy/rename the existing `.sav` to match the unique G3R1 ROM basename.
- Cold boot the G3R1 ROM.
- Do not load a cross-build emulator Save State / quick-state.
- Verify battle entry first visible Pokémon body is PMD.
- Verify a visible PMD shadow beneath the body.
- Verify Rotate returns naturally to the 45-degree HOME.
- Verify move interruption still returns to HOME and then ambient behavior.

Only user runtime evidence can promote G3R1 beyond candidate status.
