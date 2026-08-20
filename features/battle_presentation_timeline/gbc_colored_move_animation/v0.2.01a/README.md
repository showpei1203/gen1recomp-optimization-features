# PMD v0.2.01a — GBC-A2 One-Shot B Fixture TEST

Status: **TEST-only candidate**. Runtime/visual acceptance is pending Thor evidence.

## Scope

v0.2.01a builds on exact v0.2.00b and adds Crystal-derived colored VFX for:

- QUICK ATTACK — contact / authoritative-HIT impact
- FURY SWIPES — multi-hit / alternating slash
- PSYBEAM — travelling beam/wave
- SURF — battlefield area wave

A TEST-only free-overworld **B** hook starts one isolated benchmark battle per process. The fixture uses a battle-local clone and does not write player moveset, HP/status, `mod.save`, or `save.modData`. The second free-overworld B press after the fixture must prove the one-shot guard.

## Formal promotion hard gate

The complete `GBC_A2_FIXTURE` block, B input hook, fixture state and fixture logging **must be deleted before formal release**.

## Candidate SHA-256

- `main.lua`: `698deb2ea8ade820b6f2c0d96e006ebbd2bb44d6f8977f5d3272b18e880e9ee5`
- `manifest.json`: `09e7ce55e2adf2cb6bf3b2639958fdca1da51797766ee95da2744ae09f4874b8`
- `gbc_anim_data.lua`: `b19b65d930a88e238ebdc3d1b1bab2b499c827296705a804d5529eb49a6b681e`
- `hit_gold.png`: `d5d7c5c5ad7fc8866833b38c81497e95daea227484fa49c4ab688580ce42d213`
- `cut_red.png`: `f8cd3d0ee9a0f7fbd7803fd934edd2f06c728f261e0ac2b7fe8d16cf655de92d`
- `psychic_purple.png`: `57648323176c2fd767b1ab37a39df1f2d7547aeb13a0d2c02add39f99d4de4c9`
- `wave_blue.png`: `8956a225b0f9e93bf5aad41779b4704017c93c1fa94ddb7a2408ccdc9629f6bb`

A1 assets remain byte-exact from v0.2.00b.

Complete TEST ZIP: `GEN1RECOMP_PMD_v0.2.01a_GBC_A2_ONE_SHOT_B_FIXTURE_TEST_20260821.zip`
ZIP SHA-256: `a66ba76e18cedbd3454a29ae08c424ae9b1c6c48c07ee03ddf8fc37450cf3515`

## Static result

**45 PASS / 0 FAIL**.

Sealed HIT_FRAME, Action Binding HIT/COMPLETE, and A1 Ember/Thundershock/Thunder Wave draw-function bodies remain byte-exact against v0.2.00b.
