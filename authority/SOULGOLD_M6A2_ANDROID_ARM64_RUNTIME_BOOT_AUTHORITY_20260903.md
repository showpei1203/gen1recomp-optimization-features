# SoulGold M6A2 Android ARM64 Runtime Boot Authority

## Scope
M6A2 is the first gameplay-capable Android/AYN THOR boot shell. It packages a pinned mGBA libretro ARM64 core and a project-owned JNI libretro frontend. The APK does **not** contain a commercial ROM. The user selects their own `.gba` backup with Android SAF.

## Authority split
- SoulGold/GBA gameplay timing and video/audio are produced by mGBA/libretro.
- Android owns presentation surface, AudioTrack, controller events, SAF ROM import, and app-scoped save persistence.
- M5 SoulGold-first action presentation semantics are not reinterpreted here.
- Showdown overlay integration is explicitly deferred beyond M6A2 Runtime Boot.

## Device target
- ABI: arm64-v8a
- minSdk: 24
- target/compileSdk: 35
- Confirmed prior device: AYN Thor / Android API 33 via M6A1 user acceptance.

## Runtime path
1. APK launches and dlopens bundled `libmgba_libretro.so`.
2. User selects a `.gba` file with system picker.
3. App copies it into private app storage and passes ROM bytes to `retro_load_game`.
4. Choreographer drives `retro_run` at display cadence.
5. libretro video frames are copied to a pixel-perfect Android View.
6. libretro audio is streamed to Android AudioTrack.
7. THOR controller events are mapped to libretro joypad IDs.
8. Save RAM is restored on boot and flushed every five seconds / app pause.

## Regression contracts
- R-SD-139: M6A2 APK MUST NOT bundle a commercial GBA ROM.
- R-SD-140: mGBA core MUST be packaged as ARM64 `libmgba_libretro.so` and loaded through the libretro API.
- R-SD-141: ROM boot MUST use user-selected SAF content copied into app-scoped storage.
- R-SD-142: Controller mapping MUST preserve M6A1 A/B/L/R/Start/Select/D-pad semantics; left analog remains D-pad fallback.
- R-SD-143: Save RAM MUST remain app-scoped and be restored/flushed without requiring broad storage permission.
- R-SD-144: CI build success is APK/build evidence only; AYN THOR runtime PASS requires device evidence.
- R-SD-145: Showdown overlay is NOT claimed integrated in M6A2 Runtime Boot.

## Acceptance
Build/packaging PASS requires CI to compile the pinned mGBA core, compile the JNI frontend, package both ARM64 libraries, and produce a SHA-256'd APK.
Device runtime remains PENDING until the user installs on THOR, selects their ROM, reaches live GBA video, obtains audio/controller response, and returns runtime evidence.
