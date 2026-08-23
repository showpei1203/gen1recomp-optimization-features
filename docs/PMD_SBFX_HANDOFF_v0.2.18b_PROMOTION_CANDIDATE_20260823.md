# PMD + StadiumBattleFX Handoff — v0.2.18b Promotion Candidate

Date: **2026-08-23**

## Formal Authority

Current PMD + StadiumBattleFX integration-lane source authority remains **v0.2.17e FORMAL AUTHORITY** until the fixture-free promotion smoke is accepted.

Formal hashes:
- PMD `main.lua`: `726cf94166333ea49512e05925fad3f6925ff796c669bd729d29801125103490`
- PMD `manifest.json`: `b2b0844ba43dbdc05efd57453353ad5c6f1aca003b470c53e90037f0b0d5009c`
- StadiumFxPlayer: `5d5d774994f107c567d413f4b195a6806875a729d5a1e7578b83c57e782a3c4f`

## v0.2.18a2 acceptance

A2 automated evidence passed all structural gates:
- fixture started;
- Reflect / Light Screen / Barrier / Recover each routed as `status_self`;
- each routed through `self_support_source_only`;
- opponent target VFX ownership was forbidden;
- no fixture error / runtime error.

User visual acceptance on 2026-08-23:
- all four effects normal;
- no self-support animation appeared on the enemy;
- all four effects visually distinguishable.

A2 evidence archive was stored in Google Drive `04_Test_Logs` as:
`PMD_v0218a2_SELF_SUPPORT_SOURCE_OWNERSHIP_IV_A2_EVIDENCE_20260823_193521.zip`
Drive file id: `1bu3Bh6I2DmGjmLk0J9GLVBs8v7jA-GPT`.

## Accepted presentation rule

True self / own-side support moves use **source-only visual ownership**. The opponent target anchor is forbidden from rendering those effects.

The accepted dedicated source-side renderers currently include:
- Reflect
- Light Screen
- Barrier
- Recover

This is presentation-only. Battle mechanics remain engine-owned.

## v0.2.18b fixture-free promotion candidate

Package:
`GEN1RECOMP_PMD_v0.2.18b_SELF_SUPPORT_SOURCE_OWNERSHIP_PROMOTION_CANDIDATE_20260823.zip`

Package SHA-256:
`07ee27d1aab71174bd3051e8ff6db2d2b57e4f9da20f022be936e9a7cd59b637`

Candidate hashes:
- PMD `main.lua`: `b67b2f57bb955eea1834210a471ddf0c2ef20cd50f82c145e074c9a5e0d36d46`
- PMD `manifest.json`: `f75aca6b3d0a98c56b131cc3cb6730aba772f9499df581b9cc3fdeaf261f1563`
- StadiumFxPlayer: `7e40e164f24e89c0671d6ef8a0b4fd21f68b0443232f68410b2070f100c17cd7`

## Scope proof

- A2 StadiumFxPlayer is byte-identical in v0.2.18b.
- A2 -> B PMD production change removes the embedded self-support B-key TEST fixture and adds only the promotion marker/version metadata around that removal.
- `PMD_SELF_SUPPORT_VISIBILITY_IV_A2_FIXTURE` is absent from the B candidate PMD source.
- `startSemanticAuditFixture` is absent from the B candidate PMD source.
- no battle mechanics change;
- no HIT_FRAME change;
- no Fly/Dig change;
- no Beam AV change;
- no depth change.

## Promotion smoke

Install v0.2.18b, then:
1. confirm B no longer opens the audit fixture;
2. enter one ordinary battle;
3. use at least one ordinary move and confirm PMD + Stadium presentation remains normal;
4. finish or leave the battle;
5. run `COLLECT_PMD_v0.2.18b_PROMOTION_SMOKE_EVIDENCE.bat`.

Promotion requires exact hashes, zero fixture source/runtime rows, zero runtime errors, and user confirmation that ordinary battle presentation remains normal.

Until that smoke passes, **v0.2.17e remains Formal Authority**.
