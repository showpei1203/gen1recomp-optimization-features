# GBC-A1 Source Manifest

Primary technical reference: `pret/pokecrystal` master, consulted 2026-08-20.

## Runtime-derived graphics
- `gfx/battle_anims/fire.png`
  - Git blob `19f01141b29f7d02004f534fa810d685667578a1`
  - source SHA-256 `e25b50de5594655874db8e3752201c0d86898a229d62dd42e5329c62401a569d`
  - derived runtime asset `fire_red.png`
- `gfx/battle_anims/lightning.png`
  - Git blob `11ec99793fd1efd1f78840c88e2f4dffcb3ac939`
  - source SHA-256 `c949c8be5d00a161c399510596fa4d1d9157de77f6afa8d71f622ffc2276b4ed`
  - derived runtime asset `lightning_yellow.png`
- `gfx/battle_anims/explosion.png`
  - Git blob `0af9f1a0d98cf10396c24c3de4e014e7842400aa`
  - source SHA-256 `01e60d7244bb925819dca6c8d2c8034c9a7f7185fc09e55464eb23ecc9a44d15`
  - derived runtime asset `explosion_gray.png`

Palette source:
- `gfx/battle_anims/battle_anims.pal`
- Git blob `d2ebb6cefeb4bcedfc8cd5c97724bdfd2198997c`

A1 palette mapping treats Crystal OAM white/index-0 as transparent, then maps the remaining grayscale indices into the original red/yellow/gray palette families.

## Behavior references
- `data/moves/animations.asm`
  - `BattleAnim_Ember`
  - `BattleAnim_Thundershock`
  - `BattleAnim_ThunderWave`
- `data/battle_anims/objects.asm`
  - Ember red/fire object
  - Thundershock yellow/lightning + gray core objects
  - Thunder Wave yellow/lightning object
- `data/battle_anims/framesets.asm`
  - Ember frameset OAMSET 0F/10
  - Thunder Wave OAMSET 3E/3F/40
  - Thundershock sparks OAMSET 46/47; core OAMSET 18
- `data/battle_anims/oam.asm`
  - tile offsets/compositions used to select source tiles for the A1 runtime scaffold

## Interpretation policy
A1 is an event-binding scaffold, not yet a byte-exact interpreter of every Crystal animation command. It preserves Crystal palette/object identity and characteristic behavior while binding the resulting colored VFX to the already-sealed Gen1recomp presentation events.

Native animation remains visible during A1. Exact command/OAM interpretation and supported-move native-visual replacement are later gates.

Drive copy of detailed provenance: `1BmLb3w36dcKDMH7n2MQskCwk82ZgOOkt`.