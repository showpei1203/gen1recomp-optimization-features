# SOULGOLD M6X1R4 — Edge Residue + Battle-End Teardown Guard

Status: BUILD/STATIC PASS; AYN THOR R4 runtime gate PENDING.
Branch: feature/soulgold-showdown-m6x1
Pinned SoulGold: 671b62f421b2356961274fcb6f199d6843017f16
Pinned mGBA: 507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6
Canonical R4 CI: Run #14 / 33963616919
Canonical binary head: 248c1592a5c0eb0729b813a85536dcdc422f1430

## Sealed baseline
- M1.4 mGBA single-clock audio remains SEALED.
- M6X1 registry/audio bridge remains SEALED.
- M6X1R2 bridge v3, last-known-good snapshot, ROM-frame provider clock, presentation lifecycle, HUD bounce decoupling, monbg semantics, x2/y2 authority and lower-UI Z authority remain sealed.
- M6X1R3 pinned-SoulGold native stat assets / tilemap / palette / scroll / blend remain sealed.
- Historical stripe/tint stat approximation remains REJECTED and forbidden.
- FRONT rollout and 901-species expansion remain BLOCKED.

## R3 device authority entering R4
AYN THOR report #3 established:
- external_registry_syncs=11067, failures=0
- external_overlay_frames=2260, failures=0
- stat_native_pattern_frames=87
- stat_asset_failures=0
- presentation_semantics=M6X1_R3_NATIVE_SOULGOLD_STAT_FIDELITY

Remaining R3 user-visible regressions:
1. Stat-decrease effect correctly follows the Showdown sprite but leaves a small residual animation on the LEFT side.
2. At battle end, the old/native battler sprite briefly flashes.

## R4 repair A — edge-safe stat alpha composition
R3 composed the native SoulGold pattern first and then used DST_IN with the Showdown bitmap inside a fractional saveLayer RectF. R4 changes only the alpha-composition order:
- draw the exact current Showdown frame alpha first,
- set the native stat-pattern paint to PorterDuff SRC_IN,
- paint the FULL stat rectangle through that alpha,
- explicitly reset the xfermode every frame.

R3 native assets, ROM statScroll, native decrease X offset and statBlend remain authoritative.

Permanent R4 gate forbids DST_IN for this stat mask, old stripe/clipRect approximation and hard-coded tint.

## R4 repair B — battle-end provider ownership latch
Battle teardown may clear/inactivate gBattleMons before the provider-owned native OBJ generation is destroyed. R4 therefore stores ROM-side provider ownership by exact battler sprite generation:
- valid
- species
- side
- spriteId

Ownership may bridge only an inactive/zero-species teardown gap on the SAME spriteId and only while the host provider table still confirms the latched species. A real nonzero replacement species or different generation releases ownership.

The software tick also captures the exact suppressed spriteId and restores that object after BuildOamBuffer without depending on a possibly changed gBattlersCount.

Permanent rule: a provider-owned native battler may not become visible in a final teardown OAM snapshot before its exact OBJ generation is actually gone.

## R4 build / static authority
GitHub Actions Run #14 / 33963616919:
- declaration-safe R4 patcher: PASS
- R4 permanent presentation validator: PASS
- native SoulGold stat assets: PASS
- SoulGold ROM compile: PASS
- bridge symbol / exact 32 MiB: PASS
- SGXP: PASS
- patched mGBA ARM64: PASS
- Android contract audit: PASS
- APK assembleDebug: PASS
- test-kit upload: PASS
- evidence upload: PASS
- compact-authority housekeeping step failed only after artifacts were uploaded; binary authority remains valid.

## Canonical R4 binary authority
- gM6X1ExternalBridge: 0x02002af4
- ROM bytes: 33,554,432
- ROM SHA-256: bde1f153fda6da8fb096cd720326542be0a09a0dde11ec572dccef1a3102e9e2
- SGXP SHA-256: 2342ab524fa6f6fb858a26b4791c8b75fd824902442da9ba446b6e6f7fbbf528
- APK SHA-256: fc0731f2d4f8c18c69618039fe51f3b37a7b490206425c2d7c855c87adbc90fb

Built APK inspection confirms:
- M6X1_R4_EDGE_TEARDOWN_GUARD
- stat_mask_mode=showdown_alpha_first_src_in_full_rect
- stat_edge_safe_frames telemetry
- battle_end_native_flash_guard telemetry
- all 16 R3 native stat textures + manifest remain packaged.

## Locked AYN THOR R4 gate
ONLY Sprigatito player BACK.
1. Trigger stat decrease 2–3 times: absolutely no residual stat effect outside any Showdown edge.
2. End several battles: absolutely no old/native battler sprite flash during teardown.
3. Battle command <-> MOVE command remains flicker-free.
4. HUD/dialogue/monbg layering remains correct.
5. Audio remains subjectively normal; do not reopen audio without an actual regression.
6. START+SELECT report should show:
   - presentation_semantics = M6X1_R4_EDGE_TEARDOWN_GUARD
   - stat_mask_mode = showdown_alpha_first_src_in_full_rect
   - stat_edge_safe_frames > 0 after stat animation
   - battle_end_native_flash_guard = rom_provider_ownership_latch
   - registry/overlay failures remain 0.

Do not unlock FRONT or broad roster expansion until this R4 physical-device gate is accepted.
