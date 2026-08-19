# Battle Presentation Priorities

Date: 2026-08-19
Priority: P0

## Goal 1 — Battle Presentation Timeline Authority

Unify PMD sprite actions, move VFX, move SFX, hit frames, damage/status presentation and recovery under one frame-based timeline.

Required timeline markers:
- PREPARE
- ACTION_START
- VFX_START
- SFX_START
- HIT_FRAME
- RECOVERY
- COMPLETE

Rules:
- No independent wall-clock timers for sprite/VFX/SFX presentation.
- Multi-hit moves expose repeated HIT_FRAME markers.
- Charge moves support phase-separated timelines.
- Sustained/looping SFX must have an explicit stop/fade policy.
- Natural one-shot SFX tails may extend the presentation recovery when appropriate.
- Sprite action returns to battle idle only after the move presentation reaches COMPLETE.

First defect target: animation completes while move SFX continues, plus weak synchronization between PMD sprite action and move presentation.

## Goal 2 — Gen2 GBC Colored Move Animation Layer

Use Pokémon Gold/Silver/Crystal-style colored battle animation presentation as the primary visual direction.

Implementation direction:
- build reusable animation commands rather than one-off hardcoded sequences
- palette/background effects
- animation objects/projectiles/hit particles
- timed waits and callbacks
- synchronized SFX triggers
- per-move scripts mapped onto the Timeline Authority

Reference behavior should be derived from the Gen2 battle animation command structure and move scripts, then adapted to Gen1recomp rather than blindly copying the current asynchronous playback path.

## Development order

1. Build Timeline Authority.
2. Validate representative benchmark moves.
3. Implement the Gen2 colored animation layer on the same timeline.
4. Expand by move families/templates.
5. Add per-move exceptions only when required.
6. Full regression and AYN Thor acceptance.

Initial benchmark set should include at minimum:
- single projectile
- melee hit
- multi-hit
- long/sustained SFX move
- area/background-effect move
- status/self-target move
