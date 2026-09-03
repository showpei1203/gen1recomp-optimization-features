# HANDOVER — SoulGold M6A2 FIX4A Audio-Clock Master
Date: 2026-09-03
Branch: `feature/soulgold-showdown-m6a2`

## Status
M6A2 FIX3 is REJECTED by AYN THOR runtime evidence: audio remains incorrect and develops audible delay.
M6A2 FIX4A is built and CI-validated, but device runtime PASS is pending user THOR test.
M6A3 Showdown Android compositor remains blocked until this audio/pacing gate passes.

## Root cause
The problem is frontend timing/audio architecture, not the pinned mGBA emulation core.

The relevant Android baselines all make audio consumption part of synchronization:
- mGBA libretro GBA path consumes a smoothed per-frame amount of source audio inside `retro_run()` for frame pacing.
- mGBA SDL frontend explicitly resamples core audio to the obtained output device rate and participates in audio high-water synchronization.
- RetroArch Android resamples to frontend/device output rate, blocks/synchronizes on the audio driver and uses dynamic rate control from real audio buffer availability.
- An existing unofficial mGBA Android port uses a core thread with `audioSync=true`, 48 kHz output and Oboe.

M6A2 FIX3 did none of those correctly. It used Choreographer as the emulation master, pushed 32768 Hz PCM directly to AudioTrack, had no audio-buffer feedback or explicit frontend resampler, deliberately prefetched roughly 62.5–125 ms, and retained stale audio in large software queues. Catch-up frame bursts could therefore become growing audio delay.

## FIX4A architecture
- Pinned mGBA core remains unchanged: `507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6`.
- Choreographer is presentation-only and never calls `retro_run()`.
- Dedicated `SoulGold-M6A2-AudioClock` thread runs one mGBA frame, drains that frame audio, explicitly resamples source audio to Android native output rate, then performs blocking AudioTrack write.
- Audio sink backpressure therefore paces the next emulation frame.
- Java multi-second pending queue is removed.
- Initial prefill target is approximately one emulated frame, not 62–125 ms plus retained backlog.
- Pause/resume/reset stop the worker, flush AudioTrack, discard stale native PCM, and reset resampler phase.
- Runtime diagnostics now include playback-head position, AudioTimestamp, underrun count and estimated sink latency.

## Permanent rules
- R-SD-155 CHOREOGRAPHER_MUST_NOT_BE_THE_ONLY_MASTER_CLOCK_WHEN_AUDIO_IS_ACTIVE
- R-SD-156 ANDROID_AUDIO_PIPELINE_MUST_EXPOSE_REAL_OCCUPANCY_OR_PLAYBACK_PROGRESS_TO_SYNC_CONTROL
- R-SD-157 CORE_SOURCE_RATE_TO_DEVICE_RATE_RESAMPLING_MUST_BE_EXPLICIT_AND_FRONTEND_OWNED
- R-SD-158 AUDIO_LATENCY_MUST_BE_BOUNDED_BY_A_SMALL_TARGET_WATERMARK_NOT_MULTI_SECOND_BACKLOGS
- R-SD-159 AUDIO_SINK_PRESSURE_MUST_TRIGGER_BACKPRESSURE_RATE_CONTROL_OR_BOUNDED_DROP_NOT_STALE_QUEUE_GROWTH
- R-SD-160 PAUSE_RESUME_MUST_FLUSH_ALL_HOST_AND_NATIVE_AUDIO_QUEUES_AS_ONE_TRANSACTION
- R-SD-161 AUDIO_DIAGNOSTICS_MUST_MEASURE_DEVICE_PLAYBACK_PROGRESS_OR_REAL_OUTPUT_OCCUPANCY
- R-SD-162 M6A2_FIX2_AND_FIX3_AUDIO_ARCHITECTURES_ARE_REJECTED_AND_MUST_NOT_BE_RESURRECTED

## Build evidence
Workflow run: 33754314646
Job: `build-runtime-apk` — SUCCESS
Artifact: `SOULGOLD_M6A2_FIX4A_THOR_AUDIO_CLOCK.apk`
Bytes: 750171
SHA-256: `e1e8caef61403d065a4803dcf19f922fb5f31486098504c133713fe696dd79dd`
ABI: arm64-v8a
Contains `libmgba_libretro.so`: yes
Contains `libsoulgold_m6a2.so`: yes
ROM included: no

## THOR acceptance test
Test normal play for at least several minutes, including battle and menus.
Report:
1. Pitch: normal / low / high.
2. Audio-video timing: synchronized / fixed delay / delay grows over time.
3. Crackle: none / occasional / persistent.
4. Game speed: normal / slow / fast / unstable.
5. Enter Party/Pokemon/Summary and confirm original SoulGold transitions remain unchanged.
6. Pause to Android/home and resume; confirm stale audio does not replay.
7. If anything is wrong, press Start+Select while running to write `M6A2_FIX4A_AUDIO_CLOCK_REPORT.json` under the app external files directory.

## Promotion
Only after THOR confirms clean pitch, no progressive delay, stable speed, acceptable latency and preserved original menus may M6A3 battle-only Showdown compositor resume.
