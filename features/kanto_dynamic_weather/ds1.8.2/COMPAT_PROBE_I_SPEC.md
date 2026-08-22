# Kanto Dynamic Weather × Dramatic Shape 1.8.2 — Compatibility Probe I

Upstream: Kanto Dynamic Weather 1.0.3 (MIT).
Target: exact Gen1recomp project Dramatic Shape 1.8.2 Authority.

## Safety model

This candidate does not patch Dramatic Shape files on disk. It changes only the Kanto Dynamic Weather dependency gate from `DRAMATIC_SHAPE@>=1.7.2 <1.8.0` to `DRAMATIC_SHAPE@>=1.8.2 <1.8.3`, then deliberately reuses KDW's existing verified in-memory compatibility bridge.

The upstream bridge applies Sky/Voxel3D/VoxelScene hunks by source anchors and fails closed on mismatch. Therefore Compat Probe I answers whether the existing bridge already survives the 1.8.2 renderer line without pretending that changing the version string itself proves compatibility.

## Exact-source precheck

Against the project's captured DS1.8.2 Authority source:

- Voxel3D SHA-256 `923f0b827ce6f8834d1fa763861b96e1338a9f3ddfdb4ead78cd9eb688b9bc4f`
- VoxelScene SHA-256 `d273b3f94b6e0822710d4ce02b830762a46399f2a4385ab1b96919c25781b7ec`
- 12 inspected Voxel3D/VoxelScene compatibility anchors: PASS
- Sky: left to the upstream bridge's runtime source-anchor validator; mismatch must fail closed.

A TEST-only read-only companion probe logs whether DS and KDW loaded and what KDW exports as its compatibility state.

## Result gate

Thor PASS requires KDW detected on DS1.8.2, zero KDW compatibility errors, zero current Lua/FATAL/ANR errors, exact Voxel3D/VoxelScene hashes unchanged, and normal outdoor 3D weather rendering.

If a hunk fails, the next candidate changes only the explicitly failed compatibility hunk. The sealed DS1.8.2 source must not be modified.
