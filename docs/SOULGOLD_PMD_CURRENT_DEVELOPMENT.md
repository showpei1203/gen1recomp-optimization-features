# Pokémon SoulGold PMD Animated Prototype — CURRENT DEVELOPMENT

Date: 2026-08-28
Status: ACTIVE / GBA-FIRST / G1 PLAYER-SIDE VISUAL PASS / G2 STARTED

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

## G1 authority — PLAYER-SIDE FORMAL PASS

User visual acceptance on desktop mGBA was received on 2026-08-28 using the produced G1 test ROM.

Accepted observations:

- SoulGold boots normally.
- Player-side Cyndaquil is replaced by the PMD presentation during move-selection idle.
- PMD body scale and screen placement are acceptable.
- Battle background, battle UI and HP/status boxes remain visually intact.
- No visible palette garbage, checkerboard corruption, half-frame tearing or broken body was reported.
- User explicitly judged the result positively and will continue using the same save progression for subsequent prototype ROMs.

Evidence note:

- The supplied screenshot proves static placement/body/UI integrity.
- The user's live test report is the human authority for the animated behavior.
- Opponent-side Cyndaquil visual acceptance remains pending a convenient encounter; it is not required to block G2 because the primary starter/player renderer path is now proven.
- AYN THOR acceptance remains required before a later production/formal cross-device promotion.

### G1 renderer contract — SEALED

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

G1 must not be rewritten merely to implement G2 behavior. New behavior layers must preserve this renderer contract.

## Save-file continuity policy

The user will continue one SoulGold save while prototype ROMs are updated.

Policy:

- Keep ROM/save compatibility unless a phase explicitly requires a save-breaking engine/data change.
- Prefer a stable delivered ROM filename so mGBA can continue to resolve the same `.sav` without manual work.
- When versioned ROM filenames are unavoidable, the user can rename the existing `.sav` to the new ROM basename.
- Any future save-breaking change must be declared before delivery; silent save-format changes are forbidden.

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

## G2 — Rich Ambient

Status: `IMPLEMENTATION STARTED`

Goal: replace the permanent Walk proof loop with species-aware ambient ecology while preserving the sealed two-slot renderer.

Initial Cyndaquil ecology benchmark:

`HOME -> Idle -> HOME -> Walk -> HOME -> LookUp -> HOME -> DeepBreath -> HOME -> Rotate -> HOME`

Rules inherited from Gen1recomp:

- PMD Idle is an asset, not the complete idle behavior.
- Logical battle position remains locked.
- Presentation motion never changes battle coordinates.
- Action timing follows PMD metadata plus species/body profile timing.
- Every ambient action returns to an explicit HOME boundary.
- Native move VFX/SFX and native battle ownership retain priority.
- If native combat/sendout/switch/status ownership interrupts ambient behavior, the old ambient action is abandoned.
- After interruption, presentation returns to HOME and starts a newly approved ambient sequence; it never resumes midway through the stale action.
- G2 must not increase `MAX_MON_PIC_FRAMES` or replace native `sprite->anims`.

### G2 first acceptance target

Player-side Cyndaquil at move selection should visibly cycle through multiple PMD behaviors over time, with pauses/Home holds that make it read as a living Pokémon rather than a looped GIF.

Required visual properties:

1. HOME is stable and does not drift.
2. Walk, LookUp, DeepBreath and Rotate remain visually centered around HOME.
3. No action causes logical battle displacement.
4. No stale partial frame after choosing/finishing a move.
5. Native move execution remains visually authoritative.
6. After move execution, Cyndaquil returns HOME before ambient ecology resumes.
7. G1 body integrity and palette quality do not regress.

## User reference ROM

The user's `Pokemon-SoulGold-v1.gba` is intended to be recorded as `USER_REFERENCE_ROM` rather than used as a destructive patch base. Its file size, GBA header, SHA-256 and CRC32 should be captured when the attachment becomes available to the execution environment. This reference fingerprint remains distinct from the reproducible source-build fingerprint above.

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
No phase may be promoted without actual battle evidence on the target renderer, and AYN THOR remains a required later acceptance target.
