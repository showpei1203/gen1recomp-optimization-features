# PMD × DRAMATIC_SHAPE Battle Occlusion Diagnosis

Date: 2026-08-19

## Finding

The reported tree/foreground occlusion problem is **not** a Presentation Timeline I/II regression.

Byte-exact comparison:

- Formal PMD source authority: `pmd_idle_battle_sprites v0.1.95c`
- v0.1.95c `main.lua` SHA-256: `11a1b8c3f8cdc098a8f7792b4b5fcb9557f62400999685dcc9337eb893a6f883`
- Current tested PMD candidate: `v0.1.96c`
- v0.1.96c `main.lua` SHA-256: `1169cf78409c9b01e7a06d42e3a91b1702e2a95a82f80b736d2a5a7b7d31556b`

The `battle.overlay` draw-order block is functionally unchanged between the two versions. Both versions draw PMD switch/body sprites as a screen-space overlay and contain no z/depth/occlusion integration. The v0.1.95c source itself states that PMD sprites are drawn later in `battle.overlay`.

## Exact DRAMATIC_SHAPE 1.8.2 source snapshot

Thor exact snapshot captured on 2026-08-19:

- ZIP: `GEN1RECOMP_DRAMATIC_SHAPE_EXACT_SOURCE_20260819_201011.zip`
- ZIP SHA-256: `5a2b6db26bda3a0307b824e226b4126af89a2ef6d6ec8d39f8566c5ba7a9984c`
- Drive ZIP ID: `12H_VEz4gUzbD-6mvKEotryjB7i48UOxI`
- Snapshot folder ID: `1MuzkDSY3xfOZPFMq2u5_3nPekNwrKo_8`
- exact `main.lua` SHA-256: `f8fb8616f30c3a9a7be16dce4b48e706c3d97dedfccbb9d0e6a0e8be56471ac1`
- exact `manifest.json` SHA-256: `b8ef6c5abc8c876fb15171877b27ef2b02728de49875a9e1fa8885e8601b54b2`
- manifest version: `1.8.2`
- priority: `100`
- permission: `engine_internals`

## Exact core render authority

The direct-cat core-library capture is now available:

- ZIP: `GEN1RECOMP_DRAMATIC_SHAPE_CORE_LIBS_20260819_201743.zip`
- Drive ZIP ID: `1aemyrp-JfEG7-B8SNcIPkCQJniIC1r89`
- `OverworldBattle.lua` SHA-256: `a92c90c236d2b4d4028ea03c987924353168db2b0a63e30edc323d88dab71226`
- `VoxelScene.lua` SHA-256: `d273b3f94b6e0822710d4ce02b830762a46399f2a4385ab1b96919c25781b7ec`
- `Voxel3D.lua` SHA-256: `923f0b827ce6f8834d1fa763861b96e1338a9f3ddfdb4ead78cd9eb688b9bc4f`
- Drive seam diagnosis ID: `1coEiT46-5idkpmhr__9u7O1X2mRKj6Qt`

The exact 1.8.2 source establishes the render chain conclusively:

1. `OverworldBattle.update()` calls `OverworldBattle.textures(session.battle)` every frame before the staged world shot is rendered.
2. `sideTexture()` renders each side's `BattleState.drawPicsLayer` into a transparent 160×144 canvas at canonical anchor `TEX_AX=80`, `TEX_AY=96`.
3. Those per-side canvases are passed to `BattleScene.render()`.
4. `VoxelScene` draws the resulting battle cards using `Voxel3D.draw(BattleBillboard.mesh(), card.tex, card.model, BattleBillboard.PULL)`.
5. `Voxel3D` uses a real `lequal` depth buffer, so terrain, buildings, and trees can naturally occlude the battle cards.
6. The same battle cards participate in the shadow pass.

This is the exact seam the PMD integration must use.

## Confirmed PMD incompatibility

Current PMD source intercepts `pokemon.sprite` when `ctx.kind == "battle"`, sets `trueColor`, and returns `transparent.png`.

Therefore DRAMATIC_SHAPE's `sideTexture()` sees a transparent native battle picture and builds a transparent world card. The real PMD animated body is then drawn later from `battle.overlay`, after the 3D world/depth pass has already completed.

That makes the observed bug inevitable: a screen-space overlay cannot be occluded by a tree/building already written into the 3D depth buffer.

## Preferred fix

Do **not** solve this with layer-order changes, hard-coded tree masks, per-map clip rectangles, or y-sort.

Create a dedicated two-mod integration candidate that:

1. exposes the current PMD animated body frame to the battle rendering seam;
2. feeds that frame into DRAMATIC_SHAPE's per-side texture canvas instead of leaving the world card transparent;
3. lets `BattleScene` / `VoxelScene` / `Voxel3D` draw the PMD frame as a normal depth-tested battle card;
4. suppresses only the duplicate PMD body draw in `battle.overlay` when a DRAMATIC_SHAPE 3D card successfully owns that side;
5. preserves PMD Presentation Timeline v0.1.96c, move timing, HIT logic, audio-tail ownership, and non-body overlays unchanged.

## Remaining exact-source gate

Two exact 1.8.2 files are still required before producing the first behavioral candidate:

- `lib/BattleScene.lua`
- `lib/BattleBillboard.lua`

These define final card sizing, anchor/model matrix, and camera pull behavior. No candidate should guess those details.

## Runtime context

Current evidence confirms:

- `DRAMATIC_SHAPE 1.8.2` loaded
- `pmd_idle_battle_sprites 0.1.96c` loaded
- `thor_battle_ui` reports DRAMATIC_SHAPE 3D battle compatibility enabled

IIc evidence ZIP: `GEN1RECOMP_PRESENTATION_TIMELINE_IIc_EVIDENCE_20260819_200104.zip`

SHA-256: `0420ce211035f86584a1271da20232f7b16d862bf815184c0f4c93b045b3786a`

Drive evidence ID: `1OBxDEWpLRjgfSj04beGNXvraJ1hl5nK7`

## Classification

`PMD × DRAMATIC_SHAPE Integration Defect`

Timeline work remains valid and should not be rolled back for this defect.
