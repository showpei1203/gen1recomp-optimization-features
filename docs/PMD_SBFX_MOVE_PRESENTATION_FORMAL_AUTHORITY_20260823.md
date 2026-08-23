# PMD + StadiumBattleFX Move Presentation Authority — Formal Authority

Status: **FORMAL AUTHORITY**

Promoted: **2026-08-23**

Supersedes for this integration lane: **v0.2.13a Integration I Formal Authority**.

User acceptance: v0.2.17d two-turn body-owned presentation accepted with `ok`; v0.2.17e fixture-free promotion smoke accepted with `ok 繼續推進`.

## Formal production identity

- PMD version: `v0.2.17e`
- PMD `main.lua`: `726cf94166333ea49512e05925fad3f6925ff796c669bd729d29801125103490`
- PMD `manifest.json`: `b2b0844ba43dbdc05efd57453353ad5c6f1aca003b470c53e90037f0b0d5009c`
- StadiumBattleFX `lib/effects/StadiumFxPlayer.lua`: `5d5d774994f107c567d413f4b195a6806875a729d5a1e7578b83c57e782a3c4f`
- v0.2.17e promotion-candidate ZIP: `95658c9f4bf18025c2b1ae6c479f65c532e64833cc0660918ed6ad675cbab781`
- v0.2.17e promotion-smoke evidence ZIP: `ec062594438447b7c1aca219ce46c3c7178bf95349235874dd4e5cbfbf7c1563`
- v0.2.17d two-turn evidence ZIP: `061d9b1dd1898539ef90951bf01ee82e54931655174f33a76c422cf5712ad73e`
- Formal Authority archive ZIP: `b1ae2db1f6c1d66c147210af9715f0c89c415793cb9d1a9c07b879865c461526`

Pinned unchanged dependencies inherited from the prior formal authority:

- StadiumBattleFX `main.lua`: `a27f954583b098a491d698a04610bb4caf3c1ba2c70c4515ea134cfb4178fb69`
- DRAMATIC_SHAPE `OverworldBattle.lua`: `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DRAMATIC_SHAPE `BattleScene.lua`: `4c05b8788e3cd64ea64e6905c2ba623e1d69722a44387c8f193b2ad76992f3c0`
- DRAMATIC_SHAPE `Voxel3D.lua`: `399e45e4549ad844885acc1c98fbb3756e7975f1376bbb0318bd54bc6c29af75`
- THOR Battle UI `main.lua`: `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`

## Inherited sealed architecture

1. StadiumBattleFX remains external move-VFX provider and remains VFX-only for this integration.
2. Stadium `BattleHost.begin()` presentation ownership remains prohibited.
3. `BattleState.applyHitFx` remains the sole HIT_FRAME owner.
4. PMD source-pose de-dup and HOME-facing contact recovery remain active.
5. PMD source-body motion remains driven by the accepted visible-time clock.
6. Visible native PMD `head` and native `lunge` / LeapForth remain globally forbidden. Semantic families remain allowed with full-body safe fallbacks.
7. Player visible PMD remains the legacy 2D overlay; player 3D is shadow-only. Enemy visible PMD remains the accepted depth-tested 3D card.
8. DRAMATIC_SHAPE lighting parity and wide-screen ScreenFx geometry rules remain inherited from v0.2.13a.
9. Surf and Fury Swipes Integration I fixes remain sealed.

## Move Catalog / AV authority added after v0.2.13a

### Semantic routing

- move/effect interaction semantics outrank Gen1 physical/special fallback where appropriate;
- Gust / Acid / Sludge / Smog and other visually ranged exceptions route as projectile semantics;
- Night Shade routes as special cast;
- physical-by-type ranged moves such as Swift / Rock Throw / Bonemerang / Egg Bomb do not fall through to contact strike;
- Earthquake / Fissure use area-release semantics;
- non-damaging target effects are separated from true self-status effects;
- String Shot / Leech Seed use target-projectile semantics;
- Powder / Spore family uses target-field semantics;
- Reflect remains self-support semantics;
- Seismic Toss / Submission use `grapple_throw` / `grapple_slam` body semantics.

### AV timing

- exact move `Source` ownership is used for non-beam adaptive AV timing;
- Beam primary and impact phases are separate ownership domains;
- beam SE may extend the emitted beam/travel phase but must not stretch or replay target impact animation;
- later sound rows do not steal Beam primary timing ownership;
- residual static final-frame holds remain bounded.

### Status / residual / self-guard presentation

- Freeze feedback ownership is target-correct; a frozen enemy does not paint the player as frozen;
- Leech Seed initial seed launch and end-turn residual drain are separate phases;
- end-turn Leech Seed residual is target -> healer drain-only and does not replay the seed launch;
- stale `battle.move_used` context cannot override auxiliary animation anchor ownership;
- Protect has a presentation-only self guard when no Stadium registry row exists; mechanics remain engine-owned;
- Reflect retains Stadium/audio content and adds a distinct visible self-barrier presentation.

## Two-turn movement authority

`FLY` and `DIG` are **PMD-body-owned source/travel presentation moves**.

Turn 1:
- short PMD preparation;
- Fly departs upward, Dig departs downward;
- PMD remains visually absent while engine charging/semi-invulnerability continues;
- the engine/native auxiliary charge presentation row is suppressed as a presentation no-op only after PMD departure;
- battle mechanics are not suppressed.

Turn 2:
- PMD re-enters at the target: Fly from above, Dig from below;
- at PMD HANDOFF the original native move queue row retains the exact engine `hit` table but becomes hit-only;
- no second HOME-anchored Stadium/native source or travel VFX may start;
- `applyHitFx` owns target hurt/damage;
- PMD holds briefly at impact, returns target -> HOME, then explicitly resets combat/transient state and resumes ambient animation.

This single-source rule is required because Stadium/native attacker anchors are battle-side HOME anchors and do not follow PMD body translation.

## Closure evidence

v0.2.17d two-turn evidence:
- Fly charge native suppressed: `1`
- Dig charge native suppressed: `1`
- Fly release hit-only: `1`
- Dig release hit-only: `1`
- Fly ambient resumed: `1`
- Dig ambient resumed: `1`
- forbidden native Fly/Dig/Teleport/SlideDown source VFX: `0`
- no duplicate HIT / continuation re-arm / visible head / visible native lunge regression
- no LOVE traceback / FATAL / ANR

v0.2.17e fixture-free smoke:
- exact PMD / manifest / StadiumFxPlayer hashes matched candidate
- `ERROR_ROWS=0`
- `TEST_FIXTURE_RUNTIME_ROWS=0`
- PMD mod loaded as `0.2.17e`
- PMD depth bridge activated in battle
- representative Thundershock completed Action Binding + Stadium animation lifecycle
- battle emitted `battle ended`
- user accepted smoke with `ok 繼續推進`

## Fixture seal

Formal v0.2.17e contains no embedded B-key semantic/two-turn fixture. The promotion candidate was produced by removing the exact TEST fixture block from accepted v0.2.17d while preserving production runtime logic.

## Scope boundary

This is the formal **PMD + StadiumBattleFX integration-lane source authority**. It does not claim that the separate full runnable Gen1Recomp binary baseline has been imported and SHA-256 pinned in Drive.

Future PMD battle-presentation work must branch from the exact v0.2.17e formal hashes above unless a later authority explicitly supersedes them.