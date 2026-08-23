# Kanto Dynamic Weather + Wild Skies Integration — W0 Source Capture

Date: **2026-08-23**
Status: **IN PROGRESS / SOURCE CAPTURE**

## Starting authority

PMD + StadiumBattleFX `v0.2.18b` is the sealed starting authority.

- PMD main: `b67b2f57bb955eea1834210a471ddf0c2ef20cd50f82c145e074c9a5e0d36d46`
- PMD manifest: `f75aca6b3d0a98c56b131cc3cb6730aba772f9499df581b9cc3fdeaf261f1563`
- StadiumFxPlayer: `7e40e164f24e89c0671d6ef8a0b4fd21f68b0443232f68410b2070f100c17cd7`

## Target mods

### Kanto Dynamic Weather
Upstream target: `1.0.3`.

Upstream manifest hard dependency:
`DRAMATIC_SHAPE@>=1.7.2 <1.8.0`

Weather uses an in-memory compatibility bridge that patches three Dramatic Shape renderer modules:
- `Sky.lua`
- `Voxel3D.lua`
- `VoxelScene.lua`

The current AYN Thor stack uses DRAMATIC_SHAPE `1.8.2`, therefore a dependency-range-only edit is prohibited. W1 must rebase/verify the bridge against the exact installed 1.8.2 source.

### Wild Skies
Wild Skies is treated as an overworld air-entity / encounter lane. Integration must preserve its own spawning and battle-return lifecycle. Weather must not steal or duplicate its entity ownership.

## Current AYN Thor stack observed in v0.2.18b smoke

- DRAMATIC_SHAPE `1.8.2`
- kanto_first_person_thor_compat `1.60.0b-thor`
- overworld_wild_spawns `2.1.0`
- STADIUM_BATTLE_FX `2.1.8.1`
- pmd_idle_battle_sprites `0.2.18b`

## W0 package

`GEN1RECOMP_W0_WEATHER_WILDSKIES_SOURCE_CAPTURE_20260823.zip`

SHA-256:
`6246ef11760bb82416df868d3fbf169d1ce7090d414582a0554345d08f3f2c68`

Drive file id:
`1j7H0LXKH0ZWnU5zaP2s5wYZ1AH49XQyg`

W0 is read-only. It:
- captures exact installed renderer/mod source from the AYN Thor;
- downloads pristine upstream Weather and Wild Skies release ZIPs;
- extracts them locally;
- records manifests, versions and SHA-256 hashes;
- does not install, enable, patch or modify any game file.

## W1 planned gates

1. Rebase Kanto Dynamic Weather compatibility bridge onto exact DS 1.8.2 sources.
2. Preserve Kanto First Person / THOR camera ownership.
3. Preserve Wilds of Kanto ground/levitate entities.
4. Audit Wild Skies altitude, billboard/depth and rooftop perch behavior under weather fog/clouds/rain.
5. Preserve PMD/Stadium battle presentation and battle-return lifecycle.
6. Validate transition/map reload/invalidate ownership.
7. Add negative gates for duplicate draw, hidden birds, broken sky, square-mask regression, crash/ANR.
8. Profile AYN Thor frame-time under CLEAR / RAINING / THUNDERSTORM and with Wild Skies active.

No Weather/Wild Skies candidate becomes formal without combined visual and performance acceptance.
