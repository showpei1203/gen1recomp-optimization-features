# M6X1 handover

Status: BUILD/STATIC CANDIDATE ONLY. Runtime PASS requires the locked AYN THOR Sprigatito player-BACK gate.
Branch: feature/soulgold-showdown-m6x1

## Authority / baseline
- pinned SoulGold: 671b62f421b2356961274fcb6f199d6843017f16
- pinned mGBA: 507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6 plus M6X1-only libretro EWRAM exposure patch; no clock/audio-core changes.
- M6X0: REJECTED / diagnostic baseline only.
- M1.4 mGBA single-clock audio: FORMAL PASS / SEALED authority.
- M6X0 AYN THOR authority: external_registry_syncs=0 and external_overlay_frames=0; latency recovery deleted roughly half of generated source PCM.

## M6X1 fixes
1. CI resolves the real pinned SoulGold outputs Soulgold.elf / Soulgold.gba, resolves gM6X1ExternalBridge from the freshly built ELF, verifies its EWRAM address, then freezes an exact 33,554,432-byte ROM.
2. The pinned mGBA libretro API did not expose RETRO_MEMORY_SYSTEM_RAM. M6X1 adds a minimal frontend-facing export of GBA EWRAM (0x02000000, 0x40000 bytes) only; emulation clock and audio core are untouched.
3. Android writes and reads back the EWRAM provider registry immediately after every retro_run() frame using RETRO_MEMORY_SYSTEM_RAM.
4. ROM publishes proxy state after AnimateSprites and before BuildOamBuffer; provider-owned native OBJ is hidden only for that OAM snapshot and immediately restored.
5. libretro audio_batch count is stereo frames; native PCM queue and Java drain/resampler counts are interleaved int16 samples. The callback therefore expands frames * 2 exactly once.
6. mGBA FPS remains the sole emulation clock. Reported 32768 Hz remains telemetry; effective source authority is about 65536 stereo frames/s for this pinned runtime.
7. Live latency recovery may not delete PCM. Sink DRC remains bounded to ±0.5%.

## Canonical build evidence
- GitHub Actions run: 33850743516
- build head: 3ed6973e6461ef385e139c2bac0b6adefa548c78
- all build, bridge, patched mGBA, static audit, APK, package and artifact-upload steps PASS.
- final automated authority-persist step failed only after artifacts were already uploaded; the resolved generated_bridge.h and this authority set were therefore persisted manually on the same branch without rebuilding.
- resolved gM6X1ExternalBridge: 0x02002ac8
- ROM bytes: 33,554,432

## Locked first physical-device gate
- ONLY Sprigatito player BACK Showdown sprite.
- FRONT rollout: BLOCKED.
- Other roster acceptance / 901-species expansion: BLOCKED.
- CI/build success is not runtime success.

## Required runtime evidence
- diagnostics/M6X1_REGISTRY_AUDIO_REPORT.json from AYN THOR.
- external_registry_syncs > 0
- external_overlay_frames > 0
- external_overlay_failures = 0
- source_observed_rate_from_core_frames approximately 65536 stereo frames/s
- latency_recovery_dropped_source_samples = 0
- subjective crackle/noise absent and audio_underrun_count = 0

ROM_SHA256=6de15ec859049a509d81e1291ee98d71669bfaee820fe15cf4d30f36a9d02cf8
PACK_SHA256=57959d41b44103106147a32b9aa1b0a009aba6e88561c5c1807d59a7dfad31a7
APK_SHA256=6b5aa5e0844264d42acf801d4b9ca3582780dbfb1398d9f38c75091d544e8ad1
