# SoulGoldRecomp R0 Authority — 2026-08-29

## Decision

The project now has two product profiles:

1. **SoulGold GBA compatibility profile** — standard 32 MiB `.gba`, RetroArch/mGBA compatible.
2. **SoulGoldRecomp native profile** — GBARecomp-based native runtime. Animated Showdown/PMD assets are allowed to live outside the 32 MiB cartridge image.

The native profile is the primary path for unrestricted animated battlers. The GBA profile remains supported, but full-Pokédex animation compression is no longer the main blocker for the project.

## Fixed inputs

- SoulGold source: `Eemeliri/soulgold`
- SoulGold v1.0.5 source authority: `77ec3fc6275bb94dd703f4c1976f1457cc44a60b`
- GBARecomp framework: `mstan/gbarecomp`
- GBARecomp pinned revision for R0: `ed9824b70aa350cd9e1653894beaf6b1b6b27787`
- Development ROM, ELF and MAP MUST be produced by the same SoulGold source build. They are one inseparable authority set.

The release ROM previously supplied by the user is not used as the symbol-import target because a different compiler/linker build can change addresses. GBARecomp's decomp symbol importer expects build metadata that byte-matches the ROM being recompiled.

## R0 goal

Prove that SoulGold can enter the GBARecomp toolchain without hand-editing generated code.

Required R0 gate:

1. clean-build SoulGold v1.0.5;
2. verify ROM/ELF/MAP exist;
3. build pinned `gba_scan` and `gba_recompile`;
4. scan SoulGold ROM successfully;
5. import SoulGold ELF/MAP symbols with `import_decomp_symbols.py`;
6. generate a deterministic per-build `game.toml` identity config;
7. run GBARecomp C++ generation with SoulGold symbols;
8. compile the generated corpus into `gbarecomp_game` static library;
9. upload evidence only. Do **not** upload ROM or generated ROM-derived C++.

R0 PASS means: **SoulGold machine code can be translated into buildable native C++ through GBARecomp.** It does not yet mean the game boots.

## R1 goal

Create a SoulGoldRecomp host runner using the shared GBARecomp runtime and validate:

`reset/boot -> title screen`

R1 requires mGBA/reference comparison and may use interpreter/self-heal fallback for uncovered code. Do not claim static coverage where interpreter fallback was used.

## R2 goal

Validate:

`title -> New Game -> leave house -> first automatic event`

This is the same early-flow oracle that exposed the wrong v1.0.6.1 baseline in the GBA prototype.

## R3 goal

Validate the normal starter/first-battle path, then add exactly one external host asset override:

`Sprigatito Showdown idle (back)`

The external asset must not be inserted into the GBA ROM. Missing overrides fall back to the original cartridge graphics.

## R4 goal

Promote the external battler asset registry to bulk Showdown/PMD packs. Preserve SoulGold native battle choreography:

- x/y and x2/y2 movement;
- shake/lunge;
- affine scale/rotation;
- hit/faint/send-out choreography;
- battle FX.

Animated asset runtimes own body pixels and animation timing only at their explicit ownership boundary. Native battler transforms remain a separate composable layer.

## Non-negotiable rules

- Never commit or upload a ROM.
- Never commit generated ROM-derived C++.
- Generated output is evidence, not authority; fix the importer/recompiler/config and regenerate.
- Pin both SoulGold and GBARecomp revisions in CI.
- Human runtime remains `PENDING` until actually tested on the target platform.
- Android/AYN THOR packaging comes after desktop/headless runner correctness, not before.
