# SoulGold M0 mGBA Hardware Authority Bridge Handoff
Date: 2026-08-30

## Architecture reset

Main runtime authority is now mGBA, not gbarecomp.

Pinned mGBA:
`c65e8a3d4666b0ea68a01578232452f31b185332`

## Deliverable

`START_M0_MGBA_BRIDGE.bat` performs the full reproducible bootstrap in WSL and
packages evidence automatically.

The included `mgba_bridge_probe.cpp` is the first Gen1 enhancement-host seam. It
loads the mGBA libretro core directly and records the memory map supplied by
mGBA's `RETRO_ENVIRONMENT_SET_MEMORY_MAPS` interface.

This is important because enhancement logic can now observe real emulated GBA
memory without owning CPU/IRQ/BIOS correctness.

## M0 acceptance

Required regions:
- BIOS
- EWRAM
- IWRAM
- MMIO
- VRAM
- ROM0

Required video:
- at least 250 video frames out of a 300-frame probe
- logical framebuffer 240x160

## Next

M1 will make the bridge state-aware and correlate SoulGold RAM changes with:
- NPC dialogue
- scripted events
- battle transitions
- species
- moves
