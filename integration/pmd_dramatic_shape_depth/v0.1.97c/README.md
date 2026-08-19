# PMD v0.1.97c × DRAMATIC_SHAPE 1.8.2 — Depth Integration III

Status: **TEST-ONLY / STATIC PASS / WAITING THOR VISUAL + RUNTIME ACCEPTANCE**

## Why v0.1.97b failed visually

Thor evidence `GEN1RECOMP_PMD_DEPTH_II_EVIDENCE_20260819_211222.zip` matches the exact v0.1.97b installed SHA set and shows no new candidate Lua crash or ANR. The visual result still failed:

- player PMD body was completely invisible;
- enemy PMD feet were partially cut by the ground/depth plane.

The trace resolves both causes:

- `PMD_DEPTH_BRIDGE side=player` occurred 3 times;
- `PMD_DEPTH_SHADOW side=player` occurred 0 times.

So v0.1.97b did **not** keep the player shadow-only under the current Thor setting. The normal player 3D bridge ran, meaning the visible player body left the proven legacy overlay slot.

For the enemy, Integration II preserved the old PMD pixel position inside the 160×144 canvas, including `ENEMY_Y_SHIFT`, but DRAMATIC_SHAPE still returned fixed card anchor `TEX_AY=96`. The body baseline and world-ground anchor no longer matched, so lower pixels could sit below the terrain plane and be depth-clipped.

## v0.1.97c policy

1. **Player visible body is always legacy overlay for PMD**
   - PMD presence, not `BACK SPRITES`, decides this policy.
   - Visible player PMD stays in the approved v0.1.96c slot.
   - Player still receives DRAMATIC_SHAPE day/night tint.
   - A hidden `playerShadow` PMD silhouette still enters the real moving-sun ShadowMap.
   - The player never creates a visible 3D PMD card in this candidate.

2. **Enemy 3D card uses the actual PMD feet anchor**
   - PMD `drawOne` reports the real `ax/ay` used inside the side canvas.
   - DRAMATIC_SHAPE `sideTexture` uses that returned anchor in `monMatrix`.
   - This keeps `ENEMY_Y_SHIFT` and legacy PMD placement while aligning the actual feet baseline to world ground, instead of treating the fixed `TEX_AY=96` as the feet after PMD has moved the pixels.

3. **Minimal scope**
   - Changed: PMD `main.lua`, PMD manifest, DRAMATIC_SHAPE `OverworldBattle.lua`.
   - Unchanged byte-exact from v0.1.97b: `BattleScene.lua`.
   - Also unchanged: `BattleBillboard.lua`, `Voxel3D.lua`, Presentation Timeline IIc, audio-tail, HIT timing, damage and accuracy.

## Source gate: exact v0.1.97b

- PMD `main.lua`: `c500e45da02999fbff7a7c5525bd4882ce7285b7b660d4157e47d4525e66ae67`
- PMD `manifest.json`: `15a548312d690326b6945a60ab7a722c63868d1902a14048cd4dfb167d9d171f`
- DS `OverworldBattle.lua`: `a2fe3642274f58340dd465bb33c201bb853fb02ea9d03eb49676cb2140b05742`
- DS `BattleScene.lua`: `62daab3a679551ecd8871e464df6fddaf207070892d8f06dd528f98f5b2d91fb`
- DS `BattleBillboard.lua`: `0ee39926a60de750f8e3ae8f9ae7d8c87d59d5e66136d13b8fe0a73c6bea0d42`

## Candidate hashes

- PMD `main.lua`: `1dbfdabafd2041908f1834892aa0fe0e7a2bf7af46b8c686d270abf0a0908ee9`
- PMD `manifest.json`: `00da33c1c42ebb014ca0accc778e0a672e4082aeed509201b968d16d8d56a78c`
- DS `OverworldBattle.lua`: `396959a577e8cc84198fa66fca11767ac9e6c313edcf0107d0b6fc0b2f79bb4e`
- DS `BattleScene.lua`: unchanged `62daab3a679551ecd8871e464df6fddaf207070892d8f06dd528f98f5b2d91fb`
- Package ZIP: `48f29237a5d01dcc876375731ed306d5908da80fedaa3a3dfd362896a766f88a`

## Evidence / Drive authority

v0.1.97b visual-fail evidence:
- Evidence ZIP SHA-256: `48c725f9b4d1382a6e45aaa973a9759b97b72ed7d0c6d015d804232460b6e329`
- Evidence ZIP Drive ID: `1TG5g3U_gyjCWZoYWz44_Q_EwdThx70EL`
- Analysis Drive ID: `1osJ8SFMe4mVlc2u2ToNxhh2t6CXG2SI6`

v0.1.97c candidate:
- Folder ID: `1MTSK9n3ODArGu2lwV2EpAqLODZ9D8pzb`
- ZIP ID: `1pqEVIlnwYHarAB1QQVW54RmMTUegF8dV`
- PMD source ID: `1YkhoMQBcaOBEo4GEZpGwSGOY0sTbuZM4`
- DS OverworldBattle source ID: `1l0vvLB3aOnJMjZTcTxxgrO4MAMNODeyY`
- Static Validation ID: `16MnD2QcuYf_Mbua76gluS2LoY7UzO5U5`

No promotion to baseline before Thor visual/runtime acceptance.