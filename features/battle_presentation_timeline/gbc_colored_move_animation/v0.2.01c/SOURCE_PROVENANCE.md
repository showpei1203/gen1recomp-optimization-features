# v0.2.01c Source Provenance

Primary reference: `pret/pokecrystal` master.

## Behavior sources
- `data/moves/animations.asm`: BattleAnim_Surf, BattleAnim_QuickAttack, BattleAnim_FurySwipes, BattleAnim_Psybeam.
- `engine/battle_anims/bg_effects.asm`: BattleBGEffect_Surf and Surf wave initialization/rotation.
- `engine/battle_anims/functions.asm`: BattleAnimFunc_Surf and animation functions.
- `data/battle_anims/objects.asm`
- `data/battle_anims/framesets.asm`
- `data/battle_anims/oam.asm`: BATTLE_ANIM_OAMSET_22, base tile `$09`, 22-sprite Surf crest.

## Graphics sources
- `gfx/battle_anims/bubble.png`
  - git blob `b6febb0a8ba6be73ee396c958e874051fe3dcea6`
  - source PNG SHA-256 `236637192644459decd2a8e9a55778d36a74199c725a2f4df2a0c62895b8b37b`
  - derived runtime asset `bubble_blue.png`
- `gfx/battle_anims/speed.png`
  - git blob `e219b38c9f1dcb8907373cfe50bdb7d7438effb9`
  - source PNG SHA-256 `19478e5632d2db572be364b363dcfa08f9ea941ce6153f063352a5200bc59c3b`
  - derived runtime asset `speed_gold.png`

Existing A1/A2 derived assets remain sourced from Crystal fire/lightning/explosion/hit/cut/psychic/wave graphics as recorded in gbc_anim_data.lua.

The derived PNGs use transparency + a small fixed colored palette and nearest-neighbor rendering. They are not screenshots/video captures. Runtime movement/composition is reconstructed from Crystal's script/object/BG-effect behavior and mapped onto Gen1recomp's sealed presentation events.
