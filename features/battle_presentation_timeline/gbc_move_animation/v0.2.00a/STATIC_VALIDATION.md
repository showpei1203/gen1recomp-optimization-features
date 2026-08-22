# GBC-A1 v0.2.00a Static Validation

Result: **40/40 PASS**

- Lua 5.4 parser: `main.lua` PASS
- Lua 5.4 parser: `gbc_anim_data.lua` PASS
- Formal v0.1.99b base main hash PASS
- Formal v0.1.99b base manifest hash PASS
- manifest version = 0.2.00a
- Ember / Thundershock / Thunder Wave definitions present
- GBC layer additive before native `drawAnimLayer`
- native `drawAnimLayer` retained
- GBC subsystem fail-open `pcall`
- no standalone GBC timing authority
- GBC HIT consumes existing Action Binding HIT
- status GBC does not synthesize HIT
- presentation/physical anchor separation retained
- anchor cache only on legacy PMD draw
- derived fire/lightning/explosion assets exist, have expected dimensions and transparency
- pret source hashes verified
- `moveActionForQueue` byte-exact
- `moveTimingException` byte-exact
- `motionSyncTiming` byte-exact
- `armNativeActionSync` byte-exact
- `fireHitFrameAuthority` byte-exact
- `combatMotionPose` byte-exact
- `applyHitFx` wrapper byte-exact
- BATTLE_SCALE remains 0.90
- PLAYER_Y_SHIFT remains 6
- ENEMY_Y_SHIFT remains 10
- no DRAMATIC_SHAPE file in patch
- no THOR file in patch

Runtime scope: additive colored GBC layer only; native battle animation retained.
Thor runtime + visual evidence is still required before promotion.

Candidate hashes:
- main.lua `c1bf20622ed96210b7308173100adae7f3aa2449b4bb6bbd813443858e453127`
- manifest.json `89dfa55edff7d2a297da9cbc0505c0216f9f2bd825731a4496b92985cc8e45d4`
- gbc_anim_data.lua `b71ba2c58796eb76e33e9c33654833d7ed66f2471f99420d7f3f8358330a31f5`
- fire_red.png `7b279edf5a907c278d18bccfe1f6661f3ead56b7264fde4bcfe57a0999798a93`
- lightning_yellow.png `78949d8afed6f5962be7425a593246e07ea7525ce043e35e758a4dcf9bb89d2f`
- explosion_gray.png `73bea1826f82eb9bcbe66cd2675195e55e6a922808b16b66cc3b115242a5a718`
- complete TEST ZIP `3602e4ef5b31b84af8dfe59b52f51b0288eb65d90fae048cd7290b3e81a6f672`
