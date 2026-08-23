# Gen1recomp Weather Integration W1c — Shared Renderer Identity Repair

Date: 2026-08-23

## Context

W1/W1b successfully installed Kanto Dynamic Weather 1.0.3 against the Thor exact Dramatic Shape 1.8.2 renderer, but runtime visual acceptance exposed two regressions and one tooling failure:

1. Tall/3D tree leaf crowns remained visible while their trunks/stems disappeared.
2. First Person could be toggled, but the rendered camera remained in the map/third-person view; the player card stayed visible and the direction gauge became incorrect.
3. The W1 evidence collector closed immediately.

The user also noted that Kanto Dynamic Weather did not continue into battle. Upstream Kanto Dynamic Weather 1.0.3 is an overworld renderer integration, so battle-weather continuity is a Gen1recomp project extension rather than an upstream guarantee.

## Root cause

W1 compiled patched `Sky`, `Voxel3D`, and `VoxelScene` as new Lua table identities. Existing Dramatic Shape companion modules had already retained references to the original tables.

This produced split renderer state:

- Weather VoxelScene used the duplicate W1 `Voxel3D`.
- `FirstPerson` updated the original `Voxel3D.camera`.
- `Flora`/tall-tree stems drew through the original `Voxel3D` while the duplicate scene was active.
- Terrain canopy/leaves remained visible because they are part of the active terrain mesh.

This single split-identity defect matches both observed visual regressions.

## W1c repair

W1c keeps the Weather semantic transform but binds the patched modules to the already-existing Dramatic Shape table identities in memory:

- patched Sky -> `baseV.require("Sky")`
- patched Voxel3D -> `baseV.require("Voxel3D")`
- patched VoxelScene -> `baseV.require("VoxelScene")`

Runtime hard gates require each compiled module to return the exact shared table identity. The bridge READY log reports:

- `sharedSky=true`
- `sharedVoxel3D=true`
- `sharedVoxelScene=true`

No Dramatic Shape file is modified on disk.

## Exact identity

W1b bridge SHA-256:
`27ab7c91ed7547c81f31d307e661cb5ed4c2e45f2a8df652c60d0187b7b9be54`

W1c bridge SHA-256:
`31b9592da88d54d246b0b156f7a0667834556ae4cb8285bd504d8a6f8f9d3920`

W1c package:
`GEN1RECOMP_W1c_WEATHER_SHARED_RENDERER_IDENTITY_REPAIR_TEST_20260823.zip`

Package SHA-256:
`a18029684916dbc75b0962b3869bba73954c920b35fc95c979d8bd2dbf54e5c9`

## Collector repair

The old collector used a PowerShell -> `cmd /c` -> adb nested redirection path and could terminate without leaving a usable evidence package.

W1c changes collection to:

- direct BAT `adb exec-out run-as ... cat ... > localfile`
- PowerShell only analyzes already-local files
- collector pauses and preserves the folder on capture/analyze failure

The W1c collector also captures exact Thor battle renderer sources for the next phase:

- `BattleScene.lua`
- `OverworldBattle.lua`
- `BattleCam.lua`
- `BattleArena.lua`

## Battle-weather continuity

Upstream Kanto Dynamic Weather 1.0.3 targets the voxel overworld renderer. Gen1recomp project requirement is now:

**Outdoor weather should visually continue into a Dramatic Shape outdoor staged battle and resume cleanly after battle.**

This is deferred to W1d so W1c can first restore renderer identity, First Person, tree trunks, and direction-gauge stability. W1d should use the exact battle sources captured by the W1c evidence collector and must preserve PMD/Stadium battle-presentation authority.

## W1c runtime acceptance

Required visual checks:

- Weather still renders outdoors.
- 3D/tall-tree trunks are restored.
- First Person becomes an actual first-person camera.
- Player card is hidden in First Person.
- Direction gauge is correct.
- One map transition is stable.
- No new crash/ANR/traceback.

Battle weather is not a W1c acceptance gate.
