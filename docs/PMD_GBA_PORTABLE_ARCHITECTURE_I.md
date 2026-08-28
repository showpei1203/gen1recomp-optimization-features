# PMD GBA Portable Battle Framework — Architecture I

Status: DESIGN AUTHORITY / IMPLEMENTATION PENDING
Date: 2026-08-28

## Scope

The first target is Pokémon SoulGold (`Eemeliri/soulgold`) on GBA, with runtime validation on mGBA desktop and AYN THOR RetroArch + mGBA.

SoulGold is the first host, not the framework boundary. The reusable boundary is GBA + pokeemerald-style battle presentation, with a thin host adapter for each ROM hack.

GBC is explicitly deferred. No GBC renderer work is part of the current prototype.

## Source authorities

- SoulGold baseline repo: https://github.com/Eemeliri/soulgold
- SoulGold pinned source commit: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- SoulGold README identifies pokeemerald-expansion 1.15.x lineage.
- PMD source: `PMDCollab/SpriteCollab`
- Cyndaquil PMD source species folder: `sprite/0155`
- PMD source metadata authority: `AnimData.xml`

## Inherited Gen1recomp authorities

This framework inherits the proven presentation principles from Gen1recomp PMD work:

1. PMD animation is the Pokémon body-performance layer. Native move VFX/SFX remain a separate layer.
2. Animation ownership is per battler, never one global Pokémon animation state.
3. Combat synchronization is event-driven. Fixed sleeps/delays are forbidden as authority.
4. HIT is authoritative and separate from source-body animation timing.
5. Contact and projectile actions have different release/recovery semantics.
6. Rich Ambient is species-appropriate behavior, not simply looping PMD `Idle`.
7. HOME is a stable presentation position. Ambient movement must not alter logical battle coordinates.
8. After combat/reaction, settle to HOME before restarting ambient behavior.
9. Nearest-neighbor only; no bilinear/bicubic/antialias scaling.
10. Source metadata such as duration, offsets, hit/rush/return frames must be preserved through conversion.

## GBA-first architecture

```text
PMD SpriteCollab source
        |
        v
PMD source parser
        |
        v
Portable PMD Animation IR
  - species
  - actions
  - frames
  - duration
  - source offsets / center
  - rush / hit / return markers
  - direction
  - body/ecology profile
        |
        +-----------------------------+
        |                             |
        v                             v
GBA asset compiler              GBA behavior compiler
  4bpp / palette                  Rich Ambient state data
  64x64 canvas packing            combat action metadata
  frame blobs                     event sync metadata
        |                             |
        +-------------+---------------+
                      v
             GBA PMD Runtime Core
              - per-battler state
              - HOME anchor
              - two-slot rolling frame cache
              - frame clock
              - presentation offsets
              - combat interruption/recovery
                      |
                      v
               Host Adapter API
                      |
         +------------+-------------+
         |                          |
         v                          v
SoulGold adapter          future pokeemerald-expansion
                         ROM-hack adapters
```

## Why the runtime must not globally raise MAX_MON_PIC_FRAMES

SoulGold currently defines `MAX_MON_PIC_FRAMES = 2`.

Its `MonSpritesGfxManager` allocates sprite frame storage from this value for each battler. Therefore increasing this global constant to 4/8 would increase permanent battler EWRAM use and couples the framework to an arbitrary maximum frame count.

The portable runtime instead uses the existing two frame slots as a rolling cache:

- slot A = visible/current frame
- slot B = staging/next frame
- prepare next frame from ROM into the inactive slot
- swap at a frame boundary
- reuse the old slot for the following frame

Animation length therefore does not equal resident frame count.

This is the required direction for the prototype unless profiling proves a different bounded cache is necessary.

## SoulGold-specific facts already confirmed

### Player vs opponent sprite paths

`SetMultiuseSpriteTemplateToPokemon()` uses:

- player side: `gAnims_MonPic`
- opponent side: species `frontAnimFrames`

Therefore a real player-starter prototype must explicitly support the player/back-facing presentation path. Testing only an enemy front sprite is insufficient.

### Existing frame storage

`src/data.c` defines per-battler `SpriteFrameImage` tables backed by `MON_PIC_SIZE` blocks. Current generic mon animation exposes only frame 0/1.

### Asset loading

`LoadSpecialPokePicIsEgg()` independently chooses `frontPic` or `backPic` and decompresses it into the destination buffer.

The PMD runtime should integrate around these existing battle image buffers instead of replacing unrelated UI/party sprite systems in Phase 1.

## Portable Host Adapter contract

Host-specific code is limited to an adapter with semantic callbacks similar to:

```c
struct PmdBattleHostAdapter
{
    bool32 (*IsBattlerPresent)(u8 battler);
    u16    (*GetBattlerSpecies)(u8 battler);
    bool32 (*IsPlayerSide)(u8 battler);
    bool32 (*IsBattlerVisible)(u8 battler);

    void (*GetHomeAnchor)(u8 battler, s16 *x, s16 *y);
    void (*SetPresentationOffset)(u8 battler, s16 x, s16 y);
    bool32 (*StageFrame)(u8 battler, const void *frameData, u32 size, u8 cacheSlot);
    bool32 (*PresentCacheSlot)(u8 battler, u8 cacheSlot);

    void (*OnMoveStart)(u8 battler, u16 move);
    void (*OnMoveFxHandoff)(u8 battler, u16 move);
    void (*OnHit)(u8 battler);
    void (*OnMoveComplete)(u8 battler, u16 move);
    void (*OnFaint)(u8 battler);
};
```

Exact signatures may change during implementation, but portable core code must not directly depend on SoulGold battle globals where the adapter can provide the semantic event instead.

## Cyndaquil Prototype: Rich Ambient P4

Cyndaquil remains the first prototype species.

PMD `AnimData.xml` confirms several GBA-safe ambient actions:

- `Idle`: 24x32
- `Walk`: 24x32
- `Rotate`: 24x32
- `LookUp`: 24x32
- `DeepBreath`: 24x32
- `Sit`: 24x32

Large actions are intentionally deferred from the first ambient gate:

- `Hop`: 24x72
- `Attack`: 64x72
- `Swing`: 72x80

P4 Rich Ambient should therefore prove the framework using only <=64px source actions first.

Suggested first ecology profile:

```json
{
  "species": "Cyndaquil",
  "body_class": "small_quadruped",
  "ambient_style": "active_prowl",
  "home_action": "Idle",
  "ambient_pattern": [
    "idle_hold",
    "Walk",
    "idle_hold",
    "LookUp",
    "idle_hold",
    "DeepBreath",
    "idle_hold",
    "Rotate"
  ],
  "logical_position_locked": true
}
```

This pattern is presentation intent, not a requirement to execute every action every cycle. The runtime may use weighted deterministic/seeded choices after the first fixed visual benchmark is accepted.

## First formal implementation gates

### G0 — Baseline
- pinned SoulGold source builds cleanly
- baseline ROM hash/size/toolchain recorded
- desktop mGBA boot PASS
- THOR RetroArch+mGBA boot PASS

### G1 — Two-slot frame proof
- Cyndaquil player-side PMD frame can replace stock battle body without affecting battle UI
- second frame can be staged and swapped repeatedly
- no global `MAX_MON_PIC_FRAMES` increase
- no corruption after repeated swaps

### G2 — Rich Ambient core
- player Cyndaquil returns to stable HOME anchor
- at least three distinct PMD action sources participate in one ambient loop
- animation clock uses metadata-derived durations
- logical battler coordinates remain unchanged
- no drift/jitter accumulation

### G3 — Opponent-side proof
- same portable asset/behavior record can render opponent Cyndaquil using the host adapter side/direction selection
- no duplicate species-specific renderer code

Only after G0-G3 pass do large-action (>64px) policies and combat state binding become the next gate.

## Non-goals until G0-G3 pass

- batch importing the Pokédex
- global replacement of all Pokémon graphics
- PMD faint
- large composite sprites
- GBC backend
- random ambient personality generation
- gameplay/stat/move/story modifications

## Portability acceptance rule

A feature is not considered part of the portable PMD framework if it requires SoulGold-specific globals inside the core behavior/asset layer and cannot be represented behind the host adapter.

Long-term GBA portability will be proven by installing the same IR/runtime core into a second pokeemerald-expansion ROM hack with only adapter/build-integration changes.
