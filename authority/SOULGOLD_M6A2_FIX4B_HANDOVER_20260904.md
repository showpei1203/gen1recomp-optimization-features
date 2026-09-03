# SoulGold M6A2 FIX4B — HANDOVER

Date: 2026-09-04
Project: Pokémon SoulGold Showdown-first / Android ARM64 / AYN THOR
Branch: `feature/soulgold-showdown-m6a2`
Baseline after CI artifact persistence: `ab76d4d1f387edcf635997320c24b690c9c4e9f4`

## Runtime status

- M6A1 THOR platform smoke: USER PASS
- M6A2 original ROM boot: PASS
- M6A2 FIX1 audio: FAIL
- M6A2 FIX2 worker architecture: REJECTED
- M6A2 FIX3 Choreographer + pending audio: FAIL
- M6A2 FIX4A hard audio-clock master: USER FAIL
  - video visibly laggy
  - audio laggy
  - SE reaction speed normal
- M6A2 FIX4B CI/build: PASS
- M6A2 FIX4B THOR runtime: PENDING USER TEST
- Showdown Android compositor: still deferred

## FIX4A root cause

FIX4A ran `nativeRunFrame()` and `AudioTrack.WRITE_BLOCKING` sequentially on the same audio-priority thread. Android sink blocking therefore stalled the next mGBA frame and made video/gameplay inherit audio-device stalls. This architecture is permanently rejected.

## FIX4B architecture

- Dedicated mGBA core scheduler using monotonic time and core-reported FPS.
- Dedicated audio-priority AudioTrack sink thread.
- Blocking AudioTrack writes cannot block core advancement.
- Explicit 32768-ish mGBA source -> Android native output-rate resampling.
- Source-queue feedback drives bounded DRC, max +/-0.5%.
- No long catch-up bursts after scheduling stalls.
- Exceptional stale-audio growth is discarded toward target latency instead of slowing the whole game.
- Choreographer only presents latest framebuffer.
- No Showdown overlay in this APK; native SoulGold presentation remains authority.

## CI evidence

Workflow run: `33816492258`
Job: `100849687710`
Artifact: `SOULGOLD_M6A2_FIX4B_THOR_DECOUPLED_DRC`
Artifact ID: `9916758242`
Artifact archive digest: `sha256:008a731da08010b059e952a701623f703d42aa4c230fde5bb4c0ac8de64d2e1b`

APK:
- file: `SOULGOLD_M6A2_FIX4B_THOR_DECOUPLED_DRC.apk`
- bytes: `750999`
- sha256: `0288550bd37a00653acd78811bf41dfb3e49ac699068182b9f6cc23c62ec94f2`
- ABI: arm64-v8a
- pinned mGBA: `507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6`
- ROM included: false

All workflow steps passed, including mGBA ARM64 build, FIX4B architecture validation, Gradle APK build, native-library APK verification, artifact upload and persistent transport.

## New regression rules

R-SD-163 through R-SD-170 are defined in:
`authority/SOULGOLD_M6A2_FIX4B_DECOUPLED_CORE_DRC_AUTHORITY_20260904.md`

Most important prohibitions:

1. Never restore `nativeRunFrame -> WRITE_BLOCKING -> next nativeRunFrame` as one thread.
2. Never fix BGM/pacing by simply inflating audio buffers when SE latency is already acceptable.
3. Never allow multi-second stale PCM accumulation to dictate game speed.
4. Choreographer never advances emulation.
5. CI PASS is not THOR runtime PASS.

## THOR acceptance test

Test normal play for at least several minutes and check:

1. video/gameplay speed and smoothness,
2. BGM pitch/speed and crackle,
3. whether A/V delay grows over time,
4. SE response remains immediate,
5. Pokémon / Party / Summary native slide transitions remain intact,
6. app background -> resume does not replay stale sound.

Start + Select writes:
`M6A2_FIX4B_DECOUPLED_DRC_REPORT.json`

Useful report fields:
- `core_deadline_rebases`
- `core_max_late_ms`
- `source_queue_peak_samples`
- `source_queue_target_samples`
- `source_queue_hard_samples`
- `drc_rate_adjust_current/min/max`
- `latency_recovery_dropped_source_samples`
- `estimated_sink_latency_ms`
- `audio_underrun_count`

## Next decision

- If FIX4B restores normal gameplay/video and stable audio: promote M6A2 runtime baseline, then proceed to M6A3 battle-only Showdown compositor.
- If video is normal but audio remains wrong: keep core scheduler sealed and modify only audio DRC/output path, likely moving toward Oboe/AAudio.
- If video still lags while audio is stable: investigate framebuffer copy/presentation cadence separately; do not change audio clock again.
