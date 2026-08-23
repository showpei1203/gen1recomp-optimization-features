# PMD + StadiumBattleFX Move Presentation Authority — v0.2.18b Formal Authority

Status: **FORMAL AUTHORITY**

Promoted: **2026-08-23**

Supersedes for this integration lane: **v0.2.17e Formal Authority**.

User acceptance lineage:
- v0.2.18a2 self-support visual acceptance: four effects normal; no enemy self-support VFX; effects distinguishable.
- v0.2.18b fixture-free promotion smoke uploaded and user explicitly continued to the next integration stage.

## Formal production identity

- PMD version: `v0.2.18b`
- PMD `main.lua`: `b67b2f57bb955eea1834210a471ddf0c2ef20cd50f82c145e074c9a5e0d36d46`
- PMD `manifest.json`: `f75aca6b3d0a98c56b131cc3cb6730aba772f9499df581b9cc3fdeaf261f1563`
- StadiumBattleFX `lib/effects/StadiumFxPlayer.lua`: `7e40e164f24e89c0671d6ef8a0b4fd21f68b0443232f68410b2070f100c17cd7`
- v0.2.18b promotion-candidate ZIP: `07ee27d1aab71174bd3051e8ff6db2d2b57e4f9da20f022be936e9a7cd59b637`
- v0.2.18b promotion-smoke evidence ZIP: `be4a06e20ad0bf468adca0e4cda412930791ce03a310b11b9b96ce6b1d391e94`
- Drive evidence file id: `1rIsC0Ss_YKaKbd7roDBh_3nT1QjLCgZs`

## Inherited sealed architecture

All v0.2.17e rules remain sealed unless explicitly superseded below:

1. StadiumBattleFX remains external move-VFX provider and VFX-only for this integration.
2. Stadium `BattleHost.begin()` presentation ownership remains prohibited.
3. `BattleState.applyHitFx` remains the sole HIT_FRAME owner.
4. PMD source-pose de-dup and HOME-facing contact recovery remain active.
5. PMD source-body motion remains driven by the accepted visible-time clock.
6. Visible native PMD `head` and native visible `lunge` / LeapForth remain globally forbidden.
7. Player visible PMD remains the legacy 2D overlay; player 3D is shadow-only. Enemy visible PMD remains the accepted depth-tested 3D card.
8. DRAMATIC_SHAPE lighting parity and wide-screen ScreenFx geometry rules remain inherited.
9. Surf and Fury Swipes fixes remain sealed.
10. Fly / Dig remain PMD-body-owned two-turn presentation moves with a single source/travel owner and hit-only second-turn native queue handoff.
11. Beam primary/travel AV timing remains separate from impact timing.
12. Freeze target ownership and Leech Seed residual ownership remain sealed.

## Self-Support Source Ownership IV

True self / own-side support moves use **source-only visual ownership**.

Rules:
- the attacker/source owns the presentation anchor;
- opponent target anchors are forbidden for the self-support VFX;
- battle mechanics remain engine-owned and unchanged;
- visual classification must reflect where the effect actually occurs, not merely that a move executed.

Representative accepted moves:
- Reflect
- Light Screen
- Barrier
- Recover

Accepted visual behavior:
- Reflect: source-side mirror/barrier presentation;
- Light Screen: visible source-side light screen;
- Barrier: visible source-side enclosing barrier;
- Recover: visible source-side recovery particles/ring;
- none of these four renders its self-support VFX on the opponent;
- all four are visually distinguishable in user device acceptance.

The broader classic self-support semantic family remains source-only where the move genuinely targets self/own side. Target-affecting status moves must not be swept into this rule merely because they are non-damaging.

## Promotion evidence

v0.2.18a2 runtime evidence:
- fixture START present;
- REFLECT / LIGHT_SCREEN / BARRIER / RECOVER each classified `status_self`;
- each enters `self_support_source_only`;
- `targetVfx=forbidden`;
- no fixture BLOCKED/ERROR;
- no runtime error;
- automated check PASS.

User visual acceptance:
- four effects normal;
- enemy has no self-support animation;
- effects can be distinguished.

v0.2.18b fixture-free promotion smoke:
- exact candidate hashes matched install;
- `TEST_FIXTURE_SOURCE_ROWS=0`;
- `TEST_FIXTURE_RUNTIME_ROWS=0`;
- `RUNTIME_ERROR_ROWS=0`;
- ordinary Thundershock completed PMD Action Binding and Stadium animation lifecycle;
- battle emitted `battle ended`;
- automated result PASS;
- user explicitly continued to the next integration stage after submitting the evidence.

## Fixture seal

Formal v0.2.18b contains no embedded B-key self-support audit fixture.

## Next integration lane

Kanto Dynamic Weather + Wild Skies integration work must branch from these exact v0.2.18b production hashes. Weather/overworld renderer changes must not silently alter the sealed battle-presentation ownership above.

## Scope boundary

This remains a formal **PMD + StadiumBattleFX integration-lane source authority**. It does not by itself replace the separately pending full runnable binary baseline import/hash-pin authority.
