# SOULGOLD M6X1R3 — Native SoulGold Stat Fidelity Authority

Status: BUILD/STATIC PASS; AYN THOR R3 stat-fidelity runtime gate PENDING.
Branch: feature/soulgold-showdown-m6x1
Pinned SoulGold: 671b62f421b2356961274fcb6f199d6843017f16
Pinned mGBA: 507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6
Canonical R3 CI: Run #13 / 33867021188

## Sealed baseline
- M1.4 mGBA single-clock audio remains SEALED.
- M6X0 remains REJECTED / diagnostic baseline only.
- M6X1 registry/audio bridge remains SEALED.
- M6X1R2 bridge v3, last-known-good snapshot, ROM-frame provider clock, presentation lifecycle, HUD bounce decoupling, monbg semantics, x2/y2 authority and lower-UI Z authority remain sealed.
- FRONT rollout and 901-species expansion remain BLOCKED.

## Why R3 exists
AYN THOR R2 runtime showed the stat bridge was actually active (`stat_native_composite_frames=87`) but the user still rejected the stat-decrease visual. Therefore the problem was not registry/proxy delivery. The historical M2/M6X1R2 implementation itself was only an approximation: moving hardcoded color strips clipped to the Showdown body.

That historical strip/tint approximation is now REJECTED and permanently forbidden.

## R3 native stat authority
R3 generates Android stat textures directly from the pinned SoulGold source directory `graphics/battle_anims/stat_change`.

Build-time source facts embedded in the APK manifest:
- tiles.png: 128x32 indexed-P
- tile count: 64
- increase.bin / decrease.bin: native 32x32 GBA tilemaps
- generated textures: 16 (increase/decrease x attack, defense, accuracy, speed, evasion, sp_attack, sp_defense, multiple)
- output texture size: 256x256
- tile base: 0 for increase and decrease
- native decrease BG1 X offset: 64
- palette index 0: transparent

## R3 compositor
- ROM remains authoritative for statActive/statBattler/statDecrease/statPal/statSharp/statBlend/statScroll.
- Android chooses the exact SoulGold-generated pattern.
- BitmapShader repeats the native BG texture.
- statScroll drives BG Y and decrease uses native BG X=64.
- statBlend drives alpha as blend / 16.
- Current Showdown frame alpha is applied with DST_IN as the battler silhouette mask.
- Body/stat/lower UI are composed at native mGBA framebuffer resolution and scaled once at the end.

## Permanently forbidden regressions
- stripe / venetian-blind stat approximation
- clipRect stripe segmentation
- hardcoded RGB stat tint tables / PorterDuffColorFilter stat fake
- Android uptime as provider animation clock
- transient gBridgeFresh blank frames
- provider-owned native 64x64 pixels inside stat/monbg presentation
- BOUNCE_MON action-menu coupling
- host raw BattleHealthboxInfo ABI stride writes

## R3 permanent validator
The build gate requires:
- all M2R5D/M2R11E/M2R12G/M3S1 lifecycle and layering rules,
- bridge v3 and last-known-good snapshot,
- ROM-frame animation clock,
- complete 16-texture native stat asset set + manifest,
- BitmapShader native pattern,
- DST_IN Showdown alpha mask,
- ROM scroll/blend authority,
- explicit absence of the old stripe/tint approximation,
- FRONT still blocked.

## Canonical R3 build evidence
GitHub Actions Run #13 / 33867021188:
- native stat asset generation: PASS
- R3 permanent validator: PASS
- SoulGold ROM compile: PASS
- bridge symbol / exact 32 MiB: PASS
- SGXP build: PASS
- patched mGBA ARM64: PASS
- Android contract audit: PASS
- APK assembleDebug: PASS
- test-kit upload: PASS
- evidence upload: PASS
- final compact-authority persistence housekeeping: FAIL after artifacts were already uploaded; does not invalidate the R3 binaries.

## Canonical binary authority
- gM6X1ExternalBridge: 0x02002ad4
- ROM bytes: 33,554,432
- ROM SHA-256: 9030606040c40e81dff820489dcd9cd57ea4619e7c1a3b5bfeb7e702c9018c0e
- SGXP SHA-256: 0915766512c3c704c640b95242a5fe184219a12808981e86d6729e99309724bc
- APK SHA-256: 3452c642ba2dbeb138b5ac1b5f55876e55fe25985642c8f17988fe27799a77c1

## Locked next AYN THOR gate
ONLY Sprigatito player BACK.
1. Trigger stat decrease at least 2–3 times.
2. Expected: the SoulGold native stat-change BG pattern scrolls/blends continuously inside the Showdown silhouette.
3. Forbidden: stripe/block segmentation, old native 64x64 silhouette, Showdown disappearance.
4. Battle command <-> MOVE command switching must remain flicker-free.
5. HUD/dialogue/monbg layering and audio must not regress.
6. START+SELECT runtime JSON should report:
   - presentation_semantics = M6X1_R3_NATIVE_SOULGOLD_STAT_FIDELITY
   - stat_render_mode = soulgold_bg1_tilemap_palette_scroll_showdown_alpha_mask
   - stat_native_pattern_frames > 0
   - stat_asset_failures = 0
   - registry/overlay/audio sealed metrics remain healthy.

If R3 visual fidelity is still wrong while the R3 stat counters pass, the next repair scope is ONLY shader phase / GBA BG scroll sign / blend fidelity. Do not reopen registry/audio and do not restore the rejected strip/tint approximation.
