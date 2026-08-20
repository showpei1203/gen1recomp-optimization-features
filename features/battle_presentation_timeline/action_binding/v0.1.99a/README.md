# PMD Action Binding I-A — v0.1.99a Trace Baseline

Status: **TEST-only / STATIC PASS / awaiting Thor runtime evidence**

Base Authority: `pmd_idle_battle_sprites v0.1.98b` HIT_FRAME Authority I Runtime PASS.

## Purpose

Measure the existing PMD action-binding behavior before changing presentation. This candidate is trace-only: it records which PMD action/family is selected and correlates START → HANDOFF → NATIVE_RELEASE → ANIM_RELEASE → HIT → RECOVERY_START → COMPLETE against the sealed HIT_FRAME Authority.

## No behavioral changes

- no motion-selection change
- no timing change
- no damage/status change
- no audio change
- no native barrier change
- no DRAMATIC_SHAPE or THOR Battle UI modification
- no depth / scale / Large Pokémon Bounds change
- no Nidoran/Vulpix size normalization; that observation is deferred as a non-regression presentation issue

## Static validation

`27/27 PASS`, including full Lua 5.4 parser load of candidate `main.lua`.

Candidate hashes:
- PMD main.lua: `276e3f7e86b3dfbb6b004bb80f8a8ee1697e2a6ccc656884bd8411606341cda2`
- manifest.json: `c1f60336175503613eddb702841b3a8db4e5d2d7c67aba57378f7dec0c9b5110`
- test ZIP: `b6562b90a3fd8c4ac5fac930adfd0e4ae11134b19fb4e3522ea569fb8a815c51`

Drive:
- Test Folder: `1afY9rjp5MDHWSs9gxSHufTI4u0wm3dbO`
- ZIP: `1NOurYy6OpP0tNp_G4q4tC19dFdiioZ0G`

## Core I-A Thor coverage

Required for a complete trace baseline:
1. Contact: Quick Attack preferred; Tackle / Scratch / Poison Sting / Low Kick also count.
2. Projectile: Ember or Gust.
3. Multi-hit: Fury Swipes.
4. Sustained / long-SFX: Thundershock, with actual audio-tail evidence.
5. Status: Sand Attack or Thunder Wave.

Area/full-screen is observer-only in I-A. A dedicated area fixture belongs to the next slice if needed.

Do not promote this branch until Thor evidence confirms lifecycle ownership and no sealed HIT_FRAME regression.