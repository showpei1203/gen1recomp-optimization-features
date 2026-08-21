# v0.2.01f Patch Spec — Psybeam Non-Contact Binding

Observed v0.2.01e defect: Psybeam beam is visually seamless, but the attacker Pikachu flashes/jumps for one frame at damage. Evidence identifies `family=strike action=attack` followed at HIT by `ACTION_BIND RECOVERY_START mode=contact_recovery` and `HIT_AUTH POSE sourceHitFrame=3`.

Patch scope is deliberately narrow: before generic special routing, `moveActionForQueue()` explicitly maps PSYBEAM to family `beam_release`. If native Shot exists, action=`shot`; otherwise the current source-aware strike/attack body action is preserved. The family change prevents contact recovery without changing the source body animation itself.

Expected semantics: `contact=false`, `projectile=true`, `sustained=true`; no Psybeam attacker recovery at HIT; HIT_AUTH `behavioral=false`.

Frozen: GBC Psybeam renderer/continuation, Quick Attack, Fury Swipes, Surf, GBC assets/data, HIT_FRAME implementation, Action Binding callbacks, damage, audio, barrier, Depth, DRAMATIC_SHAPE and THOR UI.

Formal release still must remove the TEST-only B fixture.
