# PMD v0.1.97b × DRAMATIC_SHAPE 1.8.2 — Depth Integration II

Status: **TEST-ONLY / STATIC PASS / WAITING THOR VISUAL + RUNTIME ACCEPTANCE**

## Evidence-driven reason for this revision

v0.1.97a runtime evidence (`GEN1RECOMP_PMD_DEPTH_I_EVIDENCE_20260819_204630.zip`) matched the installed candidate SHA exactly, showed no new Lua error or ANR, and repeatedly logged `PMD_DEPTH_BRIDGE side=enemy` with zero player bridge markers.

This is explained by DRAMATIC_SHAPE `BACK SPRITES`: the enemy enters the 3D mon-card/depth path, while the player's visible body intentionally remains pinned in the classic 2D slot. The asymmetry caused the three Thor observations: enemy placement drifted from the approved pre-depth PMD presentation, enemy body lighting changed while player lighting did not, and only the enemy shadow followed the scene light.

## Final Integration II policy

1. **Enemy placement compatibility**
   - Preserve the pre-depth PMD anchor policy inside the 3D card instead of replacing it with the generic texture center.
   - Restore `ENEMY_Y_SHIFT`, non-bird giant bias, and the approved Articuno/Zapdos/Moltres shared anchor.
   - Use the previous staged shot's projected mark to compensate slow camera drift to within one frame while keeping the card on the correct world-depth plane.

2. **Visible body lighting parity**
   - Keep `BACK SPRITES`; do not force the visible player PMD into the 3D scene.
   - Apply DRAMATIC_SHAPE `shot.tint` to the visible pinned player PMD.
   - Visible Pokémon bodies on both sides use the same global day/night tint authority.
   - During the visible 3D mon-card pass only, local ShadowMap darkening and world fog are temporarily disabled. This prevents only the 3D enemy from becoming additionally dark/fogged while the player remains a pinned 2D body.
   - The world geometry itself remains fully lit/fogged as before.

3. **Dynamic ground shadows for both sides**
   - Render a hidden `playerShadow` PMD texture only for the DRAMATIC_SHAPE sun/shadow pass.
   - Feed that silhouette to `ShadowMap` at the real player arena cell.
   - Do not add it to visible `monCards`, so no duplicate player body appears.
   - Suppress the legacy PMD 2D player shadow while this 3D shadow owner is active.
   - Enemy and player ground shadows therefore both retain real light direction/strength behavior even though visible body coloring is kept symmetric.

4. **Unchanged authorities**
   - Presentation Timeline IIc, audio-tail, HIT timing, damage and accuracy are unchanged.
   - `BattleBillboard.lua` and `Voxel3D.lua` remain byte-exact.

## Source gate

v0.1.97b only installs over the exact v0.1.97a Depth I candidate:

- PMD `main.lua`: `8478d26620607ac0dee863090b2abeeffaa475d94b40a22400a8e6ad8997c065`
- PMD `manifest.json`: `1559de038a250661ed276a69fa5c0b8e035a01edaae61495dc271f01eeaf6aa4`
- DRAMATIC_SHAPE `OverworldBattle.lua`: `07e6d42dd55fa0e2abdf7e91ce57eceada8ceca76004fbb3ac5d125e9c1b11f2`
- DRAMATIC_SHAPE `BattleScene.lua`: `833c425a674bb6004e11863562d722e6d4bf8e629c79cee1ea86b945614ee8e1`
- DRAMATIC_SHAPE `BattleBillboard.lua`: `0ee39926a60de750f8e3ae8f9ae7d8c87d59d5e66136d13b8fe0a73c6bea0d42`

## Final candidate hashes

- PMD `main.lua`: `c500e45da02999fbff7a7c5525bd4882ce7285b7b660d4157e47d4525e66ae67`
- PMD `manifest.json`: `15a548312d690326b6945a60ab7a722c63868d1902a14048cd4dfb167d9d171f`
- DRAMATIC_SHAPE `OverworldBattle.lua`: `a2fe3642274f58340dd465bb33c201bb853fb02ea9d03eb49676cb2140b05742`
- DRAMATIC_SHAPE `BattleScene.lua`: `62daab3a679551ecd8871e464df6fddaf207070892d8f06dd528f98f5b2d91fb`
- DRAMATIC_SHAPE `BattleBillboard.lua` unchanged: `0ee39926a60de750f8e3ae8f9ae7d8c87d59d5e66136d13b8fe0a73c6bea0d42`
- Package ZIP: `933c3e480417e8c2e3d1662134faf1dd00903605bb41f0a9f39d608e28e16721`

## Drive authority

- Candidate folder ID: `1MJIinEMmxfE1QWnkYR3PPplxJzV8ut5Y`
- Candidate ZIP ID: `1szhYDqJ_rPACOsMy0CnXgLUghLGkRDn5`
- PMD candidate source ID: `1KvaCAFlYLrgBiGXvd7YVltWCwv2jz_ID`
- DRAMATIC_SHAPE OverworldBattle source ID: `1fH9HOpROS6KRYbRDYnyfi8TXKMjMvvZs`
- DRAMATIC_SHAPE BattleScene source ID: `1soVRBuW-bjTuZUYgDir5khfr2Qmg4SMk`
- Static Validation ID: `1o7QlR3vQwMdBnwaKGEdEOwUghWXCfdtZ`
- v0.1.97a Evidence ZIP ID: `1y8WTrRArC8UhPiG5Gs4g5pQEVwYoWQHd`
- v0.1.97a analysis ID: `1rSh9GIuoAAh0SBKKLqlYxlwSfnCzpVX5`

No promotion to baseline is allowed before Thor visual/runtime acceptance.