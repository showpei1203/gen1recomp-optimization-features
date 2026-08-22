# PMD v0.2.06b StadiumBattleFX Exclusive VFX Integration I TEST

Status: TEST-only / static PASS / Thor runtime+visual pending. Formal Authority remains exact v0.2.04a.

## Runtime policy
- StadiumBattleFX is the exclusive move-VFX provider.
- PMD legacy custom move-VFX renderer, lifecycle, assets, data and target-anchor state are physically absent.
- Installed `main.lua` and `manifest.json` must contain zero case-insensitive `gbc` token matches.
- `gbc_anim_data.lua` and `assets/gbc_anim` must not exist after install.
- Accepted body semantics remain: Psybeam non-contact beam_release; Tackle safe body; Bubble/Bubblebeam projectile; Scratch same-pose handoff hold.
- HIT_FRAME / Action Binding / DRAMATIC_SHAPE 1.8.2 / THOR Battle UI 0.3.41 remain sealed.

## StadiumBattleFX gate
- Recursive manifest scan up to depth 5.
- Match by `id=STADIUM_BATTLE_FX` OR `name=StadiumBattleFX`.
- Accepted release strings for this slice: `2.1.8` or `2.1.8.1`.

## Hashes
- main `fc6709935d4c58f31c9d7eacad68bc13cfc8af5f523604f05b022178cf4ad14b`
- manifest `84e9b98e41333fda429c566d53dc6a835bf4b82eee31a7acff4767b9ece3c2bf`
- package `db07b1f0fc94e9d001a9da1e230bb4919568f1c7cfd521cea45f09a7345dd338`

## Static
18 PASS / 0 FAIL. Lua parser PASS. ZIP integrity PASS.

## Thor benchmark
Quick Attack / Ember / Fury Swipes / Surf in one TEST-only B fixture.

Drive candidate: `1KfUT6_qOYS6NulvP3V_s6IsdSR3n84Bd`.
