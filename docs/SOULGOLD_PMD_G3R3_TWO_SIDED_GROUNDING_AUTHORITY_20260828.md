# SoulGold PMD G3R3 — Two-Sided Grounding Authority

Date: 2026-08-28
Status: COMPILE / LINK / CI PASS — HUMAN RUNTIME PENDING

## Build authority

- Framework build commit: `7f8a2b8ed2c7bc4f7ed18e10f20deed2bfeb8394`
- GitHub Actions run: `33160878157`
- SoulGold source: `Eemeliri/soulgold@b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- SpriteCollab source: `PMDCollab/SpriteCollab@4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- ROM bytes: `33554432`
- ROM SHA-256: `730660ab5682ad702a418436b88121d70bb44070433faceaadf7c4c6ed9a3ca0`
- ROM CRC32: `2241E024`
- Full SoulGold build: PASS
- PMD warning/error audit: PASS
- Final ELF G3R3 symbol gate: PASS
- ROM artifact upload: PASS
- Save structure: UNCHANGED
- `MAX_MON_PIC_FRAMES`: UNCHANGED (`2`)
- Native `sprite->anims`: UNCHANGED

Compile PASS is not visual PASS. Human mGBA acceptance remains required before promotion.

## G3R2 runtime rejection carried forward

Human runtime evidence showed three independent failures:

1. Opponent Marill graphics were corrupted / contaminated.
2. Cyndaquil still appeared to float or bob vertically during grounded ambient presentation.
3. `Pose` visually faced the screen / waved and did not return naturally to the approved 45-degree HOME.

G3R2 must not be used as a visual baseline.

## Root cause — opponent contamination

The previous installer inserted PMD re-prime calls after native `BattleLoadMonSpriteGfx(...)` call sites. At least one call lived under a naked `if` without braces, so inserting a second statement after the native load changed effective control-flow ownership: the PMD prime could execute unconditionally even when the native load did not.

The previous all-in-one prime helper also wrote `gMultiuseSpriteTemplate.images`, a global active template. A Cyndaquil prime could therefore write PMD Cyndaquil pixels into a template / image array later associated with another battler such as Marill.

### Formal ownership rule

G3R3 splits ownership into two explicit operations:

- **Template prime**: permitted only immediately after `SetMultiuseSpriteTemplateToPokemon(species, position)` and before the corresponding `CreateSprite(...)`. It carries the explicit species selected for that sprite creation.
- **Loaded-buffer prime**: permitted only at the tail of `BattleLoadMonSpriteGfx(...)`, after the native load has determined the actual species and written the current battler backing buffer. It touches only the current battler canonical/live buffers and never the global multiuse template.

Do not reintroduce an all-in-one helper that opportunistically writes canonical buffer + global template + live sprite together.

Do not patch every `BattleLoadMonSpriteGfx` call site. Keep the loaded-buffer ownership hook inside the function that actually performs the load.

## G3R3 two-sided species registry

This acceptance gate intentionally tests both sides with PMD assets in the same battle:

- Player: `SPECIES_CYNDAQUIL`, PMD source `sprite/0155`, direction `UpRight`.
- Opponent: `SPECIES_MARILL`, PMD source `sprite/0183`, direction `DownLeft`.

Only these explicit species+side pairs are PMD-enabled in the G3R3 benchmark. Unsupported species/side pairs must remain untouched.

The test exists specifically to expose cross-battler buffer/template contamination that a one-sided test can hide.

## Grounding authority — PMD Shadow.png WHITE origin

SpriteCollab / SpriteBot semantics distinguish two concepts in `*-Shadow.png`:

- green/red/blue pixels describe the visible shadow mask selected by `ShadowSize`;
- the WHITE pixel is the shadow offset/origin marker.

G3R2 incorrectly reasoned from the colored shadow bbox. G3R3 instead uses the WHITE shadow-origin marker as the grounding normalization anchor.

For grounded ambient actions:

- visible shadow still follows `ShadowSize` marker rules;
- body and visible shadow remain composited into one 64x64 frame for the sealed two-slot renderer;
- the WHITE shadow-origin marker controls normalization;
- PMD green body-center offsets do not control grounded placement;
- runtime `presentationX` and `presentationY` are both `0`;
- intentional body/foot motion remains inside the frame;
- the renderer must not move the whole body+shadow unit to compensate for body-center changes.

### Pinned source audit

Cyndaquil player / UpRight:

- Idle: every frame shadow origin `(12,20)`
- Walk: every frame shadow origin `(12,20)`
- Nod: every frame shadow origin `(12,20)`
- Rotate: every frame shadow origin `(12,20)`

Marill opponent / DownLeft:

- Idle: every frame shadow origin `(16,24)`
- Walk: every frame shadow origin `(16,24)`
- Nod: every frame shadow origin `(16,24)`
- Rotate: every frame shadow origin `(16,24)`

These constant source origins are a structural gate. If runtime still shows whole-body vertical drift in G3R3, investigate SoulGold live sprite callbacks/OAM/native animation state rather than adding more per-frame converter translation.

## Ambient action authority

G3R3 grounded benchmark uses only:

`HOME -> Idle -> HOME -> Walk -> HOME -> Nod -> HOME -> Rotate -> HOME`

`Pose` is excluded from G3R3 because human evidence rejected its battle-facing behavior and its grounding/origin behavior differs from the accepted grounded set.

`LookUp`, `DeepBreath`, and `Sit` remain excluded from battle ambient because their source form does not satisfy the accepted directional battle-facing contract.

`Rotate` remains explicitly allowed: intermediate turning is acceptable because the action naturally settles back to the approved 45-degree HOME.

Do not add a replacement fifth action merely to preserve an arbitrary action count.

## SpriteCollab parser compatibility rule

Marill `AnimData.xml` contains legal `CopyOf` aliases that omit `<Index>`, e.g. `Emit -> Withdraw`.

G3 parser rule:

- `Name` is mandatory.
- A real/non-alias action without `Index` is invalid.
- A `CopyOf` alias may omit `Index` and must not cause the entire species import to fail.
- This compatibility belongs to the G3 wrapper until the portable base parser is deliberately promoted; do not weaken the sealed G1/G2 converter incidentally.

## Renderer contract retained

G3R3 continues to reuse the sealed G1 renderer:

- two resident frame slots;
- animation length independent of resident slot count;
- inactive-slot staging + `RequestSpriteFrameImageCopy(...)` presentation;
- no global `MAX_MON_PIC_FRAMES` increase;
- no native `sprite->anims` replacement;
- logical battle position remains locked.

G2 interruption behavior remains required:

- native move/action ownership may interrupt PMD ambient;
- an interrupted ambient action is abandoned;
- after native release, return HOME first;
- restart an approved ambient sequence;
- never resume halfway through the old action.

## Human acceptance checklist for G3R3

1. First visible player body is PMD Cyndaquil.
2. First visible opponent body is PMD Marill.
3. Neither battler ever displays pixels from the other species.
4. Native send-out motion/timing remains intact.
5. Cyndaquil shadow reads as grounded under Cyndaquil.
6. Marill shadow reads as grounded under Marill.
7. No artificial whole-body vertical drift through Idle/Walk/Nod/Rotate or HOME transitions.
8. No `Pose`, `LookUp`, `DeepBreath`, or `Sit` appears.
9. `Rotate` returns naturally to the approved 45-degree HOME.
10. Native Move -> HOME -> ambient recovery remains correct.
11. Normal `.sav` continuity remains intact; old save states are not valid cross-version evidence.

Until these are visually accepted, G3R3 remains CI PASS / runtime pending.
