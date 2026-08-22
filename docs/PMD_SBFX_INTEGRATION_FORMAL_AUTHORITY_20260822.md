# PMD + StadiumBattleFX Integration I — Formal Authority

Status: **FORMAL AUTHORITY**

Promoted: **2026-08-22**

User approval: explicit `升格 Formal Authority` after v0.2.12a closure and v0.2.13a no-fixture promotion candidate.

## Formal production identity

- PMD version: `v0.2.13a`
- PMD `main.lua`: `7365476702ab294ad75b5c52e9e69dff9710c608ea57dc806e540e7b1650d406`
- PMD `manifest.json`: `20eec657f82f85d486bcd25b714e03d0d4ac4873dd638cf363d75879ee718c4a`
- StadiumBattleFX `lib/effects/StadiumFxPlayer.lua`: `7c8c52373f894b8b821f582b875748631897d8daf89366d0aa49ba7af668b279`
- Promotion-candidate delivery ZIP: `07970c40683f5c70da3b25602c8661ac13cc7aa1673d1036d3f541c97b38902e`
- Formal Authority archive ZIP: `9f30ced7e9748578d1db406d03210260acda85ff43fb3c9fa1d570d0a45a0cdb`

Pinned unchanged dependencies:

- StadiumBattleFX `main.lua`: `a27f954583b098a491d698a04610bb4caf3c1ba2c70c4515ea134cfb4178fb69`
- StadiumFxPlayer pre-wide-screen accepted lineage: `bc1fffa60f5d17e5c606eaf9042ec2856cdf953b15ef245435c9d2df1df695fe`
- DRAMATIC_SHAPE `OverworldBattle.lua`: `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DRAMATIC_SHAPE `BattleScene.lua`: `4c05b8788e3cd64ea64e6905c2ba623e1d69722a44387c8f193b2ad76992f3c0`
- DRAMATIC_SHAPE `Voxel3D.lua`: `399e45e4549ad844885acc1c98fbb3756e7975f1376bbb0318bd54bc6c29af75`
- THOR Battle UI `main.lua`: `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`

## Formal architecture

1. StadiumBattleFX is the external move-VFX provider. PMD Custom GBC move VFX remain removed.
2. Stadium `BattleHost.begin()` presentation lifecycle remains disabled for this integration. Stadium effect rendering is VFX-only; re-enabling BattleHost presentation ownership is prohibited without a new authority review.
3. `BattleState.applyHitFx` remains the sole HIT_FRAME owner.
4. PMD source-pose de-dup prevents authoritative HIT from replaying an attacker pose already visibly presented.
5. Contact recovery returns to HOME facing the opponent and must not preserve a stale turned-away contact frame.
6. PMD source-body animation uses the accepted frame-rate-independent visible-time clock rather than one-render-one-motion-tick.
7. Visible native PMD `head` and native `lunge` / LeapForth assets are forbidden. Semantic families may remain; visible fallback is `charge -> strike -> attack`.
8. Player visible PMD remains the accepted legacy 2D overlay. The player shadow silhouette only participates in the 3D shadow pass. Enemy visible PMD remains the depth-tested 3D card.
9. DRAMATIC_SHAPE lighting parity uses live shader-uniform refresh after battle-local shadow/fog neutralization and after restore.
10. Surf keeps the accepted numeric/table-free wide water implementation. Fury Swipes keeps parallel first-hit startup and duplicate final-repose suppression.

## Wide-screen screen-space rule

Full-screen Stadium colour washes and flashes are authored on the classic `160x144` layer, while the accepted wide battle composition is `304x144` and centres the classic layer at x=`72`.

Formal v0.2.13a expands only semantic full-screen `ScreenFx.fill/flash` geometry in wide battle:

- classic: `x=0, width=160`
- wide pre-transform: `x=-72, width=304`
- after the existing +72 centring transform: effective x=`0..303`

Anchored/local particles, beams, rings, projectile anchors, impacts and HUD geometry are not stretched.

This final geometry correction was promoted without an additional Thor replay at the user's explicit request after static coordinate-path confirmation. It is therefore an intentional, documented promotion exception, not missing evidence to be silently reinterpreted later.

## Closure evidence

v0.2.12a Integration Closure Regression I completed all three fixture sets before fixture removal:

- closure sets completed: `3/3`
- HIT_AUTH duplicate: `0`
- continuation barrier re-arm: `0`
- unsafe visible `head/lunge` action ownership: `0`
- no Stadium draw failure/fallback
- no current LOVE Lua traceback
- no application FATAL EXCEPTION
- no ANR

v0.2.11c timing evidence reduced Scratch first/second source-body START->HANDOFF from the prior `61 vs 14` asymmetry to `34 vs 30` battle frames while preserving source-hit and exact HANDOFF landmarks.

## Fixture seal

Formal v0.2.13a contains no Integration Closure TEST fixture:

- no B-key synthetic-battle interception
- no fixture RNG
- no test moveset mutation
- no fixture sequence state
- no `PMD_INTEGRATION_CLOSURE_FIXTURE` marker

Future development must branch from the exact production hashes above. Test hooks belong only in later candidates and must be removed again before any future formal promotion.

## Supersession

This authority supersedes the former PMD StadiumBattleFX integration formal baseline `v0.2.04a` for this integration lane. Earlier HIT_FRAME, Action Binding, depth/occlusion and THOR authorities remain inherited unless explicitly replaced above.

## Next mainline

Next development lane: **Move Catalog Semantic + AV Synchronization Audit II**.

The next lane should audit the broader move catalog against the formal two-layer rule:

- interaction semantics: contact / projectile / area / status
- visible body semantics: swing / dash / charge / strike / punch / kick / bite / spin / multi / shot / cast / etc.

It must preserve this Formal Authority and may not reintroduce Custom GBC move VFX, BattleHost presentation ownership, visible head assets, or native LeapForth/lunge body assets.
