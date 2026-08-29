# SoulGold Recomp S0 Authority

Date: 2026-08-29
Status: ACTIVE RESEARCH / BOOTSTRAP
Branch: `feature/soulgold-recomp-s0`

## Project intent

Use the existing GBARecomp/EmeraldRecomp ecosystem as the runtime scaffold for a native SoulGold target, then use an external mod/content layer to move presentation-heavy assets outside the original GBA cartridge address-space budget.

The user-facing goal is not to enlarge a `.gba` file. The goal is to preserve SoulGold gameplay/behavior while allowing large optional content packs (animated battlers, battle FX, backgrounds, audio, weather, UI, etc.) to live outside the ROM.

## Locked upstream inputs for S0

Do not float these during S0 bring-up.

- SoulGold source: `Eemeliri/soulgold`
  - pinned commit: `a6efa38348f978348da9dc4f4a7878cccf27bfd0`
  - current build output name from Makefile: `Soulgold_Beta_1.gba`
  - base: pokeemerald-expansion / Emerald GBA target
- GBARecomp: `mstan/gbarecomp`
  - pinned commit: `ed9824b70aa350cd9e1653894beaf6b1b6b27787`
- EmeraldRecomp scaffold: `mstan/EmeraldRecomp`
  - pinned commit: `4e1f89669b9945e338c0f2e52816aa0533fa30d3`

Pins may be promoted only after an S0 baseline exists and a deliberate compatibility update is tested.

## Facts established from upstream

1. GBARecomp is game-agnostic and executes the original ROM's ARM/THUMB machine code through generated native C/C++ against the reusable GBA hardware/runtime model.
2. A game target still needs its own config/runtime integration. A prebuilt Emerald executable cannot become SoulGold merely by swapping the ROM.
3. EmeraldRecomp already exposes a compact per-game scaffold around:
   - generated recompilation shards
   - `game.toml`
   - ROM SHA-1 / CRC32 gates
   - common `gbarecomp_runtime`, GBA, debug and launcher libraries
   - built-in mod support via `GBARECOMP_ENABLE_MODS`
4. EmeraldRecomp's current `game.toml` uses a program load address of `0x08000000`, ROM identity hash, save-chip declaration, recompiler seeds/boundaries, and 64 codegen shards.
5. SoulGold is itself an Emerald/pokeemerald-expansion build and produces `.gba`, `.elf`, `.map`, and `.sym` outputs. This is unusually favorable because we can use the decomp build products to seed accurate function/symbol metadata instead of blind ROM discovery.
6. SoulGold's Makefile currently uses `FILE_NAME := Soulgold_Beta_1` and therefore emits `Soulgold_Beta_1.gba`, `Soulgold_Beta_1.elf`, `Soulgold_Beta_1.map`, and `Soulgold_Beta_1.sym`.

## Architecture decision

### What we are NOT building

```text
EmeraldRecomp.exe + SoulGold.gba = SoulGold
```

That model is rejected.

### S0 target architecture

```text
SoulGold source @ pinned commit
        |
        | make
        v
Soulgold_Beta_1.gba + ELF/MAP/SYM
        |
        | symbol import / gba_recompile
        v
SoulGold generated native shards
        |
        +------------------------------+
        |                              |
        v                              v
GBARecomp common runtime       SoulGold game config/glue
        |                              |
        +---------------+--------------+
                        v
                 SoulGoldRecomp
                        |
                  external mods
```

EmeraldRecomp is a scaffold/reference, not the execution identity of the new game.

## S0 acceptance gates

S0 is deliberately narrow. Do not add PMD/Showdown assets yet.

### S0-A Source Authority
- pinned SoulGold source checked out
- successful clean SoulGold build
- capture:
  - source commit
  - ROM size
  - SHA-1
  - SHA-256
  - CRC32
  - ELF hash
  - MAP hash
  - SYM hash

### S0-B Recompiler Intake
- `gba_scan` / CLI accepts the built SoulGold ROM
- symbol importer can consume SoulGold decomp outputs or a deterministic derived form
- a SoulGold `game.toml` is generated/reviewed
- `gba_recompile` emits deterministic sharded C/C++ without fatal discovery errors

### S0-C Native Runner Build
- SoulGold target links against pinned GBARecomp runtime
- ROM hash gate rejects the wrong ROM
- runner reaches BIOS -> ROM entry without fatal runtime error

### S0-D Visual Bring-up
Minimum promotion target:
- title screen visible and responsive

Preferred S0 closure:
- title -> new/load game -> overworld movement

Runtime interpreter/self-heal misses are allowed during early bring-up but must remain visible in evidence; they may not be mislabeled as full static coverage.

## S1: the actual 32 MB breakthrough

S1 does not mean producing a ROM larger than 32 MB.

S1 succeeds when a visual asset requested by SoulGold is resolved from an external package and rendered while gameplay remains correct, with safe fallback to the original ROM asset.

Proposed contract:

```text
SoulGold asset request
      |
      v
External Asset Resolver
  | found             | missing/disabled
  v                   v
external provider     original ROM path
```

Initial S1 proof should use one battler/graphic only. Do not bulk-convert the Pokédex until this works on THOR.

## S2 direction after S1

Provider priority can later become declarative, e.g.:

```text
PMD provider
  -> Showdown provider
     -> SoulGold original fallback
```

Large animation/audio/background resources remain external. Game logic, save behavior, battle state and hardware-facing semantics stay engine/game-owned.

## User workload policy

The user should normally only need to:
1. run a provided bootstrap/test package,
2. supply their locally built/owned ROM when required,
3. run the candidate on PC/THOR,
4. return evidence/logs/screenshots.

Do not make the user manually edit source or repeat environment discovery that can be automated.

## Next implementation tasks

1. Build an automated S0 workspace bootstrap with pinned upstream commits.
2. Capture SoulGold ROM/ELF/MAP/SYM authority deterministically.
3. Prototype symbol-import path from SoulGold ELF/MAP into GBARecomp.
4. Fork the EmeraldRecomp per-game scaffold into a `soulgold` variant locally without carrying Emerald-only RAM dispatch hacks.
5. Produce first runnable Windows candidate, then Android/THOR packaging after PC bring-up is stable.

## Hard rule

> Preserve the GBA game's behavior; remove the GBA cartridge's content-storage ceiling.

Do not confuse those two goals.
