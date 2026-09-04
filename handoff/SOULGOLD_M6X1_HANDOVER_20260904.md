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
1. CI resolves Soulgold.elf / Soulgold.gba, resolves gM6X1ExternalBridge from the freshly built ELF, verifies its EWRAM address, then freezes an exact 33,554,432-byte ROM.
2. Pinned mGBA did not expose RETRO_MEMORY_SYSTEM_RAM. M6X1 adds only a libretro-facing GBA EWRAM export at 0x02000000 / 0x40000 bytes. mGBA timing and audio core remain untouched.
3. Android rewrites and reads back the provider registry after every retro_run().
4. audio_batch count is stereo frames; native/Java PCM buffers are interleaved int16 samples. Frames are expanded to frames*2 exactly once.
5. Reported 32768 Hz stays telemetry; effective source authority is approximately 65536 stereo frames/s. Live latency recovery sample deletion is prohibited.

## Canonical build
- run: 33850743516
- build head: 3ed6973e6461ef385e139c2bac0b6adefa548c78
- bridge address: 0x02002ac8
- ROM exact size: 33,554,432 bytes
- ROM SHA256: 6de15ec859049a509d81e1291ee98d71669bfaee820fe15cf4d30f36a9d02cf8
- PACK SHA256: 57959d41b44103106147a32b9aa1b0a009aba6e88561c5c1807d59a7dfad31a7
- APK SHA256: 6b5aa5e0844264d42acf801d4b9ca3582780dbfb1398d9f38c75091d544e8ad1
- build/bridge/mGBA/audit/APK/package/upload steps: PASS
- automated authority persist: housekeeping FAIL after artifact upload; compact authority was persisted manually on this same branch.

## Locked first physical-device gate
- ONLY Sprigatito player BACK Showdown sprite.
- FRONT rollout BLOCKED.
- Other roster acceptance / 901-species expansion BLOCKED.
- CI/build success is not runtime success.

## Runtime PASS contract
- AYN THOR diagnostics/M6X1_REGISTRY_AUDIO_REPORT.json
- external_registry_syncs > 0
- external_overlay_frames > 0
- external_overlay_failures = 0
- source_observed_rate_from_core_frames approximately 65536 stereo frames/s
- latency_recovery_dropped_source_samples = 0
- audio_underrun_count = 0
- no persistent crackle/noise
- Sprigatito player BACK is Showdown sprite on first visible battler frame with no native flash
