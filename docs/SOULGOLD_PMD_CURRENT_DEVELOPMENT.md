# Pokémon SoulGold PMD Animated Prototype — CURRENT DEVELOPMENT

Date: 2026-08-28
Status: ACTIVE / GBA-FIRST / G1 SEALED / G2 BEHAVIOR PASS / G3 ACTIVE

## Current baseline authority

- Host: `Eemeliri/soulgold`
- Pinned source commit: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- Upstream lineage: pokeemerald-expansion 1.15.x
- Target runtime: GBA ROM, mGBA desktop, AYN THOR RetroArch + mGBA
- Prototype species: Cyndaquil
- PMD source: `PMDCollab/SpriteCollab` species `0155`
- PMD source revision: `4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- Framework branch: `feature/pmd-portable-battle-framework`

## G1 authority — PLAYER-SIDE FORMAL PASS / RENDERER SEALED

User visual acceptance on desktop mGBA was received on 2026-08-28.

Accepted:

- PMD Cyndaquil body scale and battle placement are acceptable.
- Background, UI and HP/status boxes remain intact.
- Four Walk source frames play through the two existing resident image slots.
- No visible palette garbage, checkerboard corruption, half-frame tearing or body corruption was reported.

Sealed renderer contract:

- `MAX_MON_PIC_FRAMES` remains `2`.
- Animation length is independent of resident cache count.
- Presentation uses `RequestSpriteFrameImageCopy(...)`.
- Native `sprite->anims` tables are not replaced.
- `src/data.c` / global frame-count plumbing is not modified.
- Player battle-facing source row is `UpRight`; opponent row is `DownLeft`.

G1 must not be rewritten merely to add later behavior.

## Save-file continuity policy

The user will continue one SoulGold save while prototype ROMs are updated.

- Keep ROM/save compatibility unless a phase explicitly requires a save-breaking change.
- Delivered live ROM basename should remain stable when practical.
- Any future save-breaking change must be declared before delivery.
- G1/G2/G3 do not change the save structure.

## G2 authority — RICH AMBIENT BEHAVIOR PASS / VISUAL-FACING PARTIAL

G2 build ROM:

- bytes: `33554432`
- SHA-256: `0831c1c1172ef789c1152bb2955db2789c43b8aeabb207295fae5505e9c42eae`
- CRC32: `554857E1`
- CI run: `33150904208`

Human runtime observations received 2026-08-28:

1. Ambient action switching is fluid — **PASS**.
2. During native move execution, the PMD body freezes/yields ownership; after the move it returns correctly to the idle/ecology loop — **PASS**.
3. The five tested ambient behaviors are clearly distinguishable — **PASS**.
4. Some actions do not visually preserve the desired 45-degree battle facing and therefore read as stiff/odd — **PARTIAL / RULE CREATED**.
5. On initial battle entry, SoulGold still displays the legacy battle sprite before PMD takes over — **FAIL / G3 TARGET**.

G2 proves the HOME/interruption/ecology state machine but is not the final visual-facing authority.

## Battle-facing asset policy — FORMAL RULE

For current and future Pokémon battle ambient assets:

- The action must come from a genuine directional PMD source sheet; shared single-row/non-directional assets are not eligible for battle ambient presentation.
- Player presentation selects the approved 45-degree `UpRight` source orientation; opponent presentation selects `DownLeft`.
- HOME must begin and end at the approved 45-degree battle-facing orientation.
- Intermediate frames may turn, nod, pose, rotate or otherwise change posture naturally.
- A transitional-turn action is acceptable when it naturally settles back to the same 45-degree HOME at completion.
- `Rotate` is explicitly **allowed** because it naturally returns to the battle-facing orientation.
- Import/build tooling must reject non-directional ambient candidates before ROM compilation rather than silently adapting them.

Cyndaquil source audit at the pinned SpriteCollab revision:

- `Idle`: genuine directional — eligible.
- `Walk`: genuine directional — eligible.
- `Nod`: genuine directional — eligible.
- `Pose`: genuine directional — eligible.
- `Rotate`: genuine directional — eligible and explicitly retained.
- `LookUp`: shared single-row/non-directional — banned from battle ambient.
- `DeepBreath`: shared single-row/non-directional — banned from battle ambient.
- `Sit`: shared single-row/non-directional — banned from battle ambient.
- `Charge`: genuine directional but reserved for later combat/ecology work, not general G3 ambient.

This policy supersedes the overly strict interpretation that every intermediate frame must itself remain at 45 degrees.

## PMD shadow policy — FORMAL RULE

PMD shadow is part of the battle presentation contract, not optional decoration.

- Every eligible battle action must have a matching PMDCollab `*-Shadow.png` sheet with the same sheet dimensions as its body animation.
- Shadow rendering follows PMDCollab SpriteBot marker semantics and the species `AnimData.xml` `ShadowSize` value.
- Cyndaquil has `ShadowSize=1`: green and red shadow marker pixels are active; blue marker pixels are not.
- Active shadow markers are rendered as opaque black underneath the PMD body.
- For G3 grounded/small-OBJ ambient actions, shadow and body are composited into the same normalized 64x64 presentation frame before palette remap.
- This gives body/shadow atomic frame synchronization and avoids an extra OBJ/tile-cache/palette ownership layer.
- The G1 two-slot rolling renderer remains unchanged because it simply swaps the already-combined frame.
- Future large jump/float/composite actions may require a separate ground-shadow OBJ when body vertical motion must be independent of shadow position. That is a later renderer gate and must not regress the current grounded path.

Import tooling must perform both a directional-sheet audit and shadow-sheet audit before an action is admitted to the battle asset pool.

## G3 — BATTLE-FACING CLEANUP + PMD FROM FIRST BATTLE FRAME + SHADOW

Status: `IMPLEMENTATION / CI ACTIVE`

### G3 ambient set

Cyndaquil benchmark:

`HOME -> Idle -> HOME -> Walk -> HOME -> Nod -> HOME -> Pose -> HOME -> Rotate -> HOME`

All selected actions are genuine directional sheets at the pinned source revision. `LookUp`, `DeepBreath`, and `Sit` are excluded. Every generated frame includes the authentic PMD per-frame shadow underneath the body.

### G3 battle-entry rule

Goal: the Pokémon body must already be PMD when the native send-out Pokémon sprite is created.

Implementation strategy:

- Keep SoulGold's native Poké Ball/send-out motion, callback timing, affine effects and battle sequencing.
- Immediately before native `CreateSprite(...)` for the Pokémon body, prime both resident battler image slots with the combined PMD HOME body+shadow frame.
- Both cache slots receive the same HOME image so native frame index 0/1 changes during send-out cannot reveal the legacy battle sprite.
- After native send-out ownership settles, the existing G2 HOME/Rich Ambient state machine resumes normal rolling-cache presentation.

This deliberately changes the body pixels, not the native send-out choreography.

### G3 acceptance target

1. Battle entry never visibly exposes the legacy Cyndaquil battle sprite.
2. Native send-out timing/motion remains normal.
3. Cyndaquil appears as PMD HOME from the first visible Pokémon-body frame.
4. PMD shadow is visible, grounded correctly, and remains synchronized with the body.
5. `LookUp`, `DeepBreath`, and `Sit` never appear in ambient behavior.
6. `Rotate` remains and naturally returns to the 45-degree HOME.
7. Idle/Walk/Nod/Pose/Rotate remain visually distinct and smooth.
8. Move interruption and post-move HOME recovery do not regress.
9. Save continuity remains intact.

## User reference ROM

The user's `Pokemon-SoulGold-v1.gba` remains intended as `USER_REFERENCE_ROM`, not a destructive patch base. Its exact fingerprint should be recorded when the attachment is available to the execution environment.

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
