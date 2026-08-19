# PMD v0.1.97f × DRAMATIC_SHAPE 1.8.2

## Presentation Overflow / Depth Integration

**Status:** Runtime PASS + Visual Acceptance PASS on Thor.

### Accepted behavior

- enemy PMD position restored to approved pre-depth composition;
- enemy feet complete;
- tree/building occlusion remains owned by DRAMATIC_SHAPE/Voxel3D depth;
- enemy dynamic lighting/shadow behavior remains correct;
- player visible PMD remains in legacy overlay under BACK SPRITES;
- player hidden silhouette enters DRAMATIC_SHAPE sun/shadow pass;
- `thor_battle_ui` forwards `sideTexture(..., opts)` correctly;
- Timeline IIc / audio-tail / HIT=`ANIM_RELEASE` remains intact.

### Accepted hashes

- Candidate ZIP: `8492bc002c1eb7707c5b232dc1b3029eac98fcc4c0df7b9157ebff1981ee94b2`
- PMD `main.lua`: `a4870ddea71c5679917275a8444d6451405a0634758767e9f8487d1e0180ca49`
- PMD `manifest.json`: `87d9caf6d33d1082c86fa3804422827bb0f5e8437825e14be409c98240015051`
- DRAMATIC_SHAPE `lib/OverworldBattle.lua`: `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DRAMATIC_SHAPE `lib/BattleScene.lua`: `bca552070e26c9ac6554f8cc387ffb34036a76722b7be9c5d3184974237873cc`
- `thor_battle_ui/main.lua`: `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`
- Acceptance Evidence ZIP: `2bfd0fbc5e01ff41a27943107c763565ce1698fa2fba1acda9cd3f54e275ad88`

### Root causes resolved

1. `thor_battle_ui 0.3.41` dropped the third `opts` argument when wrapping `OverworldBattle.sideTexture`, converting player shadow-only capture into visible 3D ownership.
2. `bridgeAnchor` lived inside a `pcall` closure and was lost before card-anchor construction, causing fallback to `TEX_AY=96`.
3. v0.1.97e used the physical feet anchor as the visible presentation anchor. That fixed clipping but cancelled legacy `ENEMY_Y_SHIFT`, moving the enemy upward.
4. v0.1.97f separates presentation and physical anchors and uses a narrow camera-ray depth-bias overflow pass to preserve both approved position and full feet.

### Compatibility authority

See `docs/PMD_DRAMATIC_SHAPE_DEPTH_INTEGRATION_AUTHORITY.md`.

Large Pokémon must continue to follow the original v0.1.95c Expanded Battle Presentation Bounds. Do not shrink or reposition large species merely to satisfy a nominal 3D card boundary.
