# SoulGoldRecomp S0-C3D Diagnostic Build Fix

Date: 2026-08-29

## Observed failure
The first S0-C3D launcher successfully patched the detached `gbarecomp_c3d` worktree but failed during CMake configure:

- `include could not find requested file: external/arm-recomp-core/cmake/ArmRecompCore.cmake`
- `Unknown CMake command "arm_recomp_core_sources"`

## Root cause
Pinned GBARecomp declares `external/arm-recomp-core` as a Git submodule. A newly-created detached Git worktree does not automatically materialize the submodule working tree, while GBARecomp `CMakeLists.txt` unconditionally includes `external/arm-recomp-core/cmake/ArmRecompCore.cmake`.

The sealed baseline already has the pinned submodule populated and previously built successfully, so the diagnostic worktree should reuse that exact populated source rather than fetching a potentially different external revision.

## Fix policy
S0-C3D Fix1:
1. verify sealed `gbarecomp/external/arm-recomp-core/cmake/ArmRecompCore.cmake` exists;
2. reset/clean only `gbarecomp_c3d`;
3. create `gbarecomp_c3d/external/arm-recomp-core` as a symlink to the sealed populated submodule source;
4. delete stale `build-c3d` CMake cache from the failed configure;
5. re-run diagnostic patch/configure/build;
6. leave sealed S0-B source and runner untouched.

## Status
This was a diagnostic harness setup defect, not a new SoulGold runtime failure. S0-A/B/C1/C2 remain sealed; S0-C3 remains FAIL / NOT PROMOTED; S0-C3D remains diagnostic-only.
