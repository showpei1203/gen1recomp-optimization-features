# PMD Head Action Ban I

Status: **PROJECT HARD CONSTRAINT / implementation test pending**
Date: 2026-08-22

## Rule

Visible PMD `action=head` is forbidden for every Pokémon species and every runtime context.

Reason: extracted `*_head.png` strips can be detached head-only crops instead of complete-body battle poses. Headbutt on the v0.2.10b Thor fixture demonstrated the invalid floating-head result.

Semantic family `head` is still allowed for move classification, timing, HIT ownership and recovery behavior. It must never select the PMD `head` body asset.

Required full-body fallback order:

`lunge -> charge -> strike -> attack`

The rule applies to:
- Headbutt / Skull Bash / Horn / Peck-style semantic-head moves
- Bite family if it previously borrowed `head`
- Fury Attack / multi-hit semantic routing
- ambient/small-action patterns
- future features and test fixtures

A central `motionAssetFor()` safety redirect is required so any accidental future request for `action=head` is converted before asset lookup.

Promotion gate:
- zero visible detached-head incidents
- zero runtime visible-body `ACTION_BIND ... action=head`

## v0.2.10b evidence note

Motion prewarm itself was inexpensive (player 4 actions about 9.3 ms, enemy Tackle about 1.4 ms), but Scratch remained first-use asymmetric: first START->HANDOFF 59f, second 29f while both SFX->HIT were 72f. Therefore the remaining first-Scratch delay is not texture/Quad cold-load and will be investigated separately after the head-action safety gate.
