# SOULGOLD M2R10B PROVIDER GATE ALIGNMENT AUTHORITY (2026-08-31)

## Observed failure
User M2R10 launch reached provider-registry preflight and failed only at:
`dynamic_runtime_path=FAIL` -> `M2R6_PROVIDER_REGISTRY=FAIL`.

## Root cause
The production/runtime host had already evolved in M2R9 Sprite Lab from the old direct call
`load_showdown_clip(proxy.species, ...)` to the visual-only selector path:
`proxy.species -> sprite_lab_display_species -> display_species -> requested_species -> load_showdown_clip`.

`validate_m2r6_provider_registry.py` still asserted the obsolete literal text
`load_showdown_clip(proxy.species`, so the validator rejected the newer valid architecture.
This was a stale static gate, not a runtime provider failure and not a scaling failure.

## M2R10B fix
The provider static gate now requires all of the following:
- `/showdown/` dynamic asset path remains present;
- `requested_species=display_species[battler]`;
- display species derives from `sprite_lab_display_species(battler,proxy.species)`;
- runtime loading calls `load_showdown_clip(requested_species, ...)`;
- production fallback still revokes `proxy.species` on real provider failure;
- Sprite Lab failure remains visual-only and does not mutate production registry.

## Regression
R-SD-038: provider-registry static gate must accept the visual-lab requested-species path while retaining native fallback ownership.

## Local validation
All preflight validators used by the stage pass locally, including:
- M2R5B patcher fixture
- M2R6 provider registry
- M2R8F presentation stack
- M2R9 sprite lab
- M2R9C compile order
- M2R10 size profile
- M2R6B boot sync
- M2R6C teardown dialog Z
- M2R7 scaleout
- bash syntax for M2R10B stage
