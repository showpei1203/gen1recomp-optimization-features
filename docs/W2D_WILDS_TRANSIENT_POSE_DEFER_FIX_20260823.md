# W2D Wilds Transient Pose Defer Fix

Date: 2026-08-23

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

Collector gates:
- at least 3 normal Wilds spawns;
- at least 1 `GEN1RECOMP_W2D_VOXEL_DEFER`;
- at least 1 `GEN1RECOMP_W2D_VOXEL_RESUME`;
- `POSE_NIL_ROWS=0`;
- `SPATIAL_OVERLAY_EMERGENCY_ROWS=0`;
- `RUNTIME_ERROR_ROWS=0`.

## Test build

Drive file ID: `1LDPpUx8u0qZ2gj9t945FNo3ODObdx0j9`

Package SHA-256: `cdec12376177e3e90a75fe271501eb8e0c5e1fdf9555b78223d497e21ae59ba9`
