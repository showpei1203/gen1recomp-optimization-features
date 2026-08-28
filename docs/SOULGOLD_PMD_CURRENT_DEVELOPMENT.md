# Pokémon SoulGold PMD Animated Prototype — CURRENT DEVELOPMENT

Date: 2026-08-28
Status: ACTIVE / GBA-FIRST / G1 COMPILE PASS

## Current baseline authority

- Host: `Eemeliri/soulgold`
- Pinned source commit: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- Upstream lineage: pokeemerald-expansion 1.15.x
- Target runtime: GBA ROM, mGBA desktop, AYN THOR RetroArch + mGBA
- Prototype species: Cyndaquil
- PMD source: `PMDCollab/SpriteCollab` species `0155`
- PMD source revision: `4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- Framework branch: `feature/pmd-portable-battle-framework`
- G1 compile-PASS framework commit: `a28e7595a162566827dcc245b8823a778e59a579`
- GitHub Actions run: `33149304212`

## Current phase

G1 structural runtime candidate compiled successfully. Human visual/runtime acceptance is now the authority gate.

## G1 compile evidence — PASS

The authoritative CI completed all of the following:

1. checkout exact SoulGold source revision;
2. checkout exact SpriteCollab revision;
3. convert Cyndaquil PMD Walk for player and opponent directions;
4. remap the G1 frames to SoulGold's existing Cyndaquil palette;
5. install portable runtime + SoulGold adapter + prototype manager;
6. verify scope invariants;
7. compile and link the complete SoulGold ROM;
8. audit `src/pmd_*` compiler output for warnings/errors;
9. upload the actual test ROM artifact.

Built ROM:

- CI filename: `Soulgold_Beta_1.gba`
- Test designation: `SoulGold-PMD-G1-Cyndaquil-Walk-Test`
- bytes: `33554432`
- SHA-256: `67beea6d040772325d6075391159a4128a8e794b7605800f82269911e3208ab8`
- CRC32: `0EFB799C`
- GBA title header: `POKEMON EMER`
- game code: `BPEE`
- maker code: `01`

The Emerald header is expected because SoulGold is built from the pokeemerald-expansion/decomp lineage; it is not evidence that the wrong source was compiled.

### Host-warning policy used for this gate

The pinned SoulGold source contains a pre-existing unrelated unused local variable in `src/comfy_anim.c`. Therefore the G1 integration build uses `UNUSED_ERROR=0` and `DEPRECATED_ERROR=0` so unrelated host warnings do not mask PMD integration status.

This is not a blanket relaxation for PMD code. The workflow separately rejects the candidate if the build log contains a compiler warning/error originating from `src/pmd_*`.

## G1 renderer contract — compile proven

- `MAX_MON_PIC_FRAMES` remains `2`.
- Animation frame count is independent of resident cache count.
- Cyndaquil Walk uses `4` source frames through only `2` resident battler image slots.
- Player direction: `UpRight`.
- Opponent direction: `DownLeft`.
- PMD Walk durations: `[6, 8, 6, 8]`.
- Source frame size: `24x32`.
- G1 presentation offsets remain `0/0`.
- G1 uses the existing SoulGold Cyndaquil palette to isolate renderer/cache proof from palette ownership.
- The adapter presents staged frames through `RequestSpriteFrameImageCopy(...)`.
- Native `sprite->anims` tables are not replaced.
- `src/data.c` / global `MAX_MON_PIC_FRAMES` plumbing is not modified.

## G1 host ownership policy

PMD body presentation is allowed only when all G1 conditions are satisfied, including:

- battle is in `InBattleChoosingMoves()`;
- battler sprite is the real Pokémon sprite and owns the expected `MonSpritesGfx` frame-image table;
- sprite callback is at a stable dummy callback;
- native battle animation, special animation and status animation owners are inactive.

The objective is deliberately narrow: prove multi-frame PMD playback without fighting SoulGold send-out, switch, move, hit, faint or script-driven presentation.

## Current gate

### G1 — human runtime / visual acceptance

Compile status: `PASS`

Runtime status: `PENDING USER TEST`

Required observations:

1. ROM boots normally.
2. Start/continue a game and enter a battle containing Cyndaquil.
3. During move-selection idle, Cyndaquil should use PMD Walk animation rather than a static stock body.
4. The animation must visibly cycle all four Walk source frames despite only two resident image slots.
5. No checkerboard/corruption, disappearing body, stale half-frame, palette garbage or VRAM tearing.
6. No logical battle-position movement; G1 animation is presentation-only.
7. Opening/send-out, move execution, hit reaction, switch and faint behavior must remain native and stable.
8. After native ownership returns to move selection, PMD presentation should resume without a broken/stale frame.
9. Player-side orientation should visually read correctly as `UpRight`; opponent-side as `DownLeft` if an opponent Cyndaquil is tested.
10. Test on desktop mGBA first, then AYN THOR RetroArch + mGBA.

Compile PASS is not visual PASS. G1 is not promoted to Formal until actual battle evidence is accepted.

## User reference ROM

The user's `Pokemon-SoulGold-v1.gba` is intended to be recorded as `USER_REFERENCE_ROM` rather than used as a destructive patch base. Its file size, GBA header, SHA-256 and CRC32 should be captured when the attachment becomes available to the execution environment. This reference fingerprint remains distinct from the reproducible source-build fingerprint above.

## G2 after G1 visual PASS

Implement Rich Ambient rather than a permanent Walk loop:

`HOME -> ambient action -> settle -> HOME`

Initial Cyndaquil ecology benchmark:

`Idle -> Walk -> HOME -> LookUp -> HOME -> DeepBreath -> HOME -> Rotate -> HOME`

Rules inherited from Gen1recomp:

- PMD Idle is an asset, not the complete idle behavior.
- logical battle position remains locked;
- action choice/timing are species/body-profile driven;
- native move VFX/SFX retain authority;
- combat/native interruption never resumes midway through an old ambient action;
- interruption settles/re-enters HOME and restarts an approved ecology sequence.

## Deferred intentionally

- `Hop` (`24x72`)
- PMD `Attack` (`64x72`)
- `Swing` (`72x80`)
- large/composite OBJ policy
- physical attack state
- special attack state
- hurt state
- formal PMD normal/shiny palette ownership
- batch importer
- second ROM-hack portability proof
- GBC backend

## Formal promotion policy

Compile PASS is not visual PASS.
Structural/runtime PASS is not formal prototype PASS.
No phase may be promoted without actual battle evidence on the target renderer, and AYN THOR remains a required acceptance target.
