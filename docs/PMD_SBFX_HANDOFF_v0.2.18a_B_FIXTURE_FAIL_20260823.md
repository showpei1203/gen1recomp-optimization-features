# PMD + StadiumBattleFX Handoff — v0.2.18a B Fixture Fail

Date: **2026-08-23**

## Formal Authority

Current PMD + StadiumBattleFX integration-lane source authority is **v0.2.17e FORMAL AUTHORITY**.

Canonical authority:
`docs/PMD_SBFX_MOVE_PRESENTATION_FORMAL_AUTHORITY_20260823.md`

Formal hashes:
- PMD `main.lua`: `726cf94166333ea49512e05925fad3f6925ff796c669bd729d29801125103490`
- PMD `manifest.json`: `b2b0844ba43dbdc05efd57453353ad5c6f1aca003b470c53e90037f0b0d5009c`
- StadiumFxPlayer: `5d5d774994f107c567d413f4b195a6806875a729d5a1e7578b83c57e782a3c4f`
- Formal archive ZIP: `b1ae2db1f6c1d66c147210af9715f0c89c415793cb9d1a9c07b879865c461526`

Full runnable binary baseline remains separately `PENDING_BINARY_IMPORT_AND_HASH_PIN`.

## v0.2.17e sealed presentation results

- StadiumBattleFX remains VFX-only; `BattleHost.begin()` presentation ownership remains forbidden.
- `BattleState.applyHitFx` remains sole HIT_FRAME authority.
- visible PMD `head` and native visible `lunge` / LeapForth remain forbidden.
- Beam primary AV phase remains separate from impact phase.
- Freeze feedback ownership remains target-correct.
- Leech Seed residual is drain-only and does not replay initial seed launch.
- Reflect self-barrier presentation retained.
- Fly / Dig are PMD-body-owned two-turn presentation moves with a single visual source authority.
- first-turn native Fly/Dig charge visuals are presentation-suppressed after PMD departure.
- second-turn native Fly/Dig move rows become hit-only while preserving exact engine hit tables.
- `applyHitFx` owns target hurt/damage.
- Fly/Dig return HOME and explicitly resume PMD ambient animation.
- Seismic Toss = `grapple_throw`; Submission = `grapple_slam`.
- embedded B-key TEST fixture was removed before v0.2.17e promotion.

## Current development candidate

**v0.2.18a Self-Support Visibility Audit IV-A TEST**

Package SHA-256:
`42b56ab078018d29e4f04cb688682bcfe712328c93348e30705099a9626e9a7b`

Candidate hashes:
- PMD `main.lua`: `507e21c82d6c2808abbd39ae58c4d648e15ef3e6d9ad46123f4cf17181037e7c`
- PMD `manifest.json`: `c65114a04a31979f8c05dc52d2797ba12795721d1f9096d6a0a2ccc7510aa9e6`
- StadiumFxPlayer unchanged: `5d5d774994f107c567d413f4b195a6806875a729d5a1e7578b83c57e782a3c4f`

Production delta only expands `actionBindSelfNames` presentation classification for classic self-buffs such as Barrier, Swords Dance, Agility, Harden, Withdraw, Amnesia, etc. Battle mechanics are unchanged.

TEST fixture intended moves:
1. PROTECT
2. LIGHT SCREEN
3. BARRIER
4. RECOVER

Enemy: GROWL.

## Current blocker

User runtime report:

> Pressing B does not enter the test battle.

Therefore v0.2.18a is **UNVERIFIED / TEST-HARNESS FAIL** and must not be promoted.

Static source inspection confirms the B-key hook exists. The fixture resolves every requested move before creating/pushing the battle, and aborts the whole fixture on the first unresolved move.

Highest-probability root is `PROTECT`: Protect engine/effect support exists in the codebase's Gen2 path, but that does not prove the active Gen1/Kanto `GameCore.data.moves` contains a Protect move row. Because PROTECT is the first requested fixture move, an unresolved Protect would return `missing_move_PROTECT`, log `BLOCKED`, skip `pushBattle()`, then fall back to normal overworld input. This exactly matches the reported symptom.

This is a high-confidence static diagnosis, **not yet runtime-proven** because a B-failure log was not collected before handoff.

## Immediate next action

1. Do not alter or downgrade v0.2.17e Formal Authority.
2. On installed v0.2.18a, stand still on overworld and press B once.
3. Run the handoff collector `COLLECT_v0.2.18a_B_FIXTURE_FAIL_EVIDENCE.bat`.
4. Inspect `READY`, `START`, `BLOCKED`, `ERROR`, and especially `missing_move_PROTECT`.
5. If `missing_move_PROTECT` is confirmed, make **v0.2.18a1 TEST-HARNESS-ONLY repair**:
   - use `REFLECT / LIGHT SCREEN / BARRIER / RECOVER` for the Gen1-active fixture;
   - keep the v0.2.18a production self-semantic delta unchanged;
   - do not inject Protect into gameplay merely to make a fixture pass;
   - audit Protect separately only where its move data genuinely exists or via an explicitly synthetic non-gameplay audit.
6. The repaired collector must hard-gate `FIXTURE_START_ROWS >= 1`; pressing B without a `START` row is an automatic fixture FAIL.

## Required pre-delivery discipline

After the Fly/Dig regression sequence, future presentation candidates must self-check all of the following before handoff to the user:
- exactly one visible source/travel owner;
- VFX spatial origin is logically attached to a visible source when required;
- prep -> travel -> HIT -> recovery causal ordering;
- correct target/side ownership;
- no duplicate HIT authority;
- queue handoff cannot depend on a deliberately hidden body;
- HOME/recovery clears transient state;
- ambient PMD animation resumes after recovery;
- negative regression gates, not only positive phase markers;
- Lua load order / runtime hook installation;
- TEST fixture itself actually starts.

Do not accept phase-marker presence alone as proof of visual correctness.