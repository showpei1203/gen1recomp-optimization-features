# HANDOVER M6A2

Candidate: SoulGold M6A2 Android ARM64 Runtime Boot
Date: 2026-09-03

Goal: first real AYN THOR gameplay-capable APK boot path using a user-supplied `.gba` ROM and bundled pinned mGBA libretro ARM64 core.

Important status:
- M6A1 AYN THOR platform smoke: USER VISUAL PASS (59.9 FPS, Odin Controller detected, audio/storage observed).
- M6A2 CI APK build: must be checked after workflow completion.
- M6A2 AYN THOR gameplay runtime: PENDING USER TEST.
- Showdown overlay inside Android APK: DEFERRED; do not claim PASS.
- M5A3 formal runtime seal remains independent/pending unless actual runtime evidence was supplied.

Test on THOR:
1. Install `SOULGOLD_M6A2_THOR_RUNTIME_BOOT.apk`.
2. Tap `選擇 SoulGold / GBA ROM` and select user's own `.gba` backup.
3. Confirm title/gameplay video appears.
4. Confirm A/B/D-pad/Start and audio.
5. Pause/resume app and confirm no crash; save path is app-scoped.
6. Start+Select writes `M6A2_THOR_RUNTIME_BOOT_REPORT.json`.

If boot succeeds, next milestone is M6A3 Android integration of the project Showdown presentation layer, preserving native SoulGold/mGBA timing authority.
