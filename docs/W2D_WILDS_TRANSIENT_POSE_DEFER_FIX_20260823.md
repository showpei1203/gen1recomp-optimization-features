# W2D Wilds Transient Pose Defer Fix

Date: 2026-08-23
Runtime acceptance: 2026-08-24

## Accepted W2C visual state

User visually confirmed:
- flying Pokemon animation: PASS
- Voxel Characters thickness: PASS
- Wilds Sprite Style live switching: PASS

## Root cause

W2C evidence contained 47 occurrences of:

`pose() returned nil sprite -> spatial overlay emergency`

The failures cluster immediately after normal Wilds spawns. Wilds 2.1.0 currently calls `VoxelAdapter:updateEntity()` before `SpawnFx.updateEntity()` in `behavior_tick.lua`. Grass spawn FX intentionally keeps the body hidden for about 0.10 s and water spawn FX for about 0.18 s. The Voxel adapter therefore probes an expected transient hidden body and incorrectly classifies it as a permanent world-billboard failure.

This is a presentation-order bug, not bad sprite data and not a Voxel Characters mesh failure.

## W2D delta

Only `overworld_wild_spawns/lib/voxel_adapter.lua` changes.

- Original SHA-256: `ba964fba075667ba66dabb01e4db1adb54aca7d9fc8a90b9e8a3b1403585bf9b`
- W2D SHA-256: `767868dc2beadb9516cdb18ebf4416494a3c8969aa9b163f6964e79796a7b838`

Behavior:
- if `SpawnFx.bodyVisible(entity) == false`, Voxel registration is deferred instead of falling back;
- once the spawn body becomes visible, the normal bind/pose probe resumes;
- a defensive `probePose` guard treats a nil pose caused by the same hidden-body window as transient;
- genuine pose failures still use the existing emergency fallback.

No changes to Wilds encounter logic, save format, True Size, Sprite Style provider selection, Wild Skies W2C, Voxel Characters, Dramatic Shape, Weather, PMD, or StadiumBattleFX.

## Runtime acceptance

Evidence: `GEN1RECOMP_W2D_POSE_DEFER_EVIDENCE_20260824_062448.zip`

Collector result: `PASS`

Observed:
- `WILD_SPAWN_ROWS=18`
- `W2D_DEFER_ROWS=15`
- `W2D_RESUME_ROWS=15`
- `POSE_NIL_ROWS=0`
- `SPATIAL_OVERLAY_EMERGENCY_ROWS=0`
- `W2C_SKY_BIND_ROWS=4`
- `RUNTIME_ERROR_ROWS=0`
- `W2D_ADAPTER_EXACT_HASH=True`

The defer/resume pair was seen repeatedly across normal spawns, while the previous nil-pose and emergency-overlay warnings were fully eliminated during the same run. Wild Skies W2C continued binding flyers in the same session.

## Accepted integration hashes

- Wilds `main.lua`: `cc5da502de2d240b03c879f58a4ef2754db94cdc854e517a304a2868c54c7625`
- Wilds W2D `lib/voxel_adapter.lua`: `767868dc2beadb9516cdb18ebf4416494a3c8969aa9b163f6964e79796a7b838`
- Wild Skies W2C `main.lua`: `7509b0d494eabfc52ad6a1cd049128a07d6bdc3e24534e110342506f492beb61`

## Formal status

**W2C + W2D = RUNTIME + VISUAL PASS.**

The former Wilds transient `pose() returned nil sprite -> spatial overlay emergency` issue is closed for this accepted stack.

Remaining work is ordinary long-session soak/regression only. Do not reopen the PMD Sky bridge path or alter the accepted Wilds art-authority design without new evidence.

## Test build

Drive file ID: `1LDPpUx8u0qZ2gj9t945FNo3ODObdx0j9`

Package SHA-256: `cdec12376177e3e90a75fe271501eb8e0c5e1fdf9555b78223d497e21ae59ba9`
