# SoulGoldRecomp D1A + P1.1 Reference-Corrected Authority

Date: 2026-08-30

## Baseline

C3H remains FORMAL PASS / SEALED.
D1P1 is rejected because SoundMainRAM native promotion caused audible BGM noise.

## D1A

Retain only the independent native root:

- `FastUnsafeCopy32`: runtime `0x0300017C`, ARM, ROM backing `0x09E8661C`.

Rollback static native promotion of `SoundMainRAM` at `0x030011E8` to restore the proven C3H audio path.

Capture the newly exposed hot mixed-mode mixer cluster around `0x030015C8..0x03001600` for D2 instead of assuming the whole copied buffer is safe as one native body.

## P1.1

- logical GBA framebuffer: `240x160`
- requested PC startup viewport: `480x320`
- startup scale: `2x`
- canonical framebuffer remains unfiltered correctness truth
- current color/persistence experiment stays presentation-only

## Original mGBA visual reference

The user's original SoulGold/mGBA screenshot is the visual authority:

- New Bark lamp glow position is already correct/original.
- Persistent overworld character shadows are original behavior.
- Original shadows look lighter than current recomp presentation.
- Desired desktop viewport is 480x320.
- Desired display look is the actual mGBA LCD-filter appearance.

Therefore do not modify the SoulGold guest map/config for lamps or shadows yet.
Specifically:

- do not move New Bark `OBJ_EVENT_GFX_LIGHT_SPRITE` coordinates;
- keep `OW_OBJECT_VANILLA_SHADOWS = FALSE`;
- do not change `OW_SHADOW_INTENSITY` yet.

P1.2 must first match mGBA LCD presentation more faithfully. Only after that comparison may guest visual parameters be reconsidered.

## Release architecture

One shared core, two final sprite editions:

1. Showdown Sprite Edition
2. PMD Sprite Edition

Traditional Chinese `zh-Hant-TW` remains required. Primary finished target remains AYN THOR / Android ARM64 (`arm64-v8a`).

## Handoff

`SOULGOLD_RECOMP_HANDOFF_S0_D1A_P11_REFERENCE_CORRECTED_20260830.zip`

SHA-256:
`e1f3bb14b5e5ec352d9243634667f12d344bcac9806019262330d07bbf908c02`
