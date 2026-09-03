# SoulGold M6A2 FIX4B — Decoupled Core Clock + Audio DRC Authority

Date: 2026-09-04
Branch: `feature/soulgold-showdown-m6a2`

## User runtime evidence

AYN THOR test of M6A2 FIX4A:

- audio still lagged,
- video also became visibly laggy,
- SE reaction speed remained normal.

This is a runtime FAIL for FIX4A.

## Root cause

FIX4A executed the whole emulator on an audio-priority worker with the sequence:

`nativeRunFrame() -> drain/resample -> AudioTrack.WRITE_BLOCKING -> next nativeRunFrame()`

That made every mGBA frame wait for the Android audio sink. Any AudioTrack blocking interval therefore stalled gameplay/video as well. Low-latency SE response indicates the sink itself is not the principal latency problem; coupling the sink's blocking behavior directly to core advancement is.

FIX4A corrected explicit sample-rate conversion and removed the FIX3 long pending queue, but it over-corrected by making audio backpressure a hard per-frame emulation clock.

## Reference architecture conclusion

Both mGBA frontend sync design and RetroArch use a distinction between:

1. core/emulation advancement,
2. audio device consumption,
3. bounded feedback/backpressure between them.

Audio buffer level may correct the rate, but a single blocking device write must not directly freeze the next emulation frame.

## FIX4B architecture

- mGBA core runs on a dedicated monotonic scheduler at the core-reported FPS.
- No catch-up burst: if the scheduler falls multiple frames behind, deadline is rebased instead of blasting several `retro_run()` calls.
- Audio runs on a separate audio-priority sink worker.
- Source PCM is explicitly resampled to Android's native output rate.
- A small bounded source queue is used as the sync feedback signal.
- Dynamic rate control adjusts the resampler by at most +/-0.5%, matching the same class of correction used by RetroArch DRC.
- If a platform stall grows source latency beyond the hard safety window, stale source PCM is discarded back toward the target instead of slowing the entire game for seconds to replay obsolete audio.
- Choreographer remains presentation-only and never advances emulation.
- Original SoulGold menu/battle presentation remains ROM authority.

## Regression rules

- **R-SD-163 AUDIO_WRITE_MUST_NOT_BLOCK_CORE_ADVANCEMENT**: `AudioTrack.write()` may block only the audio sink worker, never the mGBA core scheduler.
- **R-SD-164 CORE_PACING_IS_MONOTONIC_MGBA_FPS_WITHOUT_CATCHUP_BURSTS**: core timing follows mGBA FPS; long scheduling stalls rebase the deadline rather than generating burst frames.
- **R-SD-165 AUDIO_SYNC_USES_BOUNDED_DRC_NOT_UNBOUNDED_QUEUEING**: audio queue occupancy controls a bounded resampler correction; it must not create multi-second stale PCM queues.
- **R-SD-166 DRC_CORRECTION_IS_BOUNDED_TO_HALF_PERCENT**: normal dynamic rate correction is clamped to +/-0.5%.
- **R-SD-167 STALE_AUDIO_RECOVERY_PREFERS_BOUNDED_DROP_OVER_GLOBAL_SLOWDOWN**: after exceptional sink stalls, stale PCM may be dropped toward the target latency; gameplay must not be globally slowed to replay old audio.
- **R-SD-168 CHOREOGRAPHER_IS_PRESENTATION_ONLY**: Android VSYNC copies/presents the latest completed framebuffer only.
- **R-SD-169 FIX4A_HARD_AUDIO_CLOCK_IS_REJECTED**: never restore `nativeRunFrame -> WRITE_BLOCKING -> next nativeRunFrame` as the primary runtime loop.
- **R-SD-170 SE_LOW_LATENCY_OBSERVATION_IS_A_DIAGNOSTIC_GATE**: future changes must not solve BGM/pacing by inflating sink latency when SE response is already acceptable.

## Acceptance boundary

FIX4B requires THOR runtime validation. CI/build success is not device PASS.

Primary acceptance checks:

1. video/gameplay speed normal,
2. BGM/audio speed normal,
3. no progressive A/V delay over at least 5 minutes,
4. SE response remains immediate,
5. original menu transitions remain intact,
6. report shows bounded source queue, small DRC correction, and no persistent stale-audio recovery drops during normal play.
