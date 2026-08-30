# SoulGold M0 mGBA Hardware Authority — FORMAL PASS
Date: 2026-08-30

## Result
M0 is formally accepted.

Evidence package:
`SOULGOLD_M0_MGBA_BRIDGE_EVIDENCE_20260830_165743.zip`

Pinned mGBA revision:
`c65e8a3d4666b0ea68a01578232452f31b185332`

SoulGold Beta 1 ROM SHA-1:
`d88b6a59802ccd442275ecbcfc9140fff34556dc`

## Machine gates
- mGBA core booted successfully.
- 300 / 300 video frames produced.
- Logical framebuffer: 240x160.
- Reported cadence: 59.727501 FPS.
- BIOS map: 0x00000000, 16 KiB — PASS.
- EWRAM map: 0x02000000, 256 KiB — PASS.
- IWRAM map: 0x03000000, 32 KiB — PASS.
- IO map: 0x04000000, 1 KiB — PASS.
- VRAM map: 0x06000000, 96 KiB — PASS.
- ROM0 map: 0x08000000, 32 MiB — PASS.
- ROM mirrors 0x08000000 / 0x0A000000 / 0x0C000000 resolve to the same backing storage.
- Host bridge received direct pointers for GBA address-space memory through mGBA's libretro memory-map interface.

Final evidence gate:
`M0_MGBA_HARDWARE_AUTHORITY_GATE=PASS`

## Architecture authority
From this checkpoint onward:
- mGBA is the sole GBA hardware-correctness authority.
- Gen1recomp is the SoulGold enhancement/state/asset/localization layer.
- gbarecomp is optional experimental acceleration only and may not block the product mainline.

## Next checkpoint — M1
M1 must build a live state-correlation bridge on top of the same pinned mGBA core and identify stable read-only state signals for:
1. normal overworld,
2. NPC dialogue active/inactive,
3. scripted event active/inactive,
4. battle enter/exit,
5. active battler species,
6. selected/executed move.

No emulator correctness work is permitted in M1.
