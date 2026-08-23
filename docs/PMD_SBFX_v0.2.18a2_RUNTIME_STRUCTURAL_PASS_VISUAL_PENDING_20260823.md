# PMD + StadiumBattleFX — v0.2.18a2 Runtime Structural Result

Date: **2026-08-23**

Status: **RUNTIME STRUCTURAL PASS / VISUAL ACCEPTANCE PENDING**

Formal Authority remains **v0.2.17e**. Do not promote v0.2.18a2 until visual acceptance is explicitly confirmed.

## Evidence

Evidence package:
`PMD_v0218a2_SELF_SUPPORT_SOURCE_OWNERSHIP_IV_A2_EVIDENCE_20260823_193521.zip`

Auto-check result:
- `FIXTURE_START_ROWS=1`
- `FIXTURE_ERROR_ROWS=0`
- `REFLECT_STATUS_SELF_ROWS=1`
- `LIGHT_SCREEN_STATUS_SELF_ROWS=1`
- `BARRIER_STATUS_SELF_ROWS=1`
- `RECOVER_STATUS_SELF_ROWS=1`
- `REFLECT_SOURCE_ONLY_ROWS=1`
- `LIGHT_SCREEN_SOURCE_ONLY_ROWS=1`
- `BARRIER_SOURCE_ONLY_ROWS=1`
- `RECOVER_SOURCE_ONLY_ROWS=1`
- `RUNTIME_ERROR_ROWS=0`
- `RESULT=PASS`

Observed ownership log rows confirm for all four audited moves:
- `mode=self_support_source_only`
- `side=player`
- `targetVfx=forbidden`

The runtime therefore structurally proves that Reflect, Light Screen, Barrier, and Recover are routed as source-only player-side presentation and no opponent target anchor is intentionally owned by these effects.

## Remaining visual gate

The evidence package contains an unfilled `USER_RESULT.txt` template. Therefore the following cannot be inferred from logs and remain visually unverified:
- Reflect visibly appears on player only;
- Light Screen visibly appears on player only;
- Barrier visibly appears on player only;
- Recover visibly appears on player only;
- no self-support VFX is visibly drawn on the enemy;
- all four effects are visually distinguishable.

Static inspection confirms dedicated renderers exist for Reflect, Light Screen, Barrier, and Recover and all use `anchor("attacker")`, but static code presence is not a substitute for device-side visual acceptance.

## Promotion rule

v0.2.18a2 may only advance after explicit human visual confirmation of the six gates above. Until then, **v0.2.17e remains Formal Authority**.
