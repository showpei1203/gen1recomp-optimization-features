# v0.2.02a Promotion Spec

Purpose: remove every TEST-only A2 benchmark artifact from exact v0.2.01f without changing accepted move presentation or battle timing ownership.

## Removed
- `GBC_A2_FIXTURE` state/table
- fixture deep-copy / move injection / Pokedex seen helpers
- battle-local benchmark battle launcher
- free-overworld B input hook
- fixture READY / START / END / ONCE_GUARD / BLOCKED / ERROR logs
- TEST-only fixture startup log

## Frozen
Quick Attack, Fury Swipes, Psybeam, Surf render bodies; A1 move layer; Psybeam `beam_release` semantic; GBC data/assets; HIT_FRAME and Action Binding hard ownership; native animation/audio/barrier timing; Depth/DS/THOR.

No replacement debug key or hidden progression bypass is added. Formal gameplay must use normal input behavior.