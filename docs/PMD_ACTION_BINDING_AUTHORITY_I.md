# PMD Action Binding Authority I

Status: **RUNTIME PASS / FORMAL AUTHORITY**

Accepted build: `pmd_idle_battle_sprites v0.1.99b`

Inherited and extended by: **PMD + StadiumBattleFX Integration I v0.2.13a FORMAL AUTHORITY (2026-08-22)**

Current integration authority document:
`docs/PMD_SBFX_INTEGRATION_FORMAL_AUTHORITY_20260822.md`

Depends on:
- PMD HIT_FRAME Authority I (`v0.1.98b`)
- DRAMATIC_SHAPE 1.8.2 accepted Depth/Occlusion Authority
- thor_battle_ui 0.3.41 accepted compatibility hash

## Accepted hashes

Historical Action Binding I baseline:
- PMD main.lua: `b2f8f143f7298d5b0744c30bc885df5cca1eb109a073c515bbcc6eeedb4eed64`
- PMD manifest.json: `c9351afd39ce30ca25428dcd359b8687bd7f6f92d2f44bf5ca3b92fa74d45aa4`
- Candidate ZIP: `8c32d53f3dff270a309fca6b66c994240b4de92ff6ddfb428577e67f4c7a1233`
- Formal Evidence ZIP: `59f498b71f8d31e5ed2f694686f2cdfddaed6fe9032790bfc78cd7c549e124de`

Current inherited integration identity:
- PMD v0.2.13a main.lua: `7365476702ab294ad75b5c52e9e69dff9710c608ea57dc806e540e7b1650d406`
- PMD v0.2.13a manifest.json: `20eec657f82f85d486bcd25b714e03d0d4ac4873dd638cf363d75879ee718c4a`
- StadiumFxPlayer.lua: `7c8c52373f894b8b821f582b875748631897d8daf89366d0aa49ba7af668b279`
- DRAMATIC_SHAPE OverworldBattle.lua: `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- DRAMATIC_SHAPE BattleScene.lua: `4c05b8788e3cd64ea64e6905c2ba623e1d69722a44387c8f193b2ad76992f3c0`
- DRAMATIC_SHAPE Voxel3D.lua: `399e45e4549ad844885acc1c98fbb3756e7975f1376bbb0318bd54bc6c29af75`
- THOR Battle UI main.lua: `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`

## Authority rules

1. `BattleState.applyHitFx` remains the sole HIT_FRAME owner. Action Binding consumes that authority and does not redefine impact timing.
2. PMD presentation is correlated through `START → HANDOFF → NATIVE_RELEASE → ANIM_RELEASE → HIT → RECOVERY/COMPLETE`.
3. Contact actions require authoritative HIT and contact recovery on the HIT frame.
4. Projectile actions detach source-body commitment after handoff and must not inherit contact recovery. Ember is the reference projectile benchmark.
5. Multi-hit uses one sequence with row-level ownership. Continuation rows must not re-arm the native presentation barrier.
6. Sustained/long-SFX actions must not let the PMD source body return to ambient before native animation/audio release.
7. Non-damage status/self actions must not create damage HIT authority.
8. Area/full-screen presentation may consume the same HIT/Action Binding authority but does not gain a separate damage clock.
9. DRAMATIC_SHAPE, THOR, Depth/Occlusion, Presentation-vs-Physical-Feet separation, Large Pokémon Bounds, player BACK SPRITES policy, and species scale remain independent sealed authorities unless the v0.2.13a integration authority explicitly states otherwise.
10. v0.2.13a adds source-pose de-dup: if the exact source hit pose was already visibly presented, authoritative HIT must not replay the attacker pose.
11. v0.2.13a contact recovery ends HOME-facing and must not freeze a stale turned-away source frame.
12. v0.2.13a source-body presentation is frame-rate-independent and uses visible time rather than one-render-one-motion-tick.

## Global PMD visible-action hard constraints

Effective 2026-08-22 for all future PMD candidates:

- **Visible PMD `action=head` is forbidden for every species and every runtime context.**
- **Visible native PMD `action=lunge` / LeapForth asset playback is forbidden until a full-species body-integrity audit explicitly re-authorizes it.**
- Semantic family names `head` and `lunge` remain allowed for move classification and timing semantics.
- Full-body fallback order is `charge → strike → attack`.
- A central renderer/asset guard is required so future accidental unsafe requests cannot bypass the policy.

Canonical safety authority:
`docs/PMD_VISIBLE_BODY_ASSET_SAFETY_AUTHORITY_20260822.md`

## Historical formal closure

Action Binding I historical closure established:
- contact rows with missing HIT: 0
- recovery off HIT: 0
- HIT duplicates: 0
- continuation barrier re-arm: 0
- false status HIT: 0

v0.2.12a integration closure later reconfirmed:
- closure sets: `3/3`
- HIT_AUTH duplicate: `0`
- continuation barrier re-arm: `0`
- unsafe visible head/lunge ownership: `0`
- no current Stadium fallback, LOVE Lua traceback, FATAL EXCEPTION, or ANR

## Next mainline

Move Catalog Semantic + AV Synchronization Audit II must consume this authority rather than redefine it.
