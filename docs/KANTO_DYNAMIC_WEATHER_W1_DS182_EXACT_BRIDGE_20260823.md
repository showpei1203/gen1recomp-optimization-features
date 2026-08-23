# Kanto Dynamic Weather W1 — Dramatic Shape 1.8.2 Exact Bridge

Date: **2026-08-23**
Status: **STATIC PASS / THOR RUNTIME PENDING**

## Goal

Integrate upstream **Kanto Dynamic Weather 1.0.3** with the exact Dramatic Shape 1.8.2 renderer currently installed on the user's AYN Thor, without modifying Dramatic Shape on disk.

Wild Skies is deliberately deferred to W2 so Weather renderer stability can be isolated first.

## Thor exact Dramatic Shape 1.8.2 authority

Captured by W0C directly from the active Thor installation. W0C uses direct `adb exec-out run-as ... cat` and local content/hash validation; it does not modify game files.

Exact hashes:
- `manifest.json`: `b8ef6c5abc8c876fb15171877b27ef2b02728de49875a9e1fa8885e8601b54b2`
- `main.lua`: `f8fb8616f30c3a9a7be16dce4b48e706c3d97dedfccbb9d0e6a0e8be56471ac1`
- `lib/Sky.lua`: `dedc35325fd7923c0dba940dc90b5a1f50574ac7775b98367632c76a366ed992`
- `lib/Voxel3D.lua`: `399e45e4549ad844885acc1c98fbb3756e7975f1376bbb0318bd54bc6c29af75`
- `lib/VoxelScene.lua`: `d273b3f94b6e0822710d4ce02b830762a46399f2a4385ab1b96919c25781b7ec`
- `lib/AntiAlias.lua`: `ad2b9332029b0cea8420ee32df24aa38bc42b946a4675c3944666e2d47f74966`

Drive evidence:
- file ID: `1Z-xK4Avu_Of6I8pJ11oI4ARWSf0vAv2B`
- `GEN1RECOMP_W0C_THOR_EXACT_DS182_SOURCE_CAPTURE_20260823_201454.zip`

## Upstream Weather authority

Repository: `1-Camp0-1/Kanto-Dynamic-Weather`
- version: `1.0.3`
- pinned commit: `e9e2ddef22596157fb4c5f919e3ab18718b52265`
- official dependency: `DRAMATIC_SHAPE >=1.7.2 <1.8.0`

The upstream architecture reads Dramatic Shape source through `mod.exports.lib`, applies narrow in-memory patches to `Sky`, `Voxel3D`, and `VoxelScene`, compiles the patched modules for the Weather companion render path, and leaves Dramatic Shape files untouched on disk. W1 preserves this safety model.

## Why the upstream 1.7 bridge cannot simply be version-widened

The exact Thor Dramatic Shape 1.8.2 source has renderer changes that invalidate upstream 1.7.x unified-diff contexts. A concrete example is the voxel shader varying block: DS 1.8.2 added `vFirefly` immediately after `vFog`, while the Weather 1.7 bridge expects the older context at that location when inserting `vAtmosWorld`.

The Thor lineage also contains First Person/free-pitch sky handling, local VoxelScene integration changes, and `Voxel3D.refreshLighting()` used by battle-presentation fog handoff. Therefore changing only the manifest dependency range would be unsafe.

## W1 bridge design

W1 replaces the upstream 1.7 bridge with deterministic semantic transforms authored against the exact Thor DS 1.8.2 source.

Properties:
- starts from the installed Thor source at runtime
- fails closed if a required semantic anchor does not occur exactly once
- patches in memory and compiles companion modules
- **does not write Dramatic Shape on disk**
- preserves DS 1.8.2 `vFirefly`
- preserves First Person/free-pitch sky behavior
- preserves existing local VoxelScene changes because the transform starts from Thor exact source
- adapts `Voxel3D.refreshLighting()` for Weather `fog.startFromFocus`
- clears temporary `cinematicAtmos` / horizon state on scene cleanup
- does not modify PMD, StadiumBattleFX, Kanto First Person, or Wilds source files

Runtime markers:
- `[GEN1RECOMP_W1][WEATHER_BRIDGE] READY ds=1.8.2`
- `[GEN1RECOMP_W1][WEATHER] MAIN_READY ds=...`

Bridge SHA-256:
`27ab7c91ed7547c81f31d307e661cb5ed4c2e45f2a8df652c60d0187b7b9be54`

## W1 candidate

Package:
`GEN1RECOMP_W1_KANTO_DYNAMIC_WEATHER_DS182_BRIDGE_TEST_20260823.zip`

Package SHA-256:
`3223aee697765a971440b15fadacd1f22ca6727e409bb5d46162161679eead1e`

Drive test build:
- file ID: `1ei0rwnKpYLW4QzIs14Y3t5OrENKpwQ2Q`
- `GEN1RECOMP_W1_KANTO_DYNAMIC_WEATHER_DS182_BRIDGE_TEST_20260823.zip`

Installer hard-gates the exact Thor `Sky.lua`, `Voxel3D.lua`, and `VoxelScene.lua` hashes before installing. It refuses to overwrite an existing `kanto_dynamic_weather` directory. It downloads only the pinned upstream Weather commit, applies the W1 overlay to the Weather candidate, then installs Weather as a separate mod.

Rollback removes only `mods/kanto_dynamic_weather`.

## Static verification

Before delivery:
- transformed `Sky.lua`: parse PASS
- transformed `Voxel3D.lua`: parse PASS
- transformed `VoxelScene.lua`: parse PASS
- W1 bridge: parse PASS
- package ZIP integrity: PASS

Status remains **runtime unverified** until Thor evidence is returned.

## W1 runtime acceptance

Required checks:
1. Game reaches an outdoor map without black screen/crash.
2. Weather option rows are visible.
3. `ATMOSPHERE=FULL` works.
4. `WEATHER=CLEAR` renders normally.
5. `WEATHER=RAINING` renders visibly and spatially correctly.
6. `WEATHER=THUNDERSTORM` and lightning render normally.
7. First Person remains stable with Weather active.
8. At least one map transition is stable.
9. While raining, enter one ordinary battle; PMD and StadiumBattleFX remain normal and Weather does not leak incorrectly over the battle presentation.
10. Return to overworld; Weather resumes normally.
11. No new crash / traceback / ANR and no unacceptable FPS regression.
12. Collector reports bridge/main READY rows, zero relevant runtime errors, and unchanged exact DS hashes.

## Next lane

Only after W1 Weather runtime/visual acceptance should W2 add **Wild Skies**. W2 will validate airborne overworld entity rendering, depth/occlusion against Weather clouds/atmosphere, First Person presentation, Wilds encounter coexistence, and performance without reopening accepted PMD/Stadium battle-presentation behavior.
