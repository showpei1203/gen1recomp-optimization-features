# PMD v0.1.97a × DRAMATIC_SHAPE 1.8.2 — Depth Integration I

Status: **TEST-ONLY / Integration Candidate**

## Source authority

PMD source:
- `pmd_idle_battle_sprites v0.1.96c`
- main.lua SHA-256: `1169cf78409c9b01e7a06d42e3a91b1702e2a95a82f80b736d2a5a7b7d31556b`
- manifest.json SHA-256: `63371f9fef4996eef71b77b1ec4697a8bdac04c07bd59f068077449f1d7c0044`

DRAMATIC_SHAPE source:
- version `1.8.2`
- `lib/OverworldBattle.lua` SHA-256: `a92c90c236d2b4d4028ea03c987924353168db2b0a63e30edc323d88dab71226`
- `lib/BattleScene.lua` SHA-256: `31d6c945ea8274c56f9db2ecfee6ecf334f9ad9a5e682abb4e551ac096ec5ef8`
- `lib/BattleBillboard.lua` SHA-256: `0ee39926a60de750f8e3ae8f9ae7d8c87d59d5e66136d13b8fe0a73c6bea0d42`
- manifest.json SHA-256: `b8ef6c5abc8c876fb15171877b27ef2b02728de49875a9e1fa8885e8601b54b2`

## Root cause

DRAMATIC_SHAPE 1.8.2 normally renders each battle side into a 160×144 side texture, converts that texture into a real 3D battle card, and sends it through its existing Voxel3D depth/shadow path. Foreground trees and buildings therefore naturally occlude the stock Pokémon card.

PMD instead returns a transparent stock battle sprite and later draws the live PMD body in `battle.overlay`, after the 3D depth pass has finished. The PMD body therefore floats in front of trees/buildings regardless of real depth.

## Candidate behavior

Integration I keeps Presentation Timeline IIc unchanged and only moves active PMD body rendering into the existing DRAMATIC_SHAPE side-texture seam when DRAMATIC_SHAPE owns the staged battle.

1. PMD exposes `BattleState:pmdDramaticShapeSideTexture(side, anchorX, anchorY)`.
2. `OverworldBattle.sideTexture()` optionally asks PMD to draw its current live animation frame while the correct 160×144 side canvas is bound.
3. The resulting canvas continues through the stock `BattleScene` / `BattleBillboard` / `Voxel3D` depth pipeline.
4. PMD's old 2D shadow is suppressed only inside the 3D card path; the real card casts its normal alpha-silhouette shadow.
5. PMD player/enemy sheets are already direction-specific, so `nativeFacing=true` prevents DRAMATIC_SHAPE from mirroring the player card a second time.
6. Overlay body drawing is suppressed per side only after that side is successfully owned by the 3D card; otherwise the legacy overlay remains a fallback.
7. `BattleBillboard.lua` and `Voxel3D.lua` remain byte-exact unchanged.

Switch-recall ghost remains on the legacy overlay path in Integration I.

## Candidate hashes

- PMD main.lua: `8478d26620607ac0dee863090b2abeeffaa475d94b40a22400a8e6ad8997c065`
- PMD manifest.json: `1559de038a250661ed276a69fa5c0b8e035a01edaae61495dc271f01eeaf6aa4`
- DRAMATIC_SHAPE OverworldBattle.lua: `07e6d42dd55fa0e2abdf7e91ce57eceada8ceca76004fbb3ac5d125e9c1b11f2`
- DRAMATIC_SHAPE BattleScene.lua: `833c425a674bb6004e11863562d722e6d4bf8e629c79cee1ea86b945614ee8e1`
- Test ZIP SHA-256: `dc9afdee7290c06ef64e56aa251c18273b4f66e8782982e99f2cb7673a555a92`

## Google Drive authority

- Test folder ID: `1nnVtAtO58cyT3RSvYQfpXxZtyrxsKXgZ`
- Candidate ZIP ID: `15sejfAKBXz_qoPFkqFqI9dltzKk3aUAM`
- Static validation ID: `1egdCvbx2o_kCmagn8kM6zhj4s41hkrg7`
- PMD candidate source ID: `1pi8KbPmeQ9NHT2FlYpqa1rFPaOq_xtH2`
- DRAMATIC_SHAPE OverworldBattle candidate ID: `13-CKnxuzKYrKBaS9-txqVk4Uiqgmn-oY`
- DRAMATIC_SHAPE BattleScene candidate ID: `1bD6sYKGJN73Qgdj4wu0jUfTETYddULyk`

## Acceptance

Visual/runtime acceptance must verify:
- foreground trees/buildings naturally occlude intersecting PMD body regions;
- PMD remains visible when genuinely in front of geometry;
- player facing is correct, with no double mirror;
- size and feet anchor are natural;
- attack/hurt/status frames still update;
- no duplicate 3D-card + overlay body appears;
- Presentation Timeline/audio-tail behavior remains unchanged;
- no Lua error, ANR, or battle hang.

This candidate must not be promoted to a formal baseline until Thor visual acceptance and regression evidence pass.
