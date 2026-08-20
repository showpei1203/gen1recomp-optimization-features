# GBC-A2 TEST Fixture Strategy

Status: DEVELOPMENT RULE — 2026-08-20

## Problem
The user is still in the early game and cannot reasonably obtain later benchmark moves such as Ice Beam, Surf, Psybeam, etc. GBC visual/runtime validation must not depend on normal game progression.

## Formal testing strategy
1. GBC-A2 introduces a TEST-only Battle Fixture / Move Injection path.
2. The fixture exists only in test candidates and is not part of normal gameplay logic.
3. On test start, benchmark moves are provided temporarily; test exit must not persist them into the normal save.
4. Do not modify formal learnsets, TM/HM acquisition, levels, party progression, or story progress.
5. No promotion gate may require the user to naturally obtain a benchmark move first.
6. The fixture must be repeatable, traceable, rollback-safe, and emit explicit TEST_ONLY evidence.
7. The fixture may change only the test battle move set / entry point. It must not change Presentation Timeline, HIT_FRAME, PMD Action Binding, damage/status ownership, audio-tail, Depth/Occlusion, Large Pokémon bounds, or species scale.

## Initial fixture move set
- Quick Attack or Tackle — contact
- Fury Swipes — multi-hit
- Ice Beam or Psybeam — beam
- Surf or Earthquake — area/full-screen observer
- Retain Ember / Thundershock / Thunder Wave for A1 regression

## Preferred implementation
Use a battle-local move set or test clone. If safe save-backed slot replacement is used, capture the original move and restore it before exiting the fixture. Prefer a battle-local clone when there is any chance of save pollution.

Collector should record at minimum:
- `fixture=true`
- benchmark move
- move slot
- original move when applicable
- `restored=true`
- no save/learnset persistence after fixture exit

## Promotion rule
The fixture itself must first prove that it does not contaminate the normal save or formal learnsets. GBC-A2 runtime/visual coverage then uses the fixture and is independent of story progress. Formal builds remove the test entry point or keep it disabled-by-default and unreachable during normal play.
