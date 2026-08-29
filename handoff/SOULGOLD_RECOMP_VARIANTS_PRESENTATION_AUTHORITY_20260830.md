# SoulGoldRecomp Variant / Presentation Authority

Date: 2026-08-30

## Sealed core

S0-C3H is the FORMAL PASS / SEALED interactive baseline.

Do not fork correctness/runtime fixes into two independent codebases.

## Player-facing release variants

The project will ship two sprite editions built on ONE shared SoulGoldRecomp core:

1. **SoulGoldRecomp — Showdown Sprite Edition**
2. **SoulGoldRecomp — PMD Sprite Edition**

The shared core owns:
- runtime/recompiler correctness;
- static coverage convergence;
- Traditional Chinese `zh-Hant-TW`;
- original-faithful overworld visual policy;
- PC presentation options;
- AYN THOR / Android ARM64 support;
- input/audio/save/mod infrastructure.

Only battle-sprite provider/assets/animation metadata differ between variants.

Preferred architecture: normalized `BattleSpriteProvider` / animation manifest so Showdown and PMD backends feed the same runtime contract.

PMD provider must preserve frame timing, offsets, anchor/center metadata and AnimData-style semantics where available.

## Presentation policy

Logical GBA framebuffer is always **240x160**.

Desktop startup window defaults to **240x160 (1x)** rather than the current forced 4x 960x640 test window.

User scaling remains optional (2x/3x/4x/fullscreen). The logical framebuffer never changes.

### LCD preset

Add a built-in `LCD (mGBA-like)` presentation preset shared by both sprite editions.

Clean-room behavior target:
- GBA LCD color-space/color correction;
- subtle interframe LCD persistence/ghosting;
- preserve pixel geometry and 3:2 aspect ratio;
- no gameplay/runtime behavior changes;
- filter can be disabled.

At 1x (240x160), use color correction + temporal persistence only. A spatial LCD pixel/subpixel mask cannot be represented faithfully inside one output pixel.

At >=3x or fullscreen, an optional spatial LCD pixel-boundary/subpixel pass may be enabled automatically or by setting.

Implementation must be presentation-only and cross-platform:
- PC: SDL/OpenGL or equivalent backend;
- Android/AYN THOR: OpenGL ES-compatible path;
- correctness/frame hashes remain based on the unfiltered canonical framebuffer.

Do not make a visual shader part of PPU correctness.

## Current post-C3H evidence

Audit evidence `SOULGOLD_POST_C3H_D0_T0_V0_A0_EVIDENCE_20260830_031307.zip`:
- static coverage: NOT_STATIC;
- 356 distinct misses;
- 327,789,864 interpreted instructions recorded;
- 82 failed misses;
- 33 jump-table candidate regions;
- hot `0x030011E8` THUMB: 12,001 bridges;
- `0x0300017C` ARM (`FastUnsafeCopy32`): 231 bridges;
- translation audit found 500 hits across 11 core text/font headers/files;
- `OW_OBJECT_VANILLA_SHADOWS=FALSE`, candidate faithful setting is TRUE;
- New Bark Town has 4 light object events;
- Android toolchain audit: Java present, ADB/SDK/NDK not currently configured.

## Next parallel lanes

- **D1**: classify/fix `0x0300017C`, capture/classify dynamic `0x030011E8`, then clustered jump-table RAM code.
- **T1**: select text/glyph hook boundaries for external UTF-8 `zh-Hant-TW`.
- **V1-A**: vanilla-shadow candidate + lamp-anchor proof, without touching sealed C3H.
- **P0/P1**: identify renderer/window hook and implement 240x160 + LCD presentation candidate.
- **A1**: prepare Android SDK/NDK/ADB bootstrap and arm64-v8a runner path.
- **SPRITE-S0**: normalize Showdown sprite asset/animation contract.
- **SPRITE-P0**: normalize PMD sprite/AnimData asset/animation contract.

## Permanent requirements

1. Every meaningful checkpoint ships a handoff.
2. Final release includes Traditional Chinese `zh-Hant-TW`.
3. Primary finished hardware target is AYN THOR / Android ARM64.
4. Two sprite editions share one runtime core.
