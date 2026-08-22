# Move Catalog Semantic + AV Synchronization Audit II

Status: **ACTIVE NEXT MAINLINE / STATIC AUDIT STARTED**

Baseline: **PMD + StadiumBattleFX Integration I v0.2.13a FORMAL AUTHORITY**

Formal PMD main hash: `7365476702ab294ad75b5c52e9e69dff9710c608ea57dc806e540e7b1650d406`

## Goal

Expand from the accepted representative Integration I set to the broader move catalog without reopening sealed ownership.

The audit keeps two independent questions separate:

1. **Interaction semantic**: contact / projectile / area / status / sustained / multi
2. **Visible body semantic**: swing / dash / charge / strike / punch / kick / bite / spin / shot / cast / etc.

A move being physical, special, or contact does not by itself choose the visible body motion.

## Sealed inheritance

Do not change without new evidence:
- StadiumBattleFX VFX-only ownership; no `BattleHost.begin()` presentation lifecycle
- sole HIT_FRAME owner = `BattleState.applyHitFx`
- source-pose de-dup
- contact HOME-facing recovery
- frame-rate-independent PMD source-body clock
- visible `head` ban
- native `lunge` / LeapForth visible-body ban
- player legacy 2D visible overlay / shadow-only 3D silhouette
- enemy depth-tested 3D card
- DS lighting refresh parity
- Surf and Fury Swipes accepted fixes

## Static audit findings from formal v0.2.13a

### 1. Damage category is still mixed with presentation semantics

`moveActionForQueue()` enters a broad `isSpecial` branch after several explicit physical tables. Some move-name semantic tables are only consulted inside that branch. This can make a visually projectile/cast move fall through to generic `strike` when Gen1 type/category metadata classifies it as physical.

High-priority examples to verify:
- `GUST`: no explicit semantic mapping in the current formal router; can fall through to `strike` even though Stadium presents wind/projectile VFX.
- `NIGHT SHADE`: listed in `SPECIAL_CAST_DAMAGE_NAMES`, but Ghost is not one of the Gen1 special-type fallbacks; the name rule may be bypassed when category metadata is absent.
- `ACID`, `SLUDGE`, `SMOG`: listed in `PROJECTILE_SPECIAL_NAMES`, but Poison is not a Gen1 special-type fallback; the name rule may be bypassed when category metadata is absent.
- `SKY ATTACK`, `RAZOR WIND`: listed in `BEAM_CHARGE_MOVE_NAMES`, but both can miss that table if their metadata does not enter `isSpecial`.

Audit rule: **move-effect/interaction semantics must be name/effect-driven before damage-class fallback where appropriate.** Damage classification must not silently redefine whether a move is contact, projectile, area, cast, or sustained.

### 2. Species preference can outrank move semantics

The current special branch may choose `shock` for `PIKACHU`, `RAICHU`, or `JOLTEON` before several move-specific special mappings. Bubble/Bubblebeam already required an explicit exception for this reason.

Audit target: restrict species-preferred `shock` to genuinely Electric-compatible move semantics rather than allowing species identity alone to dominate unrelated special moves.

### 3. Multi-hit visible-body semantics need safety-aware review

Current multi body map includes:
- DoubleSlap -> strike
- Comet Punch -> punch
- Fury Attack -> strike
- Fury Swipes -> swing
- Double Kick -> strike
- Twineedle -> strike
- Pin Missile/Barrage/Spike Cannon -> shot

Do not automatically make names more literal. `head` and native `lunge` are formally unsafe, and any promotion of punch/kick/bite-specific assets must retain complete-body integrity.

### 4. A/V tail policy remains a catalog concern

Integration I fixed representative synchronization ownership, but the next audit must classify moves whose Stadium visual lifetime, native animation release, and audio tail differ materially.

The target rule is not "cut every sound at visual end." The correct audit records:
- source-body HANDOFF
- Stadium visual start/end
- native animation release
- HIT
- audio-tail release
- recovery complete

Then classify intentional tails versus visible desynchronization.

## Phase plan

### Audit II-A — static semantic routing matrix

Produce a move-name matrix that records:
- current family
- current visible body action
- expected interaction semantic
- whether routing depends on Gen1 damage category
- whether species override can change it
- unsafe-body risk

No runtime change in this subphase.

### Audit II-B — priority semantic corrections

Correct only high-confidence structural mismatches found by II-A. Prefer generic policy changes over move-specific exceptions.

### Audit II-C — AV-tail runtime matrix

Run a compact representative matrix covering projectile, beam, screen/area, sustained, multi, status and contact families. Record visual/audio release ownership without inventing a second hit clock.

### Audit II-D — closure

Remove TEST-only hooks and promote only after user visual acceptance and exact hash pinning.

## Immediate next target

Start with II-A and specifically verify `GUST`, `NIGHT SHADE`, `ACID`, `SLUDGE`, `SMOG`, `SURF`, `SKY ATTACK`, `RAZOR WIND`, `DOUBLE KICK`, and the Electric-species `shock` preference path.
