# SoulGold M1.3 Audio Latency Authority
Date: 2026-08-30

## Architecture
- mGBA is the permanent GBA hardware correctness authority.
- Gen1 enhancement layer owns SoulGold state observation, external PMD/Showdown assets, localization, and host UI.
- gbarecomp is optional/experimental only and may not block the mainline.

## M1.2 result
Gameplay/visual behavior was broadly accepted by the user, but audio synchronization was rejected: event and battle SFX lagged the picture by several beats.

Evidence: `SOULGOLD_M1_2_AVCLOCK_FIX_EVIDENCE_20260830_173409.zip`

Measured:
- observed FPS: 63.4293
- mGBA audio source rate: 65536 Hz
- SDL device rate: 48000 Hz
- queue min: 732 bytes
- queue max: 588556 bytes
- queue max at 48 kHz stereo S16: ~3065 ms

The M1.2 source-rate correction was successful, but its queue was unbounded. The host was running ~6.2% faster than the mGBA 59.7275-Hz timeline, so audio accumulated continuously and became seconds late.

## M1.3 repair
Narrow frontend scheduling fix only:
- mGBA unchanged
- dynamic 65536-Hz source-rate handling retained
- no queue deletion
- no second absolute video scheduler
- audio queue is used as a bounded drift signal
- startup prebuffer ~28 ms
- target ~38 ms
- normal correction begins above ~55 ms
- emergency threshold 120 ms
- normal correction waits at most 1 ms per emulated frame
- emergency recovery waits at most 12 ms per frame

Acceptance:
- observed FPS 57..62
- source rate 64..67 kHz
- max queue latency <= 140 ms
- battle and move state remain observable

## StateBridge authority
Promoted read-only fields:
- gBattleTypeFlags = 0x0200271C
- gBattlersCount = 0x02002720
- gBattleStruct = 0x02002724
- gBattleControllerExecFlags = 0x02002994
- gCurrentMove = 0x02002AB4
- gChosenMove = 0x02002B2E

Species parsing is NOT promoted. The current reader produced `battler0_species_raw=1289`, which is invalid for this game. Species layout must be corrected before M2 PMD sprite selection.
