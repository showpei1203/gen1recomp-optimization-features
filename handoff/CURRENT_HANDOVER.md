# SOULGOLD M6X1R2 — Final Showdown Presentation Authority

Status: BUILD/STATIC PASS; AYN THOR R2 runtime regression gate PENDING.
Branch: feature/soulgold-showdown-m6x1
Pinned SoulGold: 671b62f421b2356961274fcb6f199d6843017f16
Pinned mGBA: 507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6

## Sealed baseline
- M1.4 mGBA single-clock audio remains SEALED.
- M6X0 remains REJECTED / diagnostic baseline only.
- M6X1 registry/audio repair remains SEALED: EWRAM registry sync after retro_run(), effective ~65536 stereo-frame/s source authority, no live latency source-sample deletion.
- FRONT rollout and 901-species expansion remain BLOCKED.

## Why R2 exists
R1 AYN THOR runtime exposed two presentation regressions:
1. Player Showdown BACK flickers when switching Battle command <-> MOVE command.
2. Stat-decrease presentation appears segmented/blocky instead of a continuous effect.

## R2 root causes
1. Android bridge race: syncBridge() transiently set gBridgeFresh=false while the UI compositor could sample it, producing a one-display-frame proxy loss.
2. R1 did not fully restore the accepted Showdown presentation-ownership/lifecycle chain. native visibility and presentation visibility must be distinct, especially across monbg.
3. Provider animation used Android uptime instead of ROM/mGBA frame authority.
4. Stat overlay clipping was performed after display scaling, magnifying clip quantization into visible blocks.

## Final Showdown authority chain restored
- M2R5D: presentation ownership; native-visible vs presentation-visible semantics.
- M2R11E: player body/HUD bounce decoupling; lower dialogue/menu final Z authority.
- M2R12G: healthbox ABI safety; no host raw BattleHealthboxInfo stride writes.
- M3S0/M3S1: provider generation identity, first-visible epoch, gap-safe lifecycle and teardown.

## R2 implementation
- Bridge ABI v3.
- Proxy exports presentationVisible, nativeVisible, monBgActive and spriteId generation identity.
- Android uses a last-known-good bridge snapshot. Beginning the next core-frame sync no longer removes the drawable snapshot.
- Showdown provider animation clock is ROM-frame based, not SystemClock.uptimeMillis().
- True species/sprite-generation changes reset presentation epoch; ordinary command UI transitions do not.
- Provider-owned monbg suppresses native Pokémon pixel copies into BG1/BG2 while external presentation remains visible.
- Stat/body/lower UI are composited at native mGBA framebuffer resolution first, then the finished frame is scaled once.
- BOUNCE_MON remains removed; BOUNCE_HEALTHBOX remains native.
- x2/y2 remain battler-animation authority.
- Host-side raw healthbox ABI writes remain forbidden.

## Permanent regression validator
M6X1R2 validation runs before ROM/APK build and checks bridge v3, native/presentation visibility split, sprite generation identity, monbg suppression, stat external path, BOUNCE_MON removal, BOUNCE_HEALTHBOX preservation, x2/y2 preservation, last-known-good snapshot use, ROM-frame animation clock, first-visible epoch, gap release, native-resolution composite, and absence of raw healthbox ABI writes.

## Canonical R2 build evidence
- GitHub Actions Run #9: 33864081085
- build head: 6a96944d054bdb15c11a00904986e4c57f78e881
- ROM compile: PASS
- permanent R2 presentation validator: PASS
- bridge symbol / exact 32 MiB: PASS
- SGXP build: PASS
- patched mGBA ARM64: PASS
- Android contract audit: PASS
- APK assembleDebug: PASS
- test-kit/evidence upload: PASS
- final Persist compact authority step: FAIL only after artifact upload; tracked generated_bridge.h still held the pre-R2 address. Branch has now been corrected to the R2 address 0x02002ad4 to prevent recurrence.

## Binary authority from Run #9
- gM6X1ExternalBridge: 0x02002ad4
- ROM bytes: 33,554,432
- ROM SHA-256: 9030606040c40e81dff820489dcd9cd57ea4619e7c1a3b5bfeb7e702c9018c0e
- SGXP SHA-256: d149baa6e0c3a9cb57a28841f1687c825090f62234a82f5707a588f3d9313ccb
- APK SHA-256: 857e88e09e21d0b0e93223f20cd0641c3bebaae3cf9b20ee1f245131104eab07

## Locked next AYN THOR runtime gate
ONLY Sprigatito player BACK.
1. Battle command <-> MOVE command repeated transitions: zero Showdown/native flicker.
2. Stat-decrease effect: continuous presentation; no block/stripe segmentation artifact.
3. First visible battler frame: Showdown immediately; no native flash.
4. HUD/dialogue/monbg/stat layering remains correct; no gray ghost edge and no Pokémon-body HUD coupling.
5. Registry/audio sealed metrics remain passing: external_registry_syncs > 0, external_overlay_frames > 0, external_overlay_failures = 0, observed source rate ~65536 stereo frames/s, latency_recovery_dropped_source_samples = 0, audio_underrun_count = 0 and no persistent crackle.

Do not unlock FRONT or broad roster expansion until this R2 device gate is accepted.
