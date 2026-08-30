# SoulGold mGBA Mainline — M1 PASS / M1.1 Audio + StateBridge
Date: 2026-08-30

## M1 result
M1 Live State Correlator is FORMAL PASS for gameplay/state observation.

User result:
- gameplay/graphics/input normal
- audio abnormal

Evidence:
- OVERWORLD 12/12 samples
- NPC_DIALOGUE 12/12
- POST_DIALOGUE 12/12
- SCRIPTED_EVENT 12/12
- BATTLE_IDLE 12/12
- MOVE_MENU 12/12
- MOVE_EXECUTION 12/12
- M1_CAPTURE_GATE=PASS
- mGBA core 0.11.0, pinned revision c65e8a3d4666b0ea68a01578232452f31b185332
- 5931 video frames

Promoted read-only battle globals from the SoulGold symbol corpus and runtime captures:
- gBattleTypeFlags = 0x0200271C
- gBattlersCount = 0x02002720
- gBattleStruct = 0x02002724
- gBattleControllerExecFlags = 0x02002994
- gCurrentMove = 0x02002AB4
- gChosenMove = 0x02002B2E
- gBattleMons = 0x02002B34

Runtime evidence:
- overworld/dialogue/event: gBattlersCount=0, gBattleTypeFlags=0
- battle: gBattlersCount=2, gBattleTypeFlags=12
- move execution: gCurrentMove/gChosenMove changed from 10 to 39 during capture

## M1 audio defect classification
The audio defect belongs to the temporary Gen1 SDL host, not the mGBA emulation core.

M1 host problems:
- mGBA core audio was queued directly to SDL at the core rate
- renderer VSYNC was used as the main pacing clock
- when queued audio exceeded a threshold the host called SDL_ClearQueuedAudio(), deleting live samples

This host policy is retired.

## M1.1
M1.1 introduces:
- SDL_AudioStream sample-rate conversion from mGBA rate to the actual host device rate
- 48 kHz device target
- startup prebuffer
- mGBA-FPS-based frame pacing instead of monitor VSYNC
- bounded queue backpressure; no live sample deletion
- first read-only SoulGoldStateBridge logging battle state, battler species, current move and chosen move

mGBA remains the hardware/audio-emulation authority. Gen1 owns only host output and enhancement logic.
