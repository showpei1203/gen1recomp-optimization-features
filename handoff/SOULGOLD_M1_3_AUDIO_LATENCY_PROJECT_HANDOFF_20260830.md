# Pokémon SoulGold mGBA Enhancement Project — Corrected Handoff
Date: 2026-08-30

## Product direction
- Base: Pokémon SoulGold Beta 1
- Runtime authority: mGBA pinned at `c65e8a3d4666b0ea68a01578232452f31b185332`
- ROM SHA-1: `d88b6a59802ccd442275ecbcfc9140fff34556dc`
- Target: Android ARM64 / AYN THOR
- Editions: PMD Animated Sprite Edition + Showdown Sprite Edition over one shared runtime
- Localization: Traditional Chinese `zh-Hant-TW`, English fallback
- External assets are not constrained by the 32 MiB GBA ROM ceiling

## Architecture split
mGBA owns CPU/BIOS/IRQ/DMA/timers/PPU/APU/save/RTC/timing.
Gen1 owns SoulGold state, external sprites, localization, host overlays, mods and second-screen/UI.
gbarecomp is experimental only and must not become the gameplay baseline again.

## Milestones
M0: FORMAL PASS — mGBA boots SoulGold and exposes host-accessible GBA memory maps.
M1: FORMAL PASS — live EWRAM/IWRAM state correlation works.
M1.1: REJECTED — wrong frontend audio timing plus blocking caused global slow motion.
M1.2: gameplay/visual broadly PASS; audio synchronization REJECTED.
M1.3: REJECTED — bounded audio-master queue control treated the symptom and still allowed the frontend to run too fast.
M1.4: ACTIVE — exact mGBA/libretro core-clock pacing.

## Proven audio root cause
mGBA reports `59.727501 FPS` and produces audio corresponding to one emulated frame per `retro_run` call.

M1.2:
- observed host FPS = 63.4293
- queue max = 588556 bytes (~3.065 s)
- predicted excess queue from the FPS mismatch = ~572953 bytes
- prediction error ~2.7%

M1.3:
- observed host FPS = 62.4737
- queue max = 386672 bytes (~2.014 s)
- predicted excess queue = ~366690 bytes
- prediction error ~5.4%

Two independent runs therefore reproduce the queue growth from the host overclock alone. Audio queue depth is not the root cause.

M1.4 uses one pacing authority only: the FPS reported by mGBA/libretro. Renderer VSYNC and audio queue depth are not clocks.

## StateBridge
Promoted:
- gBattleTypeFlags 0x0200271C
- gBattlersCount 0x02002720
- gBattleStruct 0x02002724
- gBattleControllerExecFlags 0x02002994
- gCurrentMove 0x02002AB4
- gChosenMove 0x02002B2E
- gBattleMons base 0x02002B34

## Species correction
The previous statement that species 1289 was invalid is withdrawn.

SoulGold source authority defines:
- `SPECIES_SPRIGATITO = 1289`
- `SPECIES_MARILL = 183`

The observed battler pair 1289 / 183 is therefore consistent with Sprigatito / Marill and is positive evidence that the current species reader is valid.

## Next sequence
1. Validate M1.4 core-clock audio/video sync and seal desktop host baseline.
2. M2: use species + move state for one external PMD animated sprite proof, with Sprigatito as the natural first candidate.
3. Generalize PMD provider, then Showdown provider.
4. Add Traditional Chinese host text/font layer.
5. Android ARM64 / AYN THOR frontend.

## Handoff discipline
Every meaningful checkpoint ships a complete ZIP and evidence. Human-visible failure overrides machine PASS.
