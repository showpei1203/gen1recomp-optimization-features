# GEN1RECOMP W2B — Animated Voxel Flyer Bridge

Date: 2026-08-23
Status: TEST CANDIDATE / runtime pending

## Accepted input
- W2B0C COMPLETE exact capture: PASS
- Voxel Characters 1.8.0
- PMD Idle Battle Sprites 0.2.18b
- Wild Skies 1.12.0
- Dramatic Shape 1.8.2
- Wilds of Kanto / overworld_wild_spawns 2.1.0
- W2A Wild Skies stack: user visual PASS and structural PASS

## Objective
Make Wild Skies airborne Pokemon:
1. visibly animate using the already-installed PMD Walk cycles, instead of translating a static portrait/card;
2. expose the same animated sprite as CPU ImageData so Voxel Characters can build a real voxel/slab mesh instead of falling back from `mask_failed`.

## Design
A new independent mod is installed:
`gen1recomp_pmd_sky_voxel_bridge`

No existing DS / Weather / Wilds / Wild Skies / PMD / Voxel Characters file is modified.

The bridge ships no PMD sprite pixels. It reads the user's existing PMD files under the standard mod asset path, selects frame 0 plus the most visibly different PMD Walk frame, and lazily bakes an in-memory 16x96 six-cell walker strip:
- stand down
- stand up
- stand left
- walk down
- walk up
- walk left

Down/left use the PMD enemy/front Walk view; up uses the PMD player/back Walk view when available. Right mirroring remains engine-owned.

The bridge registers BOTH `Assets.image` and `Assets.imageData` virtual assets. The ImageData registration is the Voxel Characters compatibility requirement because its `maskFor()` path reads through Dramatic Shape ImageCache -> Assets.imageData.

## Authority hashes
- Voxel Characters main.lua: `a0d84c5fa7a595bb9efe6538a6adcf69414039fbe79743ba11707a208bf1716a`
- PMD main.lua: `b67b2f57bb955eea1834210a471ddf0c2ef20cd50f82c145e074c9a5e0d36d46`
- Wild Skies main.lua: `3f491608ab33d7fc0f986975628824a58707241aa932c33b4f6c74166849a0db`
- Dramatic Shape VoxelScene.lua: `d273b3f94b6e0822710d4ce02b830762a46399f2a4385ab1b96919c25781b7ec`
- Wilds main.lua: `cc5da502de2d240b03c879f58a4ef2754db94cdc854e517a304a2868c54c7625`

## Candidate hashes
- ZIP: `ee7564d6afe4720b1b41dfa077e14c5d22e73359a800b64aea72ed3c1d4438cf`
- bridge main.lua: `5ed941fdde0252689cc7f8127fa38bcd681f4ce02faa7c3ea6c85f970ae5be31`
- bridge manifest.json: `8817132c5e51236e92d0e156a8543c1cf75c6f2ed7dc12829d7c110cc768aa19`
- PMD walk metadata rows: 151

Drive test build:
`https://drive.google.com/file/d/1uL1ommJQk0hYHCJBfyGY_keG1w2Kr0PD/view?usp=drivesdk`

## Runtime acceptance
- `GEN1RECOMP_W2B_READY` present with `pidgeyProbe=true`
- at least one `GEN1RECOMP_W2B_SOURCE_HIT`
- at least one `GEN1RECOMP_W2B_BAKE`
- no `GEN1RECOMP_W2B_BLOCKED`
- no new runtime crash/ANR/Traceback
- user can visibly see PMD flyer animation
- flyer has Voxel Characters thickness/solid volume
- no giant scaling or cropped-corner artifact
- weather / first-person / ground Wilds remain visually normal

## Known limitation
W2B deliberately reuses the current PMD battle mod's two battle-view Walk strips. It provides real PMD animation plus front/back distinction, but not the original full eight-direction PMD air sheet. A later W2C can add a dedicated 8-direction air source only if visual acceptance shows it is worth the extra asset lane.
