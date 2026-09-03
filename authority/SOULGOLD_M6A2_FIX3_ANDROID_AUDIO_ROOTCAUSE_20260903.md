# SOULGOLD M6A2 FIX3 — Android Audio Delay Root Cause Authority
Date: 2026-09-03
Status: ROOT CAUSE CONFIRMED / FIX3 REJECTED ON THOR

## User acceptance result
M6A2 FIX3 is rejected on AYN THOR. Audio still fails and is audibly delayed.

## Reference baseline correction
There is no official mGBA Android frontend as of 2026-02. The relevant working Android baseline is RetroArch Android + the same mGBA libretro core family. The comparison therefore isolates frontend timing/audio architecture rather than the emulation core.

## Same-core evidence
The M6A2 workflow pins mGBA commit `507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6` and builds `mgba_libretro.so`.
The pinned mGBA libretro frontend already consumes GBA audio in `retro_run()` using a moving average of samples available per frame specifically for frame pacing. It sets its internal audio buffer to roughly two frames of source audio to allow small generation variance.

Therefore M6A2 must not add a large independent backlog on top of the core and then treat that backlog as an audio solution.

## Root cause A — FIX3 is video-clock-master with no audio feedback loop
FIX3 advances emulation from Java `Choreographer` timestamps:
`frameBudget += dt * coreFps`.
Audio is then pushed independently to `AudioTrack`.

There is no buffer-watermark feedback from the Android audio device to emulation pacing and no dynamic resampler rate control. Display clock and hardware audio clock are independent clocks. Small mismatch or transient UI stalls therefore accumulate as audio queue error.

RetroArch does the opposite at the frontend layer: its audio pipeline measures audio-driver write availability, uses the buffer half-full point as a control setpoint, and adjusts the resampler ratio slightly around 1.0. With audio sync enabled, a full audio sink also applies backpressure instead of allowing an arbitrary backlog.

## Root cause B — FIX3 deliberately injects large latency
FIX3 waits for `prefillShorts` before playback, with a range of 4096..8192 interleaved int16 samples.
At the GBA source rate of 32768 Hz stereo this is approximately 62.5..125 ms of queued audio before playback, before Android HAL/device latency.

The AudioTrack is also created with a buffer at least `max(minBuffer*2, 16384 bytes)`, further encouraging a deep queue instead of low-latency bounded occupancy.

## Root cause C — triple buffering permits seconds of stale audio
Current buffering layers:
1. mGBA internal per-frame audio buffer.
2. Native bridge deque: max 131072 int16 samples = about 2.0 seconds of stereo audio at 32768 Hz.
3. Java `pending[]`: 65536 int16 samples = about 1.0 second.
4. Android AudioTrack / HAL queue.

The native + Java software queues alone permit roughly 3 seconds of backlog. When non-blocking writes return zero/partial, FIX3 retains old audio and retries later. It therefore converts sink pressure into audible delay instead of correcting rate or bounding latency.

## Root cause D — hidden Android resampling is outside our control loop
mGBA GBA source audio is 32768 Hz. FIX3 opens AudioTrack at the core source rate instead of a native Android output rate. Android devices commonly mix at a different hardware/output rate, so Android performs an implicit resample downstream.

RetroArch explicitly has a frontend resampler between core input rate and configured/device output rate, and its rate-control loop adjusts that ratio based on real buffer occupancy. mGBA's standalone SDL frontend likewise initializes an explicit audio resampler from core sample rate to the obtained device rate.

FIX3 delegates resampling downstream but receives no occupancy/timing feedback from that resampler, so it cannot correct drift.

## Root cause E — catch-up frame bursts become audio backlog
FIX3 allows up to four `retro_run()` calls in one Choreographer callback after display/UI delay. Each run produces a normal frame of audio immediately. The AudioTrack still consumes in real time, so catch-up bursts increase queued audio latency.

A correct frontend may catch up presentation, but must keep audio occupancy near a bounded target rather than preserve every stale queued sample.

## Root cause F — pause/resume does not clear every latency layer
FIX3 pause clears Java pending state and flushes AudioTrack, but the native audio deque is not explicitly cleared by the Java pause path. Stale native samples can survive a frontend pause/resume boundary and be replayed later.

## Root cause G — diagnostics measure production, not what the user actually heard
FIX3 reports generated/drained/written totals but does not measure the playback head/timestamp or actual device-buffer occupancy. A report can therefore look numerically balanced while audible audio remains hundreds of milliseconds behind video.

## Comparison with mGBA/RetroArch architecture
### mGBA libretro core
- GBA audio is consumed per `retro_run()`.
- Samples-per-frame are smoothed with a moving average.
- Core internal audio buffer is intentionally small and tied to frame production.

### mGBA SDL frontend
- Device callback pulls audio.
- Explicit resampler converts core sample rate to obtained device rate.
- `audioHighWater` participates in core/audio synchronization.
- Underflow produces silence rather than replaying an arbitrarily long stale backlog.

### RetroArch Android
- mGBA core callback enters the frontend audio pipeline directly.
- Explicit resampling to frontend output rate.
- Dynamic rate control uses driver write availability / buffer occupancy.
- Audio sync can apply backpressure when output is full.
- Android OpenSL queue is bounded and reports write availability.

### M6A2 FIX3
- Java display callback is the sole emulation master.
- AudioTrack is a separate independent sink.
- No explicit source->device resampler.
- No audio occupancy feedback.
- No dynamic rate control.
- Large native and Java queues preserve stale audio.
- Non-blocking sink pressure becomes increased latency.

## Permanent rules
- R-SD-155: CHOREOGRAPHER_MUST_NOT_BE_THE_ONLY_MASTER_CLOCK_WHEN_AUDIO_IS_ACTIVE
- R-SD-156: ANDROID_AUDIO_PIPELINE_MUST_EXPOSE_REAL_OCCUPANCY_OR_PLAYBACK_PROGRESS_TO_SYNC_CONTROL
- R-SD-157: CORE_SOURCE_RATE_TO_DEVICE_RATE_RESAMPLING_MUST_BE_EXPLICIT_AND_FRONTEND_OWNED
- R-SD-158: AUDIO_LATENCY_MUST_BE_BOUNDED_BY_A_SMALL_TARGET_WATERMARK_NOT_MULTI_SECOND_BACKLOGS
- R-SD-159: AUDIO_SINK_PRESSURE_MUST_TRIGGER_BACKPRESSURE_RATE_CONTROL_OR_BOUNDED_DROP_NOT_STALE_QUEUE_GROWTH
- R-SD-160: PAUSE_RESUME_MUST_FLUSH_ALL_HOST_AND_NATIVE_AUDIO_QUEUES_AS_ONE_TRANSACTION
- R-SD-161: AUDIO_DIAGNOSTICS_MUST_MEASURE_DEVICE_PLAYBACK_PROGRESS_OR_REAL_OUTPUT_OCCUPANCY
- R-SD-162: M6A2_FIX2_AND_FIX3_AUDIO_ARCHITECTURES_ARE_REJECTED_AND_MUST_NOT_BE_RESURRECTED

## FIX4 direction
FIX4 must be an audio-clock-aware frontend, not another AudioTrack parameter tweak.

Required architecture:
1. Keep the pinned mGBA core and its per-frame audio pacing unchanged.
2. Remove the 1–3 second software backlog architecture.
3. Use the Android native output rate (normally obtained from the audio backend), not the mGBA source rate as the final sink contract.
4. Add explicit source-rate -> device-rate resampling.
5. Track real sink occupancy/playback progress and keep a small target queue (initial target roughly 30–60 ms; device evidence decides the final value).
6. Apply bounded rate correction around nominal ratio, analogous to RetroArch dynamic rate control.
7. Do not let Choreographer catch-up bursts permanently increase audio latency.
8. Flush native/core-facing host queues on pause/resume/reset.
9. Preserve all sealed battle/HUD/Showdown rules; FIX4 is audio/pacing only.

## Promotion gate
FIX4 may not advance to M6A3 until THOR confirms:
- correct pitch,
- no progressive audio delay,
- no persistent crackle,
- stable normal game speed,
- pause/resume does not reintroduce stale audio,
- original menus remain unchanged.
