# SoulGold M1.4 Formal Pass → M2 PMD Handoff
Date: 2026-08-30

## Sealed baseline

M0 = FORMAL PASS / SEALED
M1 = FORMAL PASS / SEALED
M1.4 = FORMAL PASS / SEALED

mGBA pinned revision:
`c65e8a3d4666b0ea68a01578232452f31b185332`

SoulGold Beta 1 ROM SHA-1:
`d88b6a59802ccd442275ecbcfc9140fff34556dc`

Accepted M1.4 machine evidence:
- target FPS 59.727500
- observed FPS 59.702600
- source audio 65536 Hz
- audio queue max 137.417 ms
- final queue 78.562 ms
- queue drift -0.8008 ms/sec
- machine gate PASS

Accepted human evidence:
all tested gameplay, event, battle, BGM and SFX behavior normal.

## Architecture

mGBA is the permanent GBA hardware correctness authority.
The Gen1 enhancement layer owns game-specific state, PMD/Showdown external sprites, Traditional Chinese localization, host UI and Android/AYN THOR presentation.
gbarecomp is optional experimental acceleration only and must not block the mainline.

## StateBridge

- gBattleTypeFlags = 0x0200271C
- gBattlersCount = 0x02002720
- gBattleStruct = 0x02002724
- gBattleControllerExecFlags = 0x02002994
- gCurrentMove = 0x02002AB4
- gChosenMove = 0x02002B2E
- gBattleMons base = 0x02002B34

Species observation is accepted:
- 1289 = Sprigatito
- 183 = Marill

## M2 only goal

Prove one external PMD animated Pokémon can be rendered in a live mGBA-backed SoulGold battle.

First target:
Sprigatito / species 1289.

M2 requirements:
1. external PMD assets, not ROM-injected assets
2. species-driven asset selection through StateBridge
3. host overlay on the live battle framebuffer
4. animation frames and timing
5. anchor/center/offset metadata
6. preserve M1.4 AV timing and gameplay correctness
7. no full-Pokédex conversion before the one-species proof passes

Final product requirements remain:
- Android ARM64 / AYN THOR
- PMD Edition and Showdown Edition on one runtime
- Traditional Chinese zh-Hant-TW with English fallback
