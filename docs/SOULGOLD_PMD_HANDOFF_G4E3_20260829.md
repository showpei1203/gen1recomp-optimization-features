# Pokémon SoulGold PMD Animated Prototype — G4E3 Handoff

Date: 2026-08-29

## Authority
- SoulGold: `Eemeliri/soulgold` @ `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- PMD SpriteCollab: `PMDCollab/SpriteCollab` @ `4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- Framework: `showpei1203/gen1recomp-optimization-features`
- Branch: `feature/pmd-portable-battle-framework`
- G4E3 build authority: `236d1db27799116b0af3b4b6a89362e5a0de16f4`

Do not silently move upstream pins. Runtime visual PASS still requires later AYN THOR / RetroArch / mGBA acceptance.

## User contract
- Preserve SoulGold battle logic, move FX, trainer/Poké Ball choreography, healthboxes, switching and controller timing.
- PMD owns supported battler body/shadow presentation only.
- Long-term target: PMD animated sprites for every species with sufficiently valid PMD source.
- Missing or invalid PMD source must fall back to the original SoulGold battle sprite.
- Do not invent missing PMD actions from semantically unrelated actions.
- Every meaningful checkpoint from here onward needs a new handoff.

## Corrected G4D roster authority
For 1025 National Dex base entries:
- `LOSSLESS_SINGLE_OBJ_BOTH_SIDES`: 901
- `MULTI_OBJ_REQUIRED`: 25
- `NATIVE_FALLBACK_MISSING_OR_INVALID_CORE`: 99
- source-usable core count: 926

Core actions audited: Idle / Walk / Hurt / Attack / Shoot.
Views: player UpRight, opponent DownLeft.
Transparent source overflow is allowed. Opaque pixel loss, crop and scale are forbidden.

## G4E3 tile-dictionary + delta codec
Workflow: `SoulGold PMD G4E3 Tile Delta Codec Gate`
Run/job: `33220302091` / `99012741477`
Result: SUCCESS.

Artifacts:
- ROM `9705078985`, digest `sha256:b993ea5f14c74a75d96e6f5a810c77204e4cd7e0c73e4e0047c322099cc44abc`
- Evidence `9705078409`, digest `sha256:9eef596b049ea8027c4d47ca19220020b7a56f868c121c924455d603ce6850fd`

Codec totals for 901 eligible species / both battle sides:
- side packs 1802
- core frames 67126
- dictionary entries 148919
- dictionary raw 4,765,408 bytes
- dictionary LZ77 2,575,132 bytes
- HOME maps 115,648 bytes
- raw changed-tile commands 798,202 bytes
- LZ77 command streams 772,144 bytes
- descriptor bytes 681,168
- profile bytes 144,160
- palette bytes 57,664
- shadow metadata 141,844
- packed total 4,487,760 bytes
- worst-case four-battler EWRAM working set 64,816 bytes

ROM capacity blocker:
- current 32 MiB ROM trailing free: 1,486,872 bytes
- G4E3 full core pack: 4,487,760 bytes
- shortfall: 3,000,888 bytes

Therefore G4E3 proves the lossless codec design but does NOT authorize activating all 901 species yet. Current G4E3 ROM keeps the unchanged proven runtime parent.

## New player spatial-ownership root-cause lead
A related SoulGold/PMD development lane found that the player battler and HP/status box move together while the bottom battle UI stays fixed. This strongly indicates shared native spatial offsets surviving after `AnimateSprites()`, rather than only a PMD frame-anchor error.

Candidate ordering remains:
`AnimateSprites -> presentation spatial ownership -> BuildOamBuffer`

For presentation-owned idle/persistent states, audit and neutralize BOTH:
- battler `x2/y2`
- healthbox native spatial offset

to their baseline positions before OAM build.

Do not neutralize offsets while SoulGold owns native move motion, sendout, switching or other choreography. The exact fix from the related project is expected later and should be compared line-by-line before promotion.

This supersedes the old assumption that the Cyndaquil ~1px player-side sink was necessarily a PMD action-anchor problem. Root cause remains unpromoted until SoulGold-specific validation.

## Next lane
### G4F-A Spatial ownership repair
Audit SoulGold battler->healthbox association and native offsets. Add synchronized battler+healthbox spatial neutralization after AnimateSprites and before BuildOamBuffer only when PMD idle/persistent presentation owns position.

### G4F-B Runtime G4E3 loader prototype
Implement the codec on a small representative species batch first:
- ROM profile descriptor
- LZ77 tile dictionary -> EWRAM
- HOME tilemap reconstruction
- per-action LZ77 delta stream
- changed-tile application into 2048-byte body scratch
- existing two-slot presenter
- PMD markers/shadow metadata preserved
- lookup/decode failure -> native SoulGold

Include at least a simple small species, a large-canvas but single-OBJ eligible species, and a u16 dictionary-index case.

### G4F-C ROM-space strategy
Need measured recovery/avoidance of ~3.0 MiB before full 901-species activation. Audit cross-species tile reuse, descriptor reductions, stream packing and safe reclaim of existing ROM data. Do not silently exceed normal 32 MiB GBA target.

### G4F-D Multi-OBJ
25 valid multi-OBJ species stay native until a lossless multi-OBJ compositor exists. Never crop/scale them for coverage.

## Do not regress
- preserve upstream pins
- preserve G3R4B `AnimateSprites -> PMD -> BuildOamBuffer` ordering
- preserve native sendout/move/controller ownership
- separate PMD body/shadow ownership
- never drive body vertical position from Shadow.png
- missing/invalid PMD -> native SoulGold
- no runtime visual PASS without device/human evidence
