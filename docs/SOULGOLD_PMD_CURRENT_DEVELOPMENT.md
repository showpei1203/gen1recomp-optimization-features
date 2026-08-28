# Pokémon SoulGold PMD Animated Prototype — CURRENT DEVELOPMENT

Date: 2026-08-28
Status: ACTIVE / GBA-FIRST

## Current baseline authority

- Host: `Eemeliri/soulgold`
- Pinned source commit: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- Upstream lineage: pokeemerald-expansion 1.15.x
- Target runtime: GBA ROM, mGBA desktop, AYN THOR RetroArch + mGBA
- Prototype species: Cyndaquil
- PMD source: PMDCollab/SpriteCollab species `0155`

## Current phase

Architecture / baseline preparation before engine patching.

## PASS / confirmed source findings

- SoulGold source and current commit identified.
- Build documentation identified: WSL/Linux + `make` workflow.
- `MAX_MON_PIC_FRAMES` is currently 2.
- `MonSpritesGfxManager` allocation scales with `MAX_MON_PIC_FRAMES`; globally increasing it is rejected as the first design.
- Player-side Pokémon use the back-sprite/generic `gAnims_MonPic` path.
- Opponent-side Pokémon use species `frontAnimFrames`.
- Front/back sprite assets are decompressed independently by `LoadSpecialPokePicIsEgg()`.
- Gen1recomp Rich Ambient design has been re-read and adopted as behavioral authority.
- Cyndaquil PMD source metadata has GBA-safe ambient actions (`Idle`, `Walk`, `Rotate`, `LookUp`, `DeepBreath`, `Sit`) and >64px actions (`Hop`, `Attack`, `Swing`) suitable for later renderer stress gates.

## Architecture decisions

1. GBA first. GBC backend is deferred.
2. SoulGold is a host adapter, not the reusable framework boundary.
3. Portable PMD Animation IR is independent of SoulGold battle globals.
4. Runtime uses per-battler state.
5. Rich Ambient replaces the simplistic `Idle 4F` interpretation of the first visual gate.
6. Existing native move VFX/SFX remain authoritative and separate from PMD body actions.
7. Fixed-delay synchronization is forbidden.
8. The initial multi-frame implementation uses a two-slot rolling frame cache instead of raising global frame residency.
9. Player-side back-facing presentation is the primary prototype view because it is the real starter gameplay case.
10. GBA-safe <=64px ambient actions are validated before composite/large-action work.

## Current gate

### G0 — reproducible SoulGold baseline

Required evidence:
- source commit
- toolchain/version
- exact build command
- ROM size
- SHA-256
- CRC32
- mGBA desktop boot result
- AYN THOR RetroArch+mGBA boot result

G0 status: `SOURCE AUTHORITY PASS / LOCAL BUILD EVIDENCE PENDING`

Reason: connected source authority is available, but the current execution sandbox does not provide a complete local clone/build environment for this external repository. This is infrastructure pending, not a source/build failure.

## Next exact implementation step

Build the first G1 candidate around the existing two battler image slots:

1. define a portable PMD frame descriptor and per-battler runtime state;
2. add a SoulGold adapter that can identify the battler sprite and its two image slots;
3. stage Cyndaquil PMD player-facing/back-facing frame data into the inactive slot;
4. switch displayed frame only on a safe animation boundary;
5. loop a minimal two-source benchmark before adding the full Rich Ambient script;
6. retain stock UI, transition, palette, move FX and gameplay.

## P4 Rich Ambient benchmark after G1

Use only GBA-safe source actions first:

`Idle -> Walk -> HOME -> LookUp -> HOME -> DeepBreath -> HOME -> Rotate -> HOME`

Exact pauses/timing are metadata/profile driven and will be tuned visually after structural playback is proven.

## Deferred intentionally

- `Hop` (24x72)
- PMD `Attack` (64x72)
- `Swing` (72x80)
- large/composite OBJ policy
- physical attack state
- special attack state
- hurt state
- shiny PMD palette generation
- batch importer
- second ROM-hack portability proof
- GBC support

## Formal promotion policy

Compile PASS is not visual PASS.
Structural/runtime PASS is not formal prototype PASS.
No phase may be promoted without actual battle evidence on the target renderer, and AYN THOR remains a required final acceptance target.
