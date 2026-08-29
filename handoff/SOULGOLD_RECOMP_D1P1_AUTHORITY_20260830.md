# SoulGoldRecomp D1 + P1 Candidate Authority

Date: 2026-08-30

## Sealed baseline

- S0-C3H = FORMAL PASS / SEALED interactive baseline
- C3H correctness roots are preserved unchanged:
  - `0x03000000 -> 0x09E864A0`, ARM, `IntrMain`
  - `0x0300012C -> 0x09E865CC`, ARM, `IntrMain_RetAddr`
- C3F conservative ROM-mirror native-entry dispatch remains part of the candidate lineage.

## D1 static-coverage candidate

D0 evidence showed persistent hot interpreter misses:

- `0x030011E8` THUMB, 12001 bridges
- `0x0300017C` ARM, 231 bridges

Reviewed source mappings:

- `FastUnsafeCopy32`: runtime `0x0300017C`, immutable ROM backing `0x09E8661C`, ARM.
- `SoundMainRAM`: source `0x082959F8`, copied by `m4aSoundInit()` into `SoundMainRAM_Buffer` at runtime `0x030011E8`, size `0xB40`, THUMB.

D1 candidate adds:

- an explicit native `FastUnsafeCopy32` root;
- a full `SoundMainRAM_Buffer` code-copy mapping;
- an explicit native runtime `SoundMainRAM` root.

The game is not allowed to launch unless generated dispatch contains the two C3H sealed roots plus both D1 native roots.

## P1 presentation candidate

Requested desktop startup presentation:

- logical/base surface: `240x160`
- startup scale: `1`
- aspect: 3:2

P1 is presentation-only and does not modify canonical PPU/frame-hash truth.

Candidate LCD presentation:

- mGBA-like GBA Color sRGB profile;
- darken value `0.5`;
- optional two-frame 50/50 persistence, enabled for this A/B candidate;
- raw canonical framebuffer remains unchanged.

The visible 3x LCD pixel-boundary pass is deferred to P2 / high-DPI output, especially AYN THOR. A 1x `240x160` output cannot faithfully represent the 3x LCD boundary structure.

## Release architecture

One shared runtime/core, two final sprite-content editions:

1. SoulGoldRecomp — Showdown Sprite Edition
2. SoulGoldRecomp — PMD Sprite Edition

Correctness, localization, presentation, Android host, audio, save and mod infrastructure must not fork between these editions.

## Permanent requirements

- Final localization: Traditional Chinese `zh-Hant-TW`, external string/glyph architecture with English fallback.
- Primary finished hardware: AYN THOR / Android ARM64 (`arm64-v8a`).
- PC/WSL is development/diagnostic only.
- Every meaningful checkpoint ships a downloadable handoff.

## Candidate handoff

`SOULGOLD_RECOMP_HANDOFF_S0_D1P1_20260830.zip`

SHA-256:
`b19479c30126f3b55c43959e1d6efd27f884b621b9b5ce69b7766983fb9771f5`

## Acceptance test

Run `tools\soulgold_recomp\START_S0_D1P1.bat`.

After codegen gates pass, test approximately 2–3 minutes:

- indoor movement/dialogue;
- outdoor movement;
- event progression;
- one battle;
- BGM / sound effects;
- `240x160` startup-window usability;
- LCD presentation (pleasant / too dark / too ghosty / other).

Return `SOULGOLD_S0_D1P1_EVIDENCE_*.zip` for review before promotion.
