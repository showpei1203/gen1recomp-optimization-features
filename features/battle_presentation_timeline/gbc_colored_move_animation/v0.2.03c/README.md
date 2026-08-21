# GBC Catalog Expansion A3.2 — v0.2.03c TEST

Status: **TEST-ONLY / STATIC PASS / THOR RUNTIME + VISUAL PENDING**

Formal Authority remains exact `v0.2.02a GBC Colored Move Animation Layer I`.

## Why this candidate exists

Thor evidence from failed `v0.2.03b` showed the A3 fixes were mostly healthy, but Scratch never entered the intended contact hold:

- Tackle safe body bind = 2; bad `action=lunge` bind = 0.
- Bubble/Bubblebeam projectile semantic errors = 0.
- Bubblebeam 9-bubble train and target-side WATER proof present.
- Action Binding/HIT Authority duplicate, continuation re-arm, and release-delta hard gates all 0.
- `SCRATCH_CONTACT_HOLD=0` remained the real unresolved presentation gate.
- `HASH_GATE=FAIL` was tooling-only: the collector carried a stale expected main SHA while installed hashes matched the v0.2.03b package exactly.

Scratch trace: native HANDOFF at battleFrame 943, authoritative HIT at 976, a 33-frame gap. The v0.2.03b hold waited for local source-strip exhaustion, so the condition never executed.

## v0.2.03c focused fix

Scratch now holds the same authoritative source hit frame immediately from native HANDOFF until engine-owned `applyHitFx`. At true HIT the same pose is re-delivered, so the attacker should read as one continuous action instead of a second beat.

No synthetic HIT/timer is introduced. Damage/status, audio, native barrier, queue, HIT_FRAME ownership, Depth/Occlusion, DRAMATIC_SHAPE, THOR Battle UI, Large Pokémon bounds, Tackle routing, Bubble/Bubblebeam projectile routing, and Bubblebeam late WATER retention remain unchanged.

## Candidate hashes

- main: `da480a595fba950ad54a0cec0c96b5d2958382962e3c1c93ba3556ee682b7b29`
- manifest: `7515cce9787d9dd9e9854d494c1200298a22fcb9f0397e5ec5cb29d51dc86e77`
- data: `9ba4a8f12665cad62940202927892a306c1b86f90675da582bfaae4db2a8a206`
- TEST ZIP: `2ff080a1eb7876dd45b224a431d720a1f869ebb04ce8a6d4871720cb7c26f883`

Static validation: **43 PASS / 0 FAIL**. LuaTeX embedded Lua 5.3 parser: main + data PASS.

## Persistent binary/evidence authority

Google Drive test folder: `11sq5yq3IWuGwbwtNUZlL8PtwyxaUnNa6`

Candidate ZIP: `18n73mlbULLV-J0IMxwcK-6bbp084nysO`

v0.2.03b evidence ZIP: `1L0k_ZjjWyCapTQHEQUzGTh3cqpJNMbhr`

## Promotion gate

Do not promote until Thor confirms Scratch is visually one continuous attacker action and the collector proves `SCRATCH_CONTACT_HOLD>0` with all existing hard gates healthy. TEST-only B fixture must be removed before any formal promotion.
