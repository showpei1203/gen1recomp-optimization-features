# PMD × DRAMATIC_SHAPE Depth Integration Authority

**Authority date:** 2026-08-19  
**Accepted compatibility candidate:** `pmd_idle_battle_sprites v0.1.97f` × `DRAMATIC_SHAPE 1.8.2` × `thor_battle_ui 0.3.41`  
**Status:** Runtime PASS + user visual acceptance PASS for the tested depth-integration path.

## 1. Presentation and physical authority are separate

A PMD sprite's approved battle-screen composition is not necessarily identical to its physical world-ground point.

Never use one anchor to own both:

- **Presentation Authority**: where the Pokémon should appear on the battle screen.
- **Physical Feet Authority**: where the Pokémon physically meets the 3D ground and where its shadow is grounded.

The v0.1.97b/c/e failures came from conflating these responsibilities.

For visible enemy PMD under DRAMATIC_SHAPE:

- keep DRAMATIC_SHAPE's stock visible-card presentation anchor;
- preserve PMD's legacy offsets inside the texture;
- keep the PMD-returned physical feet anchor separately for shadow/ground semantics.

## 2. Presentation Overflow Authority

If an approved PMD composition intentionally extends below DRAMATIC_SHAPE's nominal ground presentation line, do **not** move or shrink the whole Pokémon.

Use a narrow presentation-overflow depth pass for only the affected texture band:

1. main body keeps normal DRAMATIC_SHAPE depth semantics;
2. only the intentional lower overflow band receives stronger depth bias;
3. depth bias follows the camera ray so screen projection remains unchanged;
4. tree/building occlusion for the rest of the body remains normal.

This is the 3D continuation of `v0.1.95c Expanded Battle Presentation Bounds`.

## 3. Large Pokémon presentation bounds are sealed compatibility invariants

Future PMD render integration must preserve the approved v0.1.95c large-species policy:

- `BATTLE_SCALE = 0.90`
- `PLAYER_Y_SHIFT = 6`
- `ENEMY_Y_SHIFT = 10`
- enemy giant classification includes normal-scale frame width or height `>= 90`
- giant enemies do not enter the conservative fit/shrink path
- giant enemies preserve native presentation scale and may overflow physical top/side screen bounds
- non-bird giants retain the legacy presentation bias `+6 X / -4 Y` in the 160×144 path
- Articuno / Zapdos / Moltres are one presentation family and retain their shared approved anchor
- never normalize Onix/Gyarados-class large enemies merely because the renderer has a smaller nominal card envelope
- clipping fixes must expand presentation/depth allowance, not silently move or shrink the Pokémon

Before any future PMD render/depth refactor is promoted, run dedicated visual regression using representative categories:

- ordinary small/medium enemy
- large non-bird enemy such as Onix/Gyarados class
- legendary bird family
- large action/motion frame larger than idle
- foreground occluder crossing the Pokémon
- day/night lighting and dynamic shadow

## 4. Player BACK SPRITES policy

Under DRAMATIC_SHAPE BACK SPRITES:

- visible player PMD remains in the approved legacy overlay position;
- only a hidden PMD silhouette enters the 3D sun/shadow pass;
- visible player body keeps the agreed scene tint policy;
- 3D shadow ownership must never set visible `depthPlayer=true`.

Expected healthy state after send-out:

```text
depthPlayer=false
shadowPlayer=true
playerCanDraw=true
overlayWillDraw=true
```

## 5. Compatibility wrapper rule

Any wrapper around a foreign function must preserve its complete semantic signature.

Concrete failure discovered here: `thor_battle_ui 0.3.41` wrapped `OverworldBattle.sideTexture(battle, side, opts)` as `sideTexture(battle, side)`, dropping `opts`. That converted `{pmdOnly=true, shadowOnly=true}` into a visible player 3D request and suppressed the player PMD body.

**Rule:** wrapper/proxy/hook code must forward all semantic arguments unless the contract explicitly says otherwise. Argument forwarding is part of Authority, not an implementation detail.

## 6. Lua scope rule for cross-stage render metadata

Render metadata produced inside `pcall(function() ... end)` must be declared in a scope that survives until the caller consumes it.

Concrete failure discovered here:

- PMD returned enemy physical feet `ay=106`;
- `bridgeAnchor` was local inside the `pcall` closure;
- the outer return path saw no anchor and fell back to `TEX_AY=96`;
- part of the sprite was placed below the world floor and correctly clipped by depth.

**Rule:** values crossing render stages must have explicit lifetime/ownership. Do not rely on same-name locals across closures.

## 7. Evidence-backed accepted v0.1.97f behavior

Observed on Route 2:

- `playerGround=0`
- `enemyGround=0`
- `chosenGroundY=0`
- enemy presentation anchor `(80,96)`
- enemy physical anchor `(80,106)`
- overflow `10 px`
- camera-ray overflow pass active
- `screenDrift=0`
- no forbidden player-visible `sideTexture` request
- player shadow-only bridge active
- player visible overlay active after send-out
- no new Lua error / FATAL EXCEPTION / application ANR
- Timeline HIT remains aligned to `ANIM_RELEASE`

## 8. Do-not-regress checklist

Never solve PMD × 3D clipping by:

- moving the entire enemy upward;
- shrinking large Pokémon into a generic safe box;
- collapsing presentation and physical anchors;
- turning the player visible body into a 3D card under BACK SPRITES without explicit approval;
- dropping hook/wrapper arguments;
- bypassing DRAMATIC_SHAPE depth with a late full-body overlay for enemies;
- modifying Timeline/audio/HIT behavior as collateral damage during render fixes.

This document is the compatibility authority for future PMD × DRAMATIC_SHAPE render/depth work.
