# SoulGold M1.4 Core Clock Audio Sync Authority
Date: 2026-08-30

## Supersedes M1.3 bounded-queue approach
M1.3 is rejected. The audio queue was a symptom of frontend overclock, not the timing authority.

## Root-cause proof
mGBA reports 59.727501 FPS.

M1.2:
- host observed 63.4293 FPS
- 48.1481-s run
- observed audio queue max 588556 bytes
- predicted queue growth from FPS mismatch at 48 kHz stereo S16: ~572953 bytes
- error ~2.7%

M1.3:
- host observed 62.4737 FPS
- 41.5375-s run
- observed queue max 386672 bytes
- predicted growth ~366690 bytes
- error ~5.4%

The same equation explains two independent runs, so the accumulating SE delay is caused by calling `retro_run` faster than mGBA's reported game clock.

## M1.4 repair
Exactly one frontend clock:
- use mGBA/libretro reported FPS as cadence authority
- call `retro_run` once per core frame interval
- renderer VSYNC disabled as a pacing source
- audio queue does not block gameplay
- no bounded audio-master queue controller
- no live sample deletion
- dynamic source-rate updates retained

Telemetry:
- wall-clock observed FPS
- target FPS
- periodic audio queue milliseconds
- linear queue drift ms/s

Acceptance:
- observed FPS within 0.35 of target
- source rate 64..67 kHz
- queue max <=160 ms
- queue final <=130 ms
- absolute queue drift <=2 ms/s
- battle + move state remain observable

## Species authority correction
SoulGold source `include/constants/species.h` defines:
- `SPECIES_SPRIGATITO = 1289`
- `SPECIES_MARILL = 183`

The observed battler pair 1289 / 183 is valid and supports the current gBattleMons species reader. The prior invalid-species statement is withdrawn.
