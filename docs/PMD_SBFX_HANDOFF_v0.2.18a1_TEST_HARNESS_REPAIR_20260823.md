# PMD + StadiumBattleFX Handoff — v0.2.18a1 TEST-HARNESS Repair

Date: **2026-08-23**

## Formal Authority remains unchanged

Current PMD + StadiumBattleFX integration-lane source authority remains **v0.2.17e FORMAL AUTHORITY**.

Formal hashes:
- PMD `main.lua`: `726cf94166333ea49512e05925fad3f6925ff796c669bd729d29801125103490`
- PMD `manifest.json`: `b2b0844ba43dbdc05efd57453353ad5c6f1aca003b470c53e90037f0b0d5009c`
- StadiumFxPlayer: `5d5d774994f107c567d413f4b195a6806875a729d5a1e7578b83c57e782a3c4f`

Do not promote v0.2.18a or v0.2.18a1 without runtime acceptance.

## Why v0.2.18a1 exists

v0.2.18a runtime report was: pressing B did not enter the TEST battle.

Static inspection showed the fixture resolves all requested moves before `pushBattle()`. `PROTECT` was first in the requested list, while the active Gen1/Kanto move data may not expose Protect even though Protect engine support exists elsewhere. Therefore `missing_move_PROTECT` was the highest-probability root, but it was **not runtime-proven** because no B-failure log was collected before handoff.

v0.2.18a1 removes this unnecessary data-lane dependency regardless of the exact original B-fail cause. It is a **TEST-HARNESS-ONLY repair**.

## v0.2.18a1 exact identity

Package:
`GEN1RECOMP_PMD_v0.2.18a1_SELF_SUPPORT_VISIBILITY_AUDIT_IV_A1_TEST_20260823.zip`

Package SHA-256:
`9180251c1206cb86b95483aff0edf201f3352b80040988a345f0fc204549f0d7`

Drive test-build file:
`https://drive.google.com/file/d/1yeNK9g8GViyCDrygo-wRu7R_uHha8p2Z/view?usp=drivesdk`

Candidate hashes:
- PMD `main.lua`: `a2c92eb5714b59b2056331142296c1ab8d03903403572e23124c2c016125322e`
- PMD `manifest.json`: `58020fb6a3ddfc695c0d552bda3a9a7049f5044fbee809135003b772c5c5e83c`
- StadiumFxPlayer required unchanged: `5d5d774994f107c567d413f4b195a6806875a729d5a1e7578b83c57e782a3c4f`

## Scope proof

The v0.2.18a production `actionBindSelfNames` block is byte-identical in v0.2.18a1.

Block SHA-256:
`5e9f10822e5a76cca64bcde07972a7de24396bb995de5cea24d2007036d92c16`

Only the TEST harness dependency/log namespace/versioning and collector were changed. No battle mechanics, HIT_FRAME authority, Fly/Dig ownership, Beam AV timing, depth rules, StadiumFxPlayer bytes, or production self-semantic classification were changed.

## A1 fixture

Player moves:
1. REFLECT
2. LIGHT SCREEN
3. BARRIER
4. RECOVER

Enemy move: GROWL.

Recover still begins from half HP to ensure a visible successful heal.

## Collector hard gates

`COLLECT_PMD_v0.2.18a1_SELF_SUPPORT_VISIBILITY_EVIDENCE.bat` now records:
- FIXTURE READY rows
- FIXTURE START rows
- FIXTURE BLOCKED rows
- FIXTURE ERROR rows
- status_self ACTION_BIND rows for all four moves

Hard rules:
- `FIXTURE_START_ROWS >= 1`
- `FIXTURE_ERROR_ROWS = 0`
- each of REFLECT / LIGHT_SCREEN / BARRIER / RECOVER must produce at least one `status_self` ACTION_BIND row

If B is pressed but no START row exists, the collector returns `FAIL_FIXTURE_NOT_STARTED` instead of producing an ambiguous success-looking evidence ZIP.

## Runtime acceptance required

1. Install v0.2.18a1.
2. Launch game and stand still on overworld.
3. Press B once. The fixture battle must actually open.
4. Use Reflect / Light Screen / Barrier / Recover.
5. Confirm all effects appear on the player side only and are visually recognizable.
6. Run the A1 collector and return the evidence ZIP.

Until these checks pass, **v0.2.17e remains the only Formal Authority** for this integration lane.
