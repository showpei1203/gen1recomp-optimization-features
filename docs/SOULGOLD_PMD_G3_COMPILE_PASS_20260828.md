# SoulGold PMD G3 Compile Evidence — 2026-08-28

Status: **COMPILE PASS / HUMAN VISUAL ACCEPTANCE PENDING**

## Authority

- SoulGold: `Eemeliri/soulgold`
- SoulGold revision: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- SpriteCollab revision: `4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- Framework branch: `feature/pmd-portable-battle-framework`
- Framework build commit: `d59698d6b8df526fd1173e873a84bd16e419c3ad`
- GitHub Actions run: `33152897697`

## G3 gate

Cyndaquil battle presentation candidate:

- ambient: `HOME -> Idle -> HOME -> Walk -> HOME -> Nod -> HOME -> Pose -> HOME -> Rotate -> HOME`
- banned non-directional ambient: `LookUp`, `DeepBreath`, `Sit`
- player source orientation: `UpRight`
- opponent source orientation: `DownLeft`
- transitional turning is permitted when the action naturally returns to 45-degree HOME; `Rotate` is explicitly accepted.
- both resident battler image slots are primed with PMD HOME before native Pokémon `CreateSprite(...)`, so the candidate is designed to eliminate the legacy battle-sprite flash on send-out without replacing SoulGold's native send-out choreography.
- authentic PMDCollab per-action `*-Shadow.png` is rendered using SpriteBot-compatible `ShadowSize` marker rules and composited under each body frame before 64x64 normalization.
- Cyndaquil `ShadowSize=1`.
- body + shadow are atomically swapped through the sealed G1 two-slot rolling renderer.

## CI results

- directional + PMD-shadow asset preparation: PASS
- G3 install candidate: PASS
- scope invariants: PASS
- full SoulGold compile/link: PASS
- PMD source warning/error audit: PASS
- ROM artifact upload: PASS
- save structure: UNCHANGED
- `MAX_MON_PIC_FRAMES`: UNCHANGED (`2`)
- native `sprite->anims`: UNCHANGED
- G1 renderer contract: SEALED / REUSED

## Built ROM

- CI filename: `Soulgold_Beta_1.gba`
- delivered basename: `SoulGold-PMD-LIVE.gba`
- bytes: `33554432`
- SHA-256: `726df0be3323c6d9a221f55fc3e49ce136b64103a562419b99ddf11b4a8d41a3`
- CRC32: `774C447A`

The ROM was downloaded from the CI artifact and independently hashed again in the execution environment; byte count, SHA-256 and CRC32 matched the CI evidence.

## Human acceptance still required

1. No legacy Cyndaquil battle body appears at initial send-out.
2. Native send-out motion/timing remains correct.
3. PMD HOME is the first visible Pokémon body frame.
4. PMD shadow is visible, correctly grounded, and synchronized with each action.
5. Only Idle/Walk/Nod/Pose/Rotate appear in ambient ecology.
6. Rotate returns naturally to the 45-degree HOME.
7. Move interruption and post-move HOME recovery do not regress.
8. Existing save continues normally.
