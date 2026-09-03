# SoulGold M6A2 FIX3 — Conservative Audio/Pacing Authority

Date: 2026-09-03
Branch: `feature/soulgold-showdown-m6a2`

## Trigger

AYN THOR runtime feedback established that M6A2 FIX2 audio was materially worse than FIX1. The independent emulation thread plus blocking audio consumer introduced a regression and is rejected as an authority design.

The prior observation about original Pokémon/Party/Summary slide animations was clarified separately: the user was referring to the modified Showdown build, not the original ROM currently running in M6A2. FIX3 therefore makes no menu-presentation changes.

## FIX3 policy

1. Reject the FIX2 independent emulation/audio worker architecture.
2. Return `retro_run()` to the Android Choreographer callback thread, but do not equate one display callback with one emulated frame.
3. Use Choreographer timestamps only as a wall-clock source and accumulate mGBA frame budget from `nativeFps()`.
4. Keep `AudioTrack.WRITE_NON_BLOCKING`, but retain unwritten PCM samples in a persistent host ring instead of discarding partial writes.
5. Prefill audio before `AudioTrack.play()` to reduce startup underrun/crackle.
6. Preserve original SoulGold menu/presentation code untouched in this audio fix.
7. Runtime telemetry must report effective generated source rate, reported source rate, Android native output rate, AudioTrack rate, partial/zero writes, host pending depth, native queue depth, and native dropped samples.

## Regression IDs

- R-SD-149 `FIX2_AUDIO_WORKER_ARCHITECTURE_REJECTED`
- R-SD-150 `CORE_PACING_USES_CHOREOGRAPHER_TIMESTAMP_ACCUMULATOR`
- R-SD-151 `PARTIAL_AUDIO_WRITES_MUST_BE_RETAINED`
- R-SD-152 `AUDIO_START_REQUIRES_PREFILL`
- R-SD-153 `AUDIO_FIX_MUST_NOT_CHANGE_SOULGOLD_MENU_PRESENTATION`
- R-SD-154 `EFFECTIVE_GENERATED_SOURCE_RATE_IS_REPORTED`

## Build evidence

GitHub Actions run: `33749871110`
Artifact: `SOULGOLD_M6A2_FIX3_THOR_AUDIO_PACING`
Artifact ID: `9891146341`
Artifact archive digest: `sha256:198a2b09b6de4150fa0c2eeea93d218b6f232a5667608e97a037660f8f2e916a`

CI results:
- ARM64 mGBA libretro build: PASS
- FIX3 contract validation: PASS
- Android debug APK build: PASS
- APK native-library presence validation: PASS
- Artifact upload: PASS
- Compact artifact persistence step: PASS

## Runtime status

AYN THOR FIX3 audio runtime remains `PENDING DEVICE TEST` until user validation.
Static/CI success must not be promoted to device-runtime PASS.
