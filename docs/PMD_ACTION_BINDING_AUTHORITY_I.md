# PMD Action Binding Authority I

Status: **RUNTIME PASS / FORMAL AUTHORITY**

Accepted build: `pmd_idle_battle_sprites v0.1.99b`

Depends on:
- PMD HIT_FRAME Authority I (`v0.1.98b`)
- DRAMATIC_SHAPE 1.8.2 accepted Depth/Occlusion Authority
- thor_battle_ui 0.3.41 accepted compatibility hash

## Accepted hashes

- PMD main.lua: `b2f8f143f7298d5b0744c30bc885df5cca1eb109a073c515bbcc6eeedb4eed64`
- PMD manifest.json: `c9351afd39ce30ca25428dcd359b8687bd7f6f92d2f44bf5ca3b92fa74d45aa4`
- Candidate ZIP: `8c32d53f3dff270a309fca6b66c994240b4de92ff6ddfb428577e67f4c7a1233`
- Formal Evidence ZIP: `59f498b71f8d31e5ed2f694686f2cdfddaed6fe9032790bfc78cd7c549e124de`
- DRAMATIC_SHAPE OverworldBattle.lua: `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DRAMATIC_SHAPE BattleScene.lua: `bca552070e26c9ac6554f8cc387ffb34036a76722b7be9c5d3184974237873cc`
- THOR Battle UI main.lua: `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`

## Authority rules

1. `BattleState.applyHitFx` remains the sole HIT_FRAME owner. Action Binding consumes that authority and does not redefine impact timing.
2. PMD presentation is correlated through `START → HANDOFF → NATIVE_RELEASE → ANIM_RELEASE → HIT → RECOVERY/COMPLETE`.
3. Contact actions require authoritative HIT and contact recovery on the HIT frame.
4. Projectile actions detach source-body commitment after handoff and must not inherit contact recovery. Ember is the reference projectile benchmark.
5. Multi-hit uses one sequence with row-level ownership. Continuation rows must not re-arm the native presentation barrier.
6. Sustained/long-SFX actions must not let the PMD source body return to ambient before native animation/audio release. If source motion exhausts while `battle.animPlaying` remains true, v0.1.99b holds the semantic source hitFrame via `SUSTAIN_HOLD` until existing audio-tail ownership takes over. No new timer exists.
7. Non-damage status/self actions must not create damage HIT authority.
8. Area/full-screen is observer-only in Action Binding I and was not required for the formal five-family closure gate.
9. DRAMATIC_SHAPE, THOR, Depth/Occlusion, Presentation-vs-Physical-Feet separation, Large Pokémon Bounds, player BACK SPRITES policy, and species scale are outside Action Binding Authority and remain sealed/unchanged.

## Global PMD visible-action hard constraints

Effective 2026-08-22 for all future PMD candidates:

- **Visible PMD `action=head` is forbidden for every species and every runtime context.**
- Reason: extracted `*_head.png` strips can contain only a detached head crop rather than a complete-body combat pose, producing a visibly invalid floating-head result.
- Semantic family `head` may remain for move classification, timing, HIT/recovery tuning and move-effect semantics; it must never imply rendering the PMD `head` asset.
- Full-body fallback order for a semantic head request is: `lunge → charge → strike → attack`.
- This rule applies to normal moves, multi-hit mapping, ambient/small actions, test fixtures and any future feature code.
- A central renderer/asset guard is required so that even a future accidental `motionAssetFor(..., "head")` request is redirected before asset lookup.
- Promotion of any later PMD build requires zero visible detached-head incidents and zero runtime `ACTION_BIND ... action=head` ownership for visible bodies.

This is a **project hard constraint**, not a claim that v0.1.99b itself implemented the later redirect. Current implementation/promotion evidence is tracked in the active StadiumBattleFX integration candidate line.

## Formal closure

Session-safe re-analysis across Android PID 7831 and PID 9520:

- Contact rows: 9; missing HIT 0; missing recovery 0; recovery off HIT 0
- Projectile rows: 1; Ember `family=projectile`, `action=shot`, `projectile=true`
- Multi-hit rows: 3; one Fury Swipes 3-hit sequence
- Sustained audio-tail rows: 1; early COMPLETE before ANIM_RELEASE = 0
- Non-damage status rows: 12; unexpected ACTION_BIND HIT = 0
- ACTION_BIND HIT duplicate = 0
- ACTION_BIND missing COMPLETE = 0
- HIT_AUTH duplicate = 0
- HIT_AUTH continuation barrier re-arm = 0
- HIT_AUTH ANIM_RELEASE→HIT non-zero = 0
- HIT_AUTH status false hit = 0
- no current FATAL EXCEPTION, application ANR, LOVE error, stack traceback, or attempt-to runtime error

### Ember reference

PID 9520 / id 1:
- START 782
- HANDOFF 783
- NATIVE_RELEASE 784
- ANIM_DONE 872
- ANIM_RELEASE 872
- HIT_AUTH FIRE 872
- `owner=applyHitFx`
- `sourceHitFrame=1`
- `duplicate=false`
- `continuationBarrierRearm=false`
- `fromAnimRelease=0`

### Sustained reference

v0.1.99a exposed Thundershock source-body completion 43f and 71f too early. v0.1.99b closes that gap with the minimal sustained-family `SUSTAIN_HOLD` rule. Formal closure retains Thundershock COMPLETE one frame after ANIM_RELEASE.

## Evidence

Google Drive:
- Formal Evidence Folder: `1usNdR_fDImeRNKM3_pGHCC9oE0SYTOXn`
- Formal Evidence ZIP: `1gFz2xvwOKRkNndG-TUug8lph1HysmRuq`
- Formal Authority Doc: `1FY8-8sLDtLzwU0beED76ofWPRAlHb2uOqcqj2SBDT3Q`

## Collector tooling note

Session-Safe Collector V2 failed because PowerShell treats `$pid` as the built-in read-only `$PID` automatic variable, case-insensitively. This is a collector-only defect. V3 renames the variable to `$procId`. Runtime evidence and formal promotion are unaffected.

## Next mainline

Gen2/GBC Colored Move Animation Layer must consume the sealed Presentation Timeline + HIT_FRAME + Action Binding Authorities. It must not introduce a separate hit/impact clock.
