# SoulGold M1.2 AV Clock Fix
Date: 2026-08-30

M1.1 is REJECTED.

Measured failure:
- 2236 video frames in about 113 seconds (~19.8 FPS)
- map movement, NPC text reveal, battle, and music all in slow motion
- 2,451,488 libretro audio frames over 2236 video frames (~1096 audio frames/video frame)
- at 59.7275 FPS this corresponds to ~65.5 kHz effective audio input
- M1.1 kept SDL_AudioStream configured for the stale initial 32768-Hz source rate

Root cause:
1. The pinned mGBA libretro core can update AV timing at runtime and publishes it via `RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO`.
2. M1.1 did not handle that environment command.
3. M1.1 also stacked three pacing mechanisms: renderer/compositor timing, an explicit 59.7275-FPS sleep loop, and audio queue backpressure sleep.
4. The combined clocks slowed the entire frontend to ~20 FPS.

M1.2 rules:
- restore M1's user-validated SDL renderer VSYNC presentation path
- remove explicit per-frame sleep
- remove audio backpressure sleep
- handle `RETRO_ENVIRONMENT_SET_SYSTEM_AV_INFO`
- rebuild SDL_AudioStream when mGBA changes sample rate
- infer effective audio rate from audio/video callback ratio as a safety fallback
- never clear queued audio to correct drift
- record wall-clock observed FPS
- frontend checkpoints cannot machine-PASS unless observed FPS is 50..70

mGBA remains hardware/audio emulation authority. This is a frontend timing fix only.
