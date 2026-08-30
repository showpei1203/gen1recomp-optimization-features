# SoulGoldRecomp Architecture Reset — mGBA Hardware Authority
Date: 2026-08-30

## Superseding rule

The previous plan that treated gbarecomp as the required runtime authority is
retired.

### New authority split

**mGBA = GBA hardware correctness authority**

mGBA owns:
- ARM/THUMB CPU execution
- BIOS/SWI
- IRQ/HALT
- DMA/timers
- PPU
- APU
- cartridge save/RTC
- frame/audio timing

Gen1recomp must not reimplement or repair those systems as a prerequisite for
SoulGold features.

**Gen1recomp = game enhancement layer**

Gen1recomp owns:
- SoulGold state observation and game-specific hooks
- external PMD animated sprites
- external Showdown sprites
- battle presentation extensions
- Traditional Chinese `zh-Hant-TW`, English fallback
- external assets beyond the GBA ROM-size ceiling
- second-screen / AYN THOR UI
- optional mods and host-side configuration

**gbarecomp = optional experimental acceleration lane**

It may later accelerate isolated, proven game functions. It is not permitted to
be the gameplay baseline and may not block releases.

## Evidence that triggered the reset

The latest gbarecomp test showed:
- ordinary map movement initially near 59 FPS
- NPC dialogue caused persistent ~19–20 FPS behavior
- post-dialogue map movement remained slow
- battle remained slow
- BIOS IRQ interpreter bypass removed IRQ guard failures, yet lag remained
- run ultimately aborted inside a 200,000,000-instruction SELF-HEAL bridge at
  ROM PC `0x08241524`

This establishes that continuing to repair the custom GBA runtime is no longer
the highest-value path for the SoulGold product.

## mGBA pin for M0

Repository:
`https://github.com/mgba-emu/mgba`

Pinned upstream revision:
`c65e8a3d4666b0ea68a01578232452f31b185332`

The pin is immutable for M0/M1. Updating mGBA requires a separate controlled
compatibility checkpoint.

## New milestone sequence

M0 — Hardware authority bootstrap
- build pinned mGBA libretro core
- boot the exact SoulGold Beta 1 ROM
- capture mGBA memory maps
- prove direct host access to BIOS/EWRAM/IWRAM/IO/VRAM/ROM
- no graphics replacement yet

M1 — SoulGold state bridge
- correlate RAM symbols/state transitions during:
  - normal overworld
  - NPC dialogue
  - scripted event
  - battle enter/exit
  - active battler species
  - selected/executed move
- export stable read-only state API

M2 — PMD animated battle overlay proof
- one species first
- external animation files
- timing / offset / anchor metadata
- no ROM-size dependency

M3 — generalized external sprite provider
- PMD Edition
- Showdown Edition
- one shared gameplay core

M4 — Traditional Chinese host text layer
- `zh-Hant-TW`
- English fallback
- external font/text assets

A0 — Android ARM64 / AYN THOR host
- `arm64-v8a`
- mGBA-backed runtime
- dual-screen-aware frontend

## Permanent gates

1. A new enhancement may not require custom emulation correctness work.
2. mGBA behavior is the reference when host/game hooks disagree with gbarecomp.
3. External assets do not need to fit inside the 32 MiB GBA ROM.
4. PMD/Showdown variants must share the same gameplay/hardware runtime.
5. Traditional Chinese remains a final-product requirement.
6. Every meaningful checkpoint ships a complete handoff ZIP plus evidence.
