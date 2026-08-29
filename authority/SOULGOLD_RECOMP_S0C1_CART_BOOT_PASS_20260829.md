# SoulGoldRecomp S0-C1 Cart Boot / Render Pass

Date: 2026-08-29
Branch: `feature/soulgold-recomp-s0`

## Verdict

S0-C1 = FORMAL PASS / SEALED for CART BOOT + RENDER only.

This is not yet the title-screen gate.

## Evidence reviewed

- Runner SHA-256: `08647605065305fda3bdd9c13954a5626c500b95b48c790c8f7d00ccb3cf7200`
- SoulGold ROM SHA-1: `d88b6a59802ccd442275ecbcfc9140fff34556dc`
- GBA BIOS SHA-1: `300c20df6731a33952ded8c436f7f186d25d3492`
- 1200-frame headless execution exit code: 0
- final PC: `0x0800030c`
- PPU frames: 1200
- framebuffer PNG: valid, 115433 bytes
- VRAM/palette/OAM are populated

Framebuffer content is the SoulGold-native warning screen:

`WARNING! Inaccurate emulator detected! ... Press START to continue.`

This proves that the linked SoulGoldRecomp runner reached SoulGold cartridge code and rendered a game-authored screen. It is therefore materially beyond a runtime-only/blank-frame smoke test.

## Coverage status

Self-heal coverage remains `NOT_STATIC`:

- distinct dispatch misses: 23
- interpreted instructions: 40,591,045
- healed native entries: 19
- native calls: 9,251
- failed heals: 4
- jump-table candidate regions: 2

High-frequency non-healed runtime/RAM entries include:
- `0x03000000` ARM x1632
- `0x0300012C` ARM x2396
- `0x030011E8` THUMB x1198
- `0x03007DC4` THUMB x2

These are not grounds to revoke S0-C1. They remain runtime-fidelity / static-coverage work for later closure.

## Next gate: S0-C2

Do not patch out the warning yet.

S0-C2 must feed a genuine GBA START press through the runtime input path and capture post-warning framebuffers. The goal is to prove progression toward the SoulGold title/menu rather than bypass the game's own logic.

Suggested replay sequence from fresh boot:
- frame 0: keys released `0x03FF`
- frame 1250: START pressed, active-low `0x03F7`
- frame 1270: keys released `0x03FF`
- run to at least frame 3000

Capture intermediate and final PNG evidence if practical.

## Permanent requirements

- Every meaningful checkpoint must ship a downloadable handoff.
- Final release must support Traditional Chinese `zh-Hant-TW` through an external localization/glyph architecture with English fallback.
