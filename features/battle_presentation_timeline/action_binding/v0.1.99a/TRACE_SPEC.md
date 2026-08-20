# Action Binding I-A Trace Spec

The trace layer observes existing runtime behavior only.

## Lifecycle events

- `ACTION_BIND START`
- `ACTION_BIND HANDOFF`
- `ACTION_BIND NATIVE_RELEASE`
- `ACTION_BIND ANIM_RELEASE`
- `ACTION_BIND HIT`
- `ACTION_BIND RECOVERY_START`
- `ACTION_BIND COMPLETE`

Each binding record carries move, PMD family/action, side, sequence id, hit index/total, source hit frame, semantic flags, and native-barrier state.

## Hard failure conditions

- duplicate Action Binding HIT for one native hit row
- unclosed binding lifecycle
- contact hit missing HIT or recovery
- contact recovery starts on a frame different from authoritative HIT
- projectile incorrectly enters contact recovery
- non-damage status receives damage HIT binding
- sustained/long-SFX presentation completes before animation/audio release
- any sealed HIT_FRAME regression: duplicate HIT authority, multi-hit continuation barrier re-arm, nonzero ANIM_RELEASE→HIT, or status false damage HIT

## Pass coverage

Core I-A must observe contact, projectile, multi-hit, sustained/long-SFX, and status. Area/full-screen is diagnostic-only in this slice.

The trace tables are stored on the existing `Volatile` namespace rather than adding outer-scope Lua locals, because the monolithic PMD main chunk is already near Lua's per-function local-variable ceiling.