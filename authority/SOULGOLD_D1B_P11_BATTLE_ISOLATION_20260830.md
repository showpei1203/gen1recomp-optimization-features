# SoulGoldRecomp D1B + P1.1 Battle Isolation Authority

Date: 2026-08-30

## Observed D1A/P1.1 regression

Manual test:
- map BGM recovered;
- startup viewport/window is 480x320;
- entering battle causes lag and abnormal BGM;
- after closing the game window, runtime continues dispatching IRQ vector `0x00000018` with CPSR `0x60000092`;
- synchronous harness never reaches ZIP packaging because the WSL runner does not terminate.

## Interpretation

D1A had already rolled back the SoundMainRAM native mapping. Relative to sealed C3H, the only remaining correctness optimization was the `FastUnsafeCopy32` native root at `0x0300017C`.

D1A is therefore **NOT PROMOTED**.

## D1B isolation

Return correctness completely to the C3H sealed model:
- FastUnsafeCopy32 native: OFF
- SoundMainRAM native: OFF
- C3H IntrMain / IntrMain_RetAddr roots: ON
- C3F ROM mirror correction: ON

Keep P1.1 presentation for A/B isolation:
- logical framebuffer 240x160
- startup window 480x320 (2x)
- mGBA-like color presentation
- 50/50 interframe persistence

Interpretation gate:
- battle PASS => FastUnsafeCopy32 native is causally implicated;
- battle FAIL => P1.1/host timing becomes the next A/B target.

## Harness correction

Interactive runner must no longer block evidence packaging indefinitely.
D1B launches the WSL runner asynchronously with a Linux PID file. After normal close or freeze, the user returns to the launcher and presses Enter. A still-running runner receives TERM then KILL if necessary; packaging proceeds regardless.

## Sealed/release policy

- C3H remains FORMAL PASS / SEALED.
- One shared core.
- Showdown Sprite Edition and PMD Sprite Edition remain separate content providers, not runtime forks.
- Traditional Chinese zh-Hant-TW remains required.
- Primary finished device remains AYN THOR / Android ARM64.
