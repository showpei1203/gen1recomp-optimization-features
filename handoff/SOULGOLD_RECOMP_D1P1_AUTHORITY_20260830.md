# SoulGoldRecomp D1 + P1 Candidate Authority

Date: 2026-08-30

## Status

**D1P1 = REJECTED / NOT PROMOTED.**

C3H remains the FORMAL PASS / SEALED interactive baseline.

## What passed

- Runtime exited normally (`RUN_EXIT_CODE=0`).
- Indoor/outdoor traversal, events and battle entry remained functional.
- Static coverage improved dramatically versus C3H:
  - distinct misses: `356 -> 76` (~78.7% reduction)
  - interpreted instructions: `327,789,864 -> 5,559,470` (~98.3% reduction)
- Generated roots were present for C3H `IntrMain`, C3H `IntrMain_RetAddr`, D1 `FastUnsafeCopy32`, and D1 `SoundMainRAM`.
- Present cadence remained about 59.69 FPS mean, 60.10 FPS median; 14 / 6727 gaps exceeded 25ms during ~112.7 sec.

## Rejection reason

Manual acceptance found **audible BGM corruption/noise** in D1P1.

The C3H sealed baseline had clean audio. The new D1P1 change that directly touched the mixer execution path was static-native promotion of runtime-copied `SoundMainRAM`:

- runtime `0x030011E8`
- ROM backing `0x082959F8`
- copied size `0xB40`

Therefore SoundMainRAM native promotion is not accepted despite the very large coverage improvement. Audio correctness outranks coverage/performance.

D1A rolls that root/mapping back while retaining the independent `FastUnsafeCopy32` native root.

## Presentation feedback

- `240x160` / scale 1 is too small for the requested desktop presentation.
- Direct original mGBA reference confirms desired desktop game viewport is `480x320` / scale 2 while logical GBA framebuffer remains `240x160`.
- The target filter appearance is the actual mGBA LCD-filter look shown in the user's reference.

## Corrected visual authority

Direct original SoulGold/mGBA comparison supersedes the earlier visual assumption:

- New Bark lamp glow position is already original/correct. Do **not** move the `OBJ_EVENT_GFX_LIGHT_SPRITE` events.
- Persistent overworld character shadows are original behavior. Do **not** change `OW_OBJECT_VANILLA_SHADOWS` to TRUE.
- Original mGBA shadows appear lighter than the current recomp presentation.
- Since the same guest ROM already produces the desired lamp/shadow result under mGBA, the next correction belongs to host presentation first, not guest map/config edits.
- Do not alter `OW_SHADOW_INTENSITY` until host LCD presentation matches the mGBA reference.

## Next authority

Proceed to **D1A + P1.1**, followed by P1.2:

- retain `FastUnsafeCopy32` native;
- rollback SoundMainRAM native;
- capture D2 mixed-mode mixer evidence;
- startup window `480x320` (2x);
- keep canonical framebuffer `240x160`;
- P1.2 reproduces mGBA LCD presentation more faithfully before any guest visual change.

## Release architecture

One shared runtime/core, two sprite-content editions:

1. SoulGoldRecomp — Showdown Sprite Edition
2. SoulGoldRecomp — PMD Sprite Edition

Traditional Chinese `zh-Hant-TW` remains mandatory. Primary finished hardware remains AYN THOR / Android ARM64 (`arm64-v8a`).
