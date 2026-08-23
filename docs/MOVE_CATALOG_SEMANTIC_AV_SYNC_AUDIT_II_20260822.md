# Move Catalog Semantic + AV Synchronization Audit II

Status: **CLOSED / PROMOTED INTO v0.2.17e FORMAL AUTHORITY**

Original baseline: **PMD + StadiumBattleFX Integration I v0.2.13a FORMAL AUTHORITY**

Promoted authority: **PMD + StadiumBattleFX Move Presentation Authority v0.2.17e (2026-08-23)**

Canonical authority document:
`docs/PMD_SBFX_MOVE_PRESENTATION_FORMAL_AUTHORITY_20260823.md`

Formal PMD main hash: `726cf94166333ea49512e05925fad3f6925ff796c669bd729d29801125103490`

## Goal

Expand from the accepted representative Integration I set to the broader move catalog without reopening sealed ownership.

The audit kept two independent questions separate:

1. **Interaction semantic**: contact / projectile / area / status / sustained / multi
2. **Visible body semantic**: swing / dash / charge / strike / punch / kick / bite / spin / shot / cast / etc.

A move being physical, special, or contact does not by itself choose the visible body motion.

## Sealed inheritance retained

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

## Closed findings / corrections

### Damage category vs presentation semantics

Resolved structurally: high-confidence move/effect semantics now resolve before broad Gen1 damage-category fallback where required.

Accepted examples include:
- Gust / Acid / Sludge / Smog -> projectile semantics
- Night Shade -> special-cast semantics
- Sky Attack / Razor Wind -> charge semantics
- Swift / Rock Throw / Bonemerang / Egg Bomb and other physical-by-type ranged moves -> projectile semantics
- Earthquake / Fissure -> area-release semantics

### Species override

Electric-species shock preference was tightened so species identity cannot silently force unrelated special moves into shock presentation.

### Multi-hit / visible body safety

Multi-hit mappings were retained under full-body asset safety. Unsafe visible `head` and native `lunge` assets remain prohibited.

### AV timing

The audit replaced the original broad post-impact-tail concept with phase-aware ownership:
- exact move Source ownership for non-beam adaptive AV timing;
- Beam primary and impact as separate timing domains;
- Beam SE stretches the emitted beam/travel phase, never the target impact phase;
- later sound rows do not steal Beam primary timing ownership;
- residual static final-frame hold remains bounded.

### Status / auxiliary ownership

Accepted follow-up corrections:
- Freeze feedback target ownership;
- status-self vs status-target split;
- String Shot / Leech Seed target-projectile semantics;
- Powder/Spore target-field semantics;
- Leech Seed residual drain-only phase;
- stale auxiliary animation context cannot override queue-side ownership;
- Protect / Reflect self-guard presentation.

### Two-turn movement / grapple extension

The later Audit III follow-up closed two high-risk movement families:
- Fly / Dig now use single-source PMD-body-owned two-turn choreography;
- first-turn auxiliary native visuals are suppressed only as presentation rows;
- second-turn native move rows become hit-only with exact hit tables preserved;
- `applyHitFx` remains target hit/damage authority;
- PMD returns HOME and ambient animation is explicitly resumed;
- Seismic Toss / Submission use grapple-specific presentation families.

## Closure evidence

v0.2.17d:
- Fly/Dig charge native suppression = PASS
- Fly/Dig release hit-only = PASS
- Fly/Dig ambient resume = PASS
- forbidden HOME-anchored two-turn source VFX = `0`
- no duplicate HIT / continuation re-arm / unsafe head/lunge / Lua / FATAL / ANR regressions

v0.2.17e:
- embedded B-key TEST fixture removed
- exact candidate hashes matched device
- `ERROR_ROWS=0`
- `TEST_FIXTURE_RUNTIME_ROWS=0`
- representative normal battle PMD + Stadium lifecycle completed
- battle ended normally
- user accepted smoke with `ok 繼續推進`

## Next lane

Future move-presentation work must branch from **v0.2.17e Formal Authority** and should use a stricter pre-delivery rule:

- verify event order;
- verify spatial source ownership;
- verify there is exactly one visible source/travel authority;
- verify target HIT ownership;
- verify HOME/ambient state restoration;
- do not treat phase-marker presence alone as visual correctness.
