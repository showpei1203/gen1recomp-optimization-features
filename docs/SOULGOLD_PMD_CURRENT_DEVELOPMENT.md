# Pokémon SoulGold PMD Animated Prototype — CURRENT DEVELOPMENT

Date: 2026-08-28
Status: ACTIVE / GBA-FIRST / G1 SEALED / G2 BEHAVIOR PASS / G3-G3R1 RUNTIME FAIL / G3R2 COMPILE PASS — HUMAN RUNTIME PENDING

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
- G1/G2/G3/G3R1/G3R2 do not change the save structure.
- Normal in-game `.sav` files do not contain PMD action tables, renderer code, battle sprite assets or PMD shadow assets and cannot revert a new ROM to old PMD behavior.
- Save-state / quick-state validation is forbidden across prototype ROM revisions because emulator states may preserve old RAM, sprite state and execution position.

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
5. On initial battle entry, SoulGold still displays the legacy battle sprite before PMD takes over — **FAIL / LATER ROOT CAUSE FOUND**.

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
- `Charge`: genuine directional but reserved for later combat/ecology work, not general grounded ambient.

This policy supersedes the overly strict interpretation that every intermediate frame must itself remain at 45 degrees.

## PMD shadow policy — FORMAL RULE

PMD shadow is part of the battle presentation contract, not optional decoration.

- Every eligible battle action must have a matching PMDCollab `*-Shadow.png` sheet with the same sheet dimensions as its body animation.
- Shadow rendering follows PMDCollab SpriteBot marker semantics and the species `AnimData.xml` `ShadowSize` value.
- Cyndaquil has `ShadowSize=1`: green and red shadow marker pixels are active; blue marker pixels are not.
- Active shadow markers are rendered as opaque black underneath the PMD body.
- For current grounded/small-OBJ ambient actions, shadow and body remain in one atomic 64x64 presentation frame before palette remap.
- The G1 two-slot rolling renderer remains unchanged because it swaps the already-combined frame.
- Future jump/float/composite actions may require a separate ground-shadow OBJ when body vertical motion must be independent of shadow position. That is a later renderer gate and must not regress the current grounded path.

Import tooling must perform both a directional-sheet audit and shadow-sheet audit before an action is admitted to the battle asset pool.

## G3 / G3R1 — COMPILE PASS, HUMAN RUNTIME FAIL

G3 and G3R1 are retained as failure evidence. They must not be promoted or used as a visual baseline.

Human runtime rejection received 2026-08-28:

1. Initial player battle entry still visibly used the legacy SoulGold battle sprite before PMD takeover.
2. PMD shadow was visibly displaced relative to the apparent ground point in the approved 45-degree view.
3. Compared with G2, the PMD body unnaturally bobbed / floated vertically and no longer felt planted on the battlefield.

These were not caused by the user's normal `.sav` file.

### Proven root cause A — battle-entry last writer

G3/G3R1 primed PMD HOME too early.

SoulGold has later native controller paths that call `BattleLoadMonSpriteGfx(...)` after the early PMD prime. Those native loads rewrite the Pokémon image buffers with the legacy front/back battle graphics before send-out continues.

Therefore the correct ownership rule is:

**PMD must be the last body-pixel writer after every relevant native mon-gfx load, not merely an early writer before `CreateSprite(...)`.**

A pre-create PMD prime may remain as an early safety measure, but it is insufficient by itself.

### Proven root cause B — per-frame body-center normalization is wrong for grounded PMD animation

The old converter read the green body-center marker from each frame's PMD `Offsets.png` and translated every frame so that this body-center landed on one fixed GBA anchor.

That interpretation is rejected for grounded battle presentation.

Measured pinned Cyndaquil PMD data proves why:

- `Idle / UpRight` body centers change from `(7,15)` to `(8,16)`, while the raw PMD shadow stays at the same ground position.
- `Walk / UpRight` body centers alternate `(7,15) -> (6,16) -> (7,15) -> (6,16)`, while the raw PMD shadow bbox remains constant across all four frames: approximately `x=5..18, y=17..22`.

The PMD author is intentionally moving the body inside a fixed local ground/shadow coordinate system. Re-centering every frame moves the entire body+shadow frame in the opposite direction and manufactures artificial 1-pixel vertical/horizontal drift.

**Per-frame body-center translation is therefore formally forbidden for grounded PMD ambient actions.**

The green body-center marker remains useful metadata for analysis, hit/contact semantics and future action logic, but it must not drive per-frame grounded placement.

## G3R2 — POST-NATIVE-LOAD OWNERSHIP + PMD GROUND ANCHOR

Status: `COMPILE / LINK / CI PASS — HUMAN RUNTIME VISUAL ACCEPTANCE PENDING`

Authoritative build:

- framework commit: `dda24c468f1cec54bc3fb4914917927d4abe49d1`
- GitHub Actions run: `33157188171`
- bytes: `33554432`
- SHA-256: `5afbdf6aae1efcc153b9da067a932d52fbb57aa8feb90fe55040950c59cc289a`
- CRC32: `0978A865`
- full SoulGold build: **PASS**
- PMD warning/error audit: **PASS**
- final ELF symbol gate: **PASS**
- ROM artifact upload: **PASS**
- save structure: **UNCHANGED**

### G3R2 body ownership rule

Installer evidence reports:

- pre-create PMD prime paths: `2`
- post-native-`BattleLoadMonSpriteGfx` PMD re-prime paths: `5`

Every relevant controller path that performs a native `BattleLoadMonSpriteGfx(..., battler/battlerPartner)` is followed by `PmdSoulGoldPrototype_PrimeBattlerBody(...)` before native send-out choreography continues.

The intent is to preserve SoulGold's native Poké Ball, timing, movement, affine effects and callbacks while ensuring PMD HOME is the final Pokémon body pixel authority.

### G3R2 grounded placement rule — FORMAL

Policy identifier:

`PMD_TILE_SPACE_ACTION_CONSTANT_SHADOW_GROUND_ANCHOR`

Rules:

- Preserve the PMD action's raw tile-space relationship between body and shadow.
- HOME/Idle frame 0 establishes the species/side battlefield ground reference.
- Each grounded action receives exactly one fixed translation for its entire sequence.
- Different actions may receive different fixed translations when their source tile dimensions/ground anchors differ.
- Every frame within one action must have exactly the same `paste_x` and `paste_y`.
- PMD body-center metadata is recorded but `body_center_controls_translation = false`.
- Per-frame body-center re-centering is forbidden.
- Every emitted battle frame must contain a non-empty authentic PMD shadow contribution.

CI rejects any grounded action whose frames contain more than one placement tuple.

### G3R2 ambient set

Cyndaquil benchmark remains:

`HOME -> Idle -> HOME -> Walk -> HOME -> Nod -> HOME -> Pose -> HOME -> Rotate -> HOME`

`LookUp`, `DeepBreath`, and `Sit` remain banned from battle ambient.

### G3R2 human acceptance target

1. Cold-boot battle entry never visibly exposes the legacy Cyndaquil battle body.
2. Native SoulGold send-out timing/motion remains normal.
3. Cyndaquil appears as PMD HOME from the first visible Pokémon-body frame.
4. PMD shadow reads as grounded underneath the character in the approved 45-degree view.
5. No artificial whole-body 1-pixel vertical/horizontal bob caused by converter re-centering is visible.
6. Intentional internal PMD body/foot motion remains intact.
7. `LookUp`, `DeepBreath`, and `Sit` never appear.
8. `Rotate` remains and naturally returns to 45-degree HOME.
9. Native move ownership still returns cleanly to HOME and then Rich Ambient.
10. Normal `.sav` continuity remains intact.

Until this list is visually accepted by the user, G3R2 is not formally promoted beyond compile/link/structural PASS.

## User reference ROM

The user's `Pokemon-SoulGold-v1.gba` remains intended as `USER_REFERENCE_ROM`, not a destructive patch base. Its exact fingerprint should be recorded when the attachment is available to the execution environment.

## Deferred intentionally

- `Hop` (`24x72`)
- PMD `Attack` (`64x72`)
- `Swing` (`72x80`)
- large/composite OBJ policy
- independent ground-shadow OBJ for airborne actions
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
