# HANDOVER M6A0 — Android ARM64 / AYN THOR Readiness

M6A0 begins M6 platform work without pretending M5A3 runtime coverage has already passed.

Changes:
- portable SDL_GameController input + hotplug
- direct GBA A/B/L/R/Start/Select mapping
- left-stick D-pad fallback
- Android NDK arm64-v8a environment/cross-build readiness stage
- no Action Presentation changes
- no M5 formal seal claim
- no Android device runtime claim

Run desktop/current baseline as before, or use:
`tools\\soulgold_mgba\\START_M6A0_ANDROID_ARM64_READINESS.bat`
for the Android arm64 environment/cross-build gate.

Next: M6A1 SDLActivity/Gradle APK shell, while M5A3 runtime seal evidence remains an independent pending gate.
