# SoulGold M6A0 — Android ARM64 / AYN THOR Readiness Authority
Date: 2026-09-02

## Status
M6A0 starts platform work in parallel with the still-pending M5A3 runtime coverage gate.
It MUST NOT claim M5 FORMAL PASS and MUST NOT claim Android device runtime PASS.

## Goal
Prepare the existing original-first Showdown frontend for Android arm64-v8a / AYN THOR without changing SoulGold battle correctness or Action Presentation semantics.

## Input authority
- SoulGold/mGBA remains the only gameplay and action-presentation authority.
- M5A3 runtime seal remains pending normal-play evidence.
- Desktop keyboard input remains available for QA only.
- Portable controller input uses SDL_GameController.

## M6A0 changes
1. Add SDL_GameController discovery at startup.
2. Support controller hotplug/removal and failover without touching gameplay state.
3. Map GBA controls explicitly:
   - GBA A -> SDL controller A
   - GBA B -> SDL controller B
   - GBA L/R -> shoulder L/R
   - START -> START
   - SELECT -> BACK
   - D-pad -> D-pad
4. Left analog stick may act as D-pad with a fixed threshold. It does not create analog gameplay.
5. Add Android NDK arm64-v8a readiness stage.
6. Cross-compile the frontend translation unit when an Android NDK is available.
7. Attempt pinned mGBA libretro arm64-v8a build when the Android environment is available.
8. APK/SDLActivity packaging is deferred to M6A1.

## New permanent rules
- R-SD-126 PORTABLE_INPUT_USES_SDL_GAMECONTROLLER_WITH_DESKTOP_KEYBOARD_FALLBACK
- R-SD-127 CONTROLLER_HOTPLUG_MUST_NOT_RESET_OR_MUTATE_GAMEPLAY_STATE
- R-SD-128 GBA_AB_LR_START_SELECT_CONTROLLER_MAPPING_IS_EXPLICIT
- R-SD-129 LEFT_ANALOG_DPAD_FALLBACK_USES_FIXED_THRESHOLD_NO_ANALOG_GAMEPLAY
- R-SD-130 ANDROID_ARM64_GATE_USES_NDK_CMAKE_TOOLCHAIN_AND_ARM64_V8A
- R-SD-131 CROSS_COMPILE_READINESS_IS_NOT_ANDROID_DEVICE_RUNTIME_PROOF
- R-SD-132 M5_FORMAL_SEAL_REMAINS_PENDING_M5A3_RUNTIME_EVIDENCE
- R-SD-133 ACTIVE_M6A0_LAUNCHER_DECLARED_STAGE_MUST_EXIST_IN_SAME_PACKAGE
- R-SD-134 ANDROID_STORAGE_PATHS_REMAIN_CALLER_SUPPLIED_NO_HARDCODED_SHARED_STORAGE

## Promotion
M6A1 may create an SDLActivity/Gradle APK shell only after M6A0 source/toolchain readiness is structurally sound. Device performance, suspend/resume, controller feel, storage permission behavior and second-screen behavior still require AYN THOR evidence later.
