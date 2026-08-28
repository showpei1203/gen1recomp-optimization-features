# SoulGold PMD G2 Rich Ambient — Compile PASS

Date: 2026-08-28
Status: COMPILE PASS / HUMAN VISUAL ACCEPTANCE PENDING

## Authorities

- SoulGold: `Eemeliri/soulgold`
- SoulGold revision: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- PMD source: `PMDCollab/SpriteCollab` species `0155`
- SpriteCollab revision: `4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- Framework branch: `feature/pmd-portable-battle-framework`
- G2 compile framework commit: `f4d52b206029e885fa6a64a1f07b7c365ed8d545`
- GitHub Actions run: `33150904208`

## G2 scope

Player/opponent Cyndaquil Rich Ambient candidate:

`HOME -> Idle -> HOME -> Walk -> HOME -> LookUp -> HOME -> DeepBreath -> HOME -> Rotate -> HOME`

The G1 renderer contract remains sealed and reused:

- `MAX_MON_PIC_FRAMES = 2`
- arbitrary source animation length through two resident battler image slots
- `RequestSpriteFrameImageCopy(...)` presentation path
- native `sprite->anims` unchanged
- `src/data.c` / frame residency plumbing unchanged

## New G2 behavior contract

- Explicit HOME boundary.
- Ambient actions are one-shot behavior units, not permanent loops.
- HOME hold time is species-profile behavior data rather than renderer delay.
- Native battle ownership interruption abandons the stale ambient action.
- After interruption, the battler returns to HOME and restarts an approved ecology sequence.
- Mid-action resume after move/sendout/switch/status ownership is forbidden.
- Logical battle coordinates remain untouched.

## SpriteCollab source-layout finding

Cyndaquil `LookUp` is stored as a single-row 3-frame sheet (`72x32`) shared across directions, rather than an 8-direction sheet.

G2 therefore adds a source-layout wrapper that accepts either:

1. normal eight-direction PMD sheets, or
2. exactly one frame-height row shared by every direction.

The sealed G1 converter/runtime is not changed by this accommodation.

## Save compatibility

- save structure: `UNCHANGED`
- no species/save-block migration
- existing SoulGold save progression is intended to continue across G1 -> G2
- delivered ROM filename policy from G2 onward: `SoulGold-PMD-LIVE.gba` where practical

## Built ROM fingerprint

- bytes: `33554432`
- SHA-256: `0831c1c1172ef789c1152bb2955db2789c43b8aeabb207295fae5505e9c42eae`
- CRC32: `554857E1`
- title header: `POKEMON EMER`
- game code: `BPEE`
- maker code: `01`

## Next authority gate

Human visual/runtime acceptance on desktop mGBA using the user's continuing save.

Required observations:

- multiple distinct ambient behaviors are visible rather than a permanent Walk loop;
- HOME remains stable with no positional drift;
- LookUp single-row source renders correctly;
- DeepBreath and Rotate retain full-body integrity;
- choosing and executing a move interrupts ambient presentation cleanly;
- after native move ownership ends, Cyndaquil returns HOME before ambient behavior resumes;
- no stale partial frame, palette corruption, UI regression or save regression.

AYN THOR RetroArch+mGBA remains a later cross-device acceptance target.
