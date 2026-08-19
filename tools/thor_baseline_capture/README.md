# THOR Baseline Capture

First-pass, read-only discovery for the exact Gen1recomp installation currently used on the user's THOR workflow.

## Capture goals

- identify the exact Gen1recomp root
- inventory both game-root `mods/` and Windows LÖVE save-directory mods
- parse `manifest.json`
- hash files with SHA-256
- copy small text source/config files for engineering analysis
- specially flag PMD / battle animation / SFX / Kanto / Voxel / 3D / Input / Start / Select related paths
- do not copy ROM, save-state, EXE/DLL/ZIP/media into the diagnostic archive

## Artifact

Initial tool package: `GEN1RECOMP_THOR_BASELINE_CAPTURE_V1_20260819.zip`

SHA-256: `6d82c3fde85f2c1736b6ed41ea725006b1644ae14f0833fcc970e58139bc965f`

The generated capture ZIP is intended for baseline discovery only. No runtime or mod changes should be made before the capture is reviewed.
