# SOULGOLD M6X1R5 — Opponent FRONT Canary

Status: R4 RUNTIME PASS / SEALED. R5 BUILD + DEVICE GATE PENDING.
Branch: feature/soulgold-showdown-m6x1
Pinned SoulGold: 671b62f421b2356961274fcb6f199d6843017f16
Pinned mGBA: 507061afd70489a0c2ffc8ba26d8f9b53d6cf7d6

## R4 physical-device acceptance
The user physically tested M6X1R4 on AYN THOR and reported the two remaining R3 regressions fixed. R4 is therefore promoted from BUILD/STATIC candidate to RUNTIME PASS authority.

R4 sealed repairs:
- stat-change effect stays inside the Showdown silhouette using Showdown-alpha-first + SRC_IN full-pattern composition; no left-edge residue.
- battle teardown retains provider ownership on the exact native sprite generation until that OBJ is actually gone; no final native battler flash.
- player BACK Showdown lifecycle, battle/MOVE switching, lower dialogue/UI Z, monbg semantics, HUD bounce decoupling and stat presentation remain accepted.
- registry/audio remain sealed and are not reopened.

Canonical R4 build: GitHub Actions Run #14 / 33963616919
Canonical R4 binary head: 248c1592a5c0eb0729b813a85536dcdc422f1430
R4 bridge: 0x02002af4
R4 ROM SHA-256: bde1f153fda6da8fb096cd720326542be0a09a0dde11ec572dccef1a3102e9e2
R4 SGXP SHA-256: 2342ab524fa6f6fb858a26b4791c8b75fd824902442da9ba446b6e6f7fbbf528
R4 APK SHA-256: fc0731f2d4f8c18c69618039fe51f3b37a7b490206425c2d7c855c87adbc90fb

## R5 scope
R5 opens opponent FRONT for exactly one canary species:
- species: 155
- name: Cyndaquil / 火球鼠
- source: Pokemon Showdown animated FRONT (`sprites/ani/cyndaquil.gif`)
- initial FRONT scale: 0.72

Existing nine BACK providers remain unchanged. Broad FRONT rollout and 901-species expansion remain BLOCKED.

## R5 architecture
ROM changes for FRONT registry are unnecessary: the bridge has always contained backCount/frontCount + back/front species tables, and M6X1_HostProvidesSpecies is side-aware. R4 provider-ownership teardown is also side-generic.

R5 therefore changes host/presentation only:
1. Android host stores and writes `gFrontProviders` into the bridge each core frame.
2. Host readback validates both BACK and FRONT provider counts.
3. New JNI `nativeSetFrontProviders`, `nativeGetOpponentProxy`, and FRONT count telemetry.
4. SGXP parser reads `front_providers` and hard-rejects anything except the single #155 canary.
5. Enemy FRONT uses the same 14-field last-known-good proxy lifecycle, sprite-generation identity, ROM-frame animation clock, x+x2/y+y2 geometry, monbg semantics, R3/R4 native stat overlay and R4 teardown guard.
6. Enemy FRONT is composed before player BACK; lower battle dialogue/UI is restored after both.

## R5 permanent gate
New validator: `tools/validate_m6x1_r5_front_canary.py`
It must prove:
- all R4 sealed authority still exists,
- FRONT registry is actually written/read back,
- opponent proxy is side==1 and provider-gated,
- FRONT animation uses ROM frame authority,
- FRONT stat/monbg/generation lifecycle exists,
- opponent FRONT draws before player BACK,
- lower UI remains final authority,
- builder contains exactly one FRONT species (#155),
- 901/broad FRONT rollout remains blocked.

## Locked first R5 AYN THOR gate
Use a normal single battle where the opponent is Cyndaquil (#155).
Expected:
1. Enemy native battler is replaced by Showdown FRONT on its first visible battler frame; no old sprite flash.
2. Enemy Showdown FRONT follows native x2/y2 move/faint/send-out choreography without disappearing or detaching.
3. Enemy stat increase/decrease effect uses the native SoulGold pattern clipped to the Showdown silhouette.
4. Battle end has no native FRONT flash.
5. Player BACK remains exactly as R4 accepted.
6. Lower dialogue/menu stays above both external battlers.
7. Registry/overlay/audio sealed metrics do not regress.

R5 diagnostics should include:
- presentation_semantics = M6X1_R5_FRONT_CANARY
- external_pack_native_front_providers = 1
- external_bridge_front_count_readback = 1
- front_canary_species = 155
- external_front_overlay_frames > 0
- external_front_overlay_failures = 0
- external_front_active_species = 155 while active
- front_proxy_generation_changes > 0

## Known presentation watchpoint
Historical M2 authority used an alpha-masked player healthbox restoration above opponent FRONT. R5 deliberately does not reintroduce that ABI-sensitive path before the canary proves it is needed. If the physical canary shows enemy FRONT covering the player healthbox, the next repair scope is ONLY directional alpha-masked player-HUD restoration. Do not move the enemy sprite upward and do not restore a broad rectangular framebuffer region.

## Locked prohibitions
- Do not reopen audio/registry unless runtime evidence regresses.
- Do not restore stripe/tint stat approximation.
- Do not globally discard x2/y2.
- Do not unlock more FRONT species or the 901 roster before the #155 physical canary passes.
- CI/build success is not R5 runtime success.
