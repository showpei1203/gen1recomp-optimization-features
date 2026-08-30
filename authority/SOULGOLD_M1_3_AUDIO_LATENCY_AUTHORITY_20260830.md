# SoulGold M1.3 Audio Latency Authority — CORRECTED
Date: 2026-08-30

## Status
M1.3 is REJECTED.

User-visible result:
- gameplay/visuals broadly normal
- event and battle SFX still clearly delayed behind the picture

Machine evidence:
- observed FPS: 62.4737
- mGBA target FPS: 59.727501
- source audio rate: 65536 Hz
- device rate: 48000 Hz
- queue max: 386672 bytes = ~2014 ms
- bounded pacing calls: 2564
- nominal paced wait: 30658 ms

## Correct root cause
The queue is a symptom, not the authority.

M1.2 ran `retro_run` at 63.4293 FPS while mGBA reports 59.727501 FPS. At 48 kHz stereo S16, that predicts about 572953 bytes of excess queued audio during the 48.1481-s run. Observed queue max was 588556 bytes, only ~2.7% different.

M1.3 ran at 62.4737 FPS. The same calculation predicts about 366690 bytes of excess queue during the 41.5375-s run. Observed queue max was 386672 bytes, ~5.4% different.

This two-run match proves the accumulating SE delay is caused by the frontend calling `retro_run` faster than mGBA's reported game clock. The bounded audio-master queue controller did not fix that root timing error and is retired.

## M1.4 direction
Use one clock only:
- mGBA/libretro reported FPS is the frontend cadence authority
- call `retro_run` once per 1/59.727501 s
- renderer VSYNC is not a pacing authority
- audio queue depth is telemetry only
- no queue-based gameplay throttling
- no audio sample deletion
- dynamic 65536-Hz source-rate handling retained

## StateBridge correction
The earlier statement that species 1289 was invalid is REVOKED.

SoulGold source authority defines:
- `SPECIES_SPRIGATITO = 1289`
- `SPECIES_MARILL = 183`

Therefore the observed battler species pair 1289 / 183 is consistent with Sprigatito / Marill and supports the current species reader.

Promoted read-only state:
- gBattleTypeFlags = 0x0200271C
- gBattlersCount = 0x02002720
- gBattleStruct = 0x02002724
- gBattleControllerExecFlags = 0x02002994
- gCurrentMove = 0x02002AB4
- gChosenMove = 0x02002B2E
- gBattleMons base = 0x02002B34
