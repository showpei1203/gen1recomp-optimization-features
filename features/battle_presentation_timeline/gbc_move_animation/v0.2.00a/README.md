# GBC Colored Move Animation Layer I — GBC-A1 v0.2.00a

Status: **TEST-only candidate / Thor runtime + visual evidence pending**
Date: 2026-08-20

## Formal base
- pmd_idle_battle_sprites v0.1.99b — PMD Action Binding Authority I / Formal PASS
- HIT_FRAME Authority I — engine `applyHitFx` is sole authoritative HIT owner
- Presentation Timeline Authority
- DRAMATIC_SHAPE 1.8.2 × thor_battle_ui 0.3.41 sealed compatibility baseline
- Depth/Occlusion and Large Pokémon Presentation Bounds remain sealed

## Candidate scope
A1 adds an **additive colored GBC-derived VFX layer** for three benchmark moves:
- Ember — projectile
- Thundershock — sustained/electric
- Thunder Wave — non-damage status

The existing native move animation intentionally remains visible in A1. The colored layer is being validated as a presentation consumer before any supported-move native-visual replacement policy is attempted.

Authority chain remains:
`Presentation Timeline → HIT_FRAME → PMD Action Binding → GBC Colored Move Animation`.

The GBC layer never owns damage, HIT, queue barriers, SFX/audio-tail lifetime, PMD body timing, depth, or species scale.

## Runtime implementation
- `Volatile.gbc` namespace keeps state outside the already-near-limit outer Lua local scope.
- Source/color data lives in `gbc_anim_data.lua` so later move expansion does not require growing the monolithic runtime table.
- A fail-open `pcall` boundary disables only the colored layer on a GBC-specific runtime error; sealed native presentation continues.
- Event adapters consume Action Binding START / HANDOFF / NATIVE_RELEASE / ANIM_RELEASE / HIT / COMPLETE.
- GBC HIT comes only from the existing Action Binding HIT callback.
- Player/enemy target anchors use recent PMD screen-space presentation centers. Depth-owned enemy fallback uses the sealed presentation composition, not physical-feet coordinates.
- Colored VFX draw above PMD bodies and before existing native `battle.drawAnimLayer`.

## A1 visual behavior
- Ember: three red/orange 8px GBC fire objects travel attacker→target, then burst at authoritative HIT.
- Thundershock: gray core + yellow lightning objects surround the target through the sustained presentation.
- Thunder Wave: yellow expanding/pulsing lightning ring; no damage HIT is synthesized.

## Static validation
**40/40 PASS**, including real Lua 5.4 parser loads for `main.lua` and `gbc_anim_data.lua`.

Sealed functions verified byte-exact against formal v0.1.99b:
- `moveActionForQueue`
- `moveTimingException`
- `motionSyncTiming`
- `armNativeActionSync`
- `fireHitFrameAuthority`
- `combatMotionPose`
- `applyHitFx` wrapper

## Candidate hashes
- main.lua `c1bf20622ed96210b7308173100adae7f3aa2449b4bb6bbd813443858e453127`
- manifest.json `89dfa55edff7d2a297da9cbc0505c0216f9f2bd825731a4496b92985cc8e45d4`
- gbc_anim_data.lua `b71ba2c58796eb76e33e9c33654833d7ed66f2471f99420d7f3f8358330a31f5`
- fire_red.png `7b279edf5a907c278d18bccfe1f6661f3ead56b7264fde4bcfe57a0999798a93`
- lightning_yellow.png `78949d8afed6f5962be7425a593246e07ea7525ce043e35e758a4dcf9bb89d2f`
- explosion_gray.png `73bea1826f82eb9bcbe66cd2675195e55e6a922808b16b66cc3b115242a5a718`
- complete TEST ZIP `3602e4ef5b31b84af8dfe59b52f51b0288eb65d90fae048cd7290b3e81a6f672`

Drive test folder: `1knDZ2v0WFAxsbrUNtZ_OsDc9dztDdztG`
Drive complete TEST ZIP: `1ZZhhLwg-2DvmaB2707ztg1g-1h9o-4Fj`

## Thor gate
Use Ember, Thundershock and Thunder Wave at least once each and let each presentation finish. Collector requires the supported GBC event chains and sealed HIT_FRAME hard gates to remain healthy. Runtime PASS and visual acceptance remain separate. Native-animation duplication is expected in A1 and is not by itself a failure.