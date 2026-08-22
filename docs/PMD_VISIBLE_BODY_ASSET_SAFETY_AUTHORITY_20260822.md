# PMD Visible Body Asset Safety Authority

Status: **FORMAL AUTHORITY / PROJECT HARD CONSTRAINT**

Effective: 2026-08-22

Formalized by: PMD + StadiumBattleFX Integration I `v0.2.13a`

Formal PMD `main.lua`: `7365476702ab294ad75b5c52e9e69dff9710c608ea57dc806e540e7b1650d406`

## Scope

This authority governs which PMD semantic motion assets are permitted to render as the visible battler body. It does not change move mechanics, damage, HIT_FRAME ownership, Action Binding timing families, StadiumBattleFX move VFX, DRAMATIC_SHAPE depth, or THOR UI ownership.

## Hard rules

1. **Visible PMD `head` assets are forbidden globally.** Extracted `*_head.png` strips can contain only a detached head crop and can produce a floating-head result.
2. **Visible native semantic `lunge` / LeapForth assets are forbidden globally until a full-species full-body integrity audit explicitly re-authorizes them.** Thor evidence in v0.2.10d showed player Pikachu Headbutt and Bite both mapping to `action=lunge`; these were the two player moves reported as fragmenting the visible sprite into multiple pieces.
3. Semantic families `head` and `lunge` remain valid for move classification, impact direction, anticipation, recovery, and other presentation semantics. The prohibition is only on the unsafe visible body asset.
4. Safe visible-body fallback order is `charge → strike → attack`.
5. The policy must be structural, not move-specific. Headbutt, Bite, Body Slam, Fury Attack, future move mappings, ambient cues, test fixtures, and future feature code all consume the same central safety rule.
6. `motionAssetFor()` or equivalent final asset lookup must retain a last-resort guard that prevents direct visible loading of `head` or native `lunge` assets even if a future caller requests them accidentally.
7. Any future promotion requires zero detached-head incidents and zero fragmented-body incidents in relevant visual testing. Runtime Action Binding for tested visible bodies should not own `action=head` or unsafe native `action=lunge`; semantic family names may remain.

## Evidence basis

v0.2.10d Thor evidence (`PMD_v0210d_VISIBLE_MOTION_CLOCK_I_EVIDENCE_20260822_183452.zip`) localised the common body path:

- Player Scratch: `family=swing action=swing`
- Player Headbutt: `family=head action=lunge`
- Player Bite: `family=bite action=lunge`
- Player Quick Attack: `family=dash action=charge`
- Enemy Headbutt: `family=head action=charge`

The user reported exactly two player moves fragmenting the visible PMD body. The shared differentiator was the player native semantic `lunge` / LeapForth body path, not Stadium move VFX.

## Formal implementation

Starting from v0.2.10e and sealed in formal v0.2.13a:

- native semantic LeapForth/lunge records are retired from visible rendering and alias proven complete-body records;
- semantic head/lunge routing never intentionally selects native lunge;
- Fury Attack no longer requests lunge as its multi-hit body source;
- central asset lookup blocks both `head` and `lunge` and redirects to `charge → strike → attack`;
- v0.2.12a closure evidence reported `UNSAFE_VISIBLE_HEAD_LUNGE_ACTION_COUNT=0` across the closure sets.

## Supersession rule

This safety authority is inherited by every later PMD battle-presentation candidate. It may only be relaxed by a new explicit authority backed by a full-species full-body asset audit. A move-specific request is not sufficient to bypass the central guard.
