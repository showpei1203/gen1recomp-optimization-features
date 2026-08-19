# PMD Large Pokémon Presentation Bounds Authority

**Authority source:** accepted `pmd_idle_battle_sprites v0.1.95c` presentation policy, preserved through accepted v0.1.97f depth integration.

## Sealed invariants

- `BATTLE_SCALE = 0.90`
- `PLAYER_Y_SHIFT = 6`
- `ENEMY_Y_SHIFT = 10`
- an enemy is treated as a giant presentation frame when its normal-scale width or height is `>= 90 px`
- giant enemies must not enter the conservative fit/shrink path
- preserve native presentation scale whenever practical
- allow intentional top/side overflow rather than forcing the Pokémon inside a generic safe box
- non-bird giants retain the legacy `+6 X / -4 Y` presentation bias in the 160×144 path
- Articuno / Zapdos / Moltres remain one presentation family with their shared approved anchor
- a motion/action frame that becomes larger than idle inherits the same presentation-bounds philosophy

## 3D integration rule

Large Pokémon clipping under DRAMATIC_SHAPE must be solved by expanding the presentation/depth envelope, not by:

- shrinking the whole Pokémon;
- moving the whole Pokémon upward;
- cancelling legacy PMD offsets;
- replacing per-family anchors with one generic 3D card fit.

v0.1.97f demonstrates the approved pattern: keep visible Presentation Authority separate from Physical Feet Authority, and use screen-stable camera-ray depth bias only for the intentional presentation-overflow region.

## Mandatory regression set

Any future PMD render/depth refactor must visually validate at least:

1. ordinary small/medium enemy;
2. large non-bird enemy such as Onix/Gyarados class;
3. Articuno/Zapdos/Moltres family;
4. action/motion frame larger than idle;
5. foreground tree/building crossing the Pokémon;
6. day/night lighting and dynamic shadow.

A candidate that improves ordinary sprites but shrinks, repositions, clips, or misanchors large species is a visual regression and must not be promoted.
