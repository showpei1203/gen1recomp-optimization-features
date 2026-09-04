# SoulGold M6X1 Registry + Audio Fix Authority

Status: BUILD/STATIC CANDIDATE ONLY. AYN THOR runtime acceptance is still required.

M6X0 is REJECTED / diagnostic baseline only: registry sync never occurred and audio latency recovery deleted roughly half of generated source PCM. M1.4 mGBA single-clock audio remains SEALED authority.

## Proven build facts
- Canonical GitHub Actions run: 33850743516
- Build head: 3ed6973e6461ef385e139c2bac0b6adefa548c78
- SoulGold revision: 671b62f421b2356961274fcb6f199d6843017f16
- mGBA revision: 507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6
- gM6X1ExternalBridge: 0x02002ac8 in EWRAM
- ROM: exact 33,554,432 bytes, SHA256 6de15ec859049a509d81e1291ee98d71669bfaee820fe15cf4d30f36a9d02cf8
- SGXP SHA256: 57959d41b44103106147a32b9aa1b0a009aba6e88561c5c1807d59a7dfad31a7
- APK SHA256: 6b5aa5e0844264d42acf801d4b9ca3582780dbfb1398d9f38c75091d544e8ad1
- ROM build, symbol/32 MiB sealing, Showdown pack, patched mGBA ARM64, static contract audit, Android APK build, package creation and artifact uploads all PASS.

## Registry fix
Pinned mGBA's libretro implementation did not expose RETRO_MEMORY_SYSTEM_RAM through retro_get_memory_data/size. M6X1 adds only a frontend-facing GBA EWRAM export at 0x02000000, size 0x40000 bytes. mGBA timing and audio core are untouched. Android rewrites and reads back the host provider registry immediately after every retro_run().

## Audio fix
libretro audio_batch count is stereo frames. Native PCM queue and Java drain/resampler units are interleaved int16 samples. M6X1 expands frames to samples with frames*2 exactly once. mGBA FPS stays the sole emulation clock. Reported 32768 Hz remains telemetry while this pinned runtime's effective source authority is approximately 65536 stereo frames/s. Live latency recovery must not delete source PCM; bounded sink DRC remains allowed.

## Locked physical-device gate
Only Sprigatito player BACK Showdown sprite is accepted for the first AYN THOR gate. FRONT rollout and 901-species expansion remain BLOCKED.

Runtime PASS requires M6X1_REGISTRY_AUDIO_REPORT.json showing external_registry_syncs > 0, external_overlay_frames > 0, external_overlay_failures = 0, source_observed_rate_from_core_frames approximately 65536 stereo frames/s, latency_recovery_dropped_source_samples = 0, audio_underrun_count = 0, plus no persistent crackle/noise and no native sprite flash before the Sprigatito BACK Showdown sprite.

CI/build success must never be promoted to runtime success without that physical-device evidence.
