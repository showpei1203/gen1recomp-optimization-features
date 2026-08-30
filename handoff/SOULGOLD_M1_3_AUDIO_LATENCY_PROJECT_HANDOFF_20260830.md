# Pokémon SoulGold mGBA Enhancement Project — M1.3 Project Handoff
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
M1.1: REJECTED — multiple pacing authorities caused global slow motion.
M1.2: gameplay/visual broadly PASS; audio synchronization REJECTED.

## M1.2 audio evidence
- observed FPS 63.4293
- source audio 65536 Hz
- device 48000 Hz
- queue max 588556 bytes ≈ 3.065 s
- user observed event/battle SFX several beats behind visuals

Root cause: source rate is now correct, but queue growth is unbounded because the frontend advances faster than the 59.7275-Hz mGBA timeline.

## M1.3 active candidate
Bounded audio-master latency control only. No emulator change and no second absolute frame scheduler.
- startup prebuffer ~28 ms
- queue target ~38 ms
- correction threshold ~55 ms
- emergency threshold 120 ms
- normal correction 1 ms/frame when needed
- emergency recovery capped at 12 ms/frame
- never delete live audio samples

Machine acceptance:
- FPS 57..62
- source rate 64..67 kHz
- max queue latency <=140 ms
- battle + move state still observed

## StateBridge
Promoted:
- gBattleTypeFlags 0x0200271C
- gBattlersCount 0x02002720
- gBattleStruct 0x02002724
- gBattleControllerExecFlags 0x02002994
- gCurrentMove 0x02002AB4
- gChosenMove 0x02002B2E

Species is PROVISIONAL. Current raw reader produced 1289 for battler0, which is invalid. Fix species correlation before M2.

## Next sequence
1. Validate M1.3 audio/video sync and seal desktop-host baseline.
2. Correct and formally validate player/enemy species state.
3. M2: one external PMD animated sprite in real mGBA SoulGold battle.
4. Generalize PMD provider, then Showdown provider.
5. Add Traditional Chinese host text/font layer.
6. Android ARM64 / AYN THOR frontend.

## Handoff discipline
Every meaningful checkpoint ships a complete ZIP and evidence. A machine PASS may never override contradictory human-visible failure.
