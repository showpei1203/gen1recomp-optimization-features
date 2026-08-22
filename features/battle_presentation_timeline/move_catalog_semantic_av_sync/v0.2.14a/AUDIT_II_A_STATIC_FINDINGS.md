# v0.2.14a — Move Catalog Semantic + AV Sync Audit II-A

Status: **STATIC AUDIT / NO RUNTIME CHANGE YET**

Baseline: PMD + StadiumBattleFX Integration I `v0.2.13a FORMAL AUTHORITY`

Formal PMD hash: `7365476702ab294ad75b5c52e9e69dff9710c608ea57dc806e540e7b1650d406`

## Router structure found in the formal source

The formal router currently resolves several explicit physical/body tables before a broad `isSpecial` branch. Some move-name semantic tables are only consulted *inside* `isSpecial`.

This creates a structural risk: Gen1 damage category/type may decide presentation semantics for moves whose visual interaction should instead be name/effect driven.

## Priority findings

### P0 — non-contact effect can fall through to generic strike

- `GUST` has no explicit move-name routing in the formal body router. If metadata does not mark it special/projectile, it falls through to `sourceAwareAction(strike), family=strike`.
- This is already known to be visually a wind effect under StadiumBattleFX, so `strike/contact` is semantically suspicious even though Integration I's source-pose de-dup prevents the old top-sprite replay.

Recommended direction: classify interaction/body semantics separately; likely non-contact effect family with stationary or release body action. Do not reintroduce a new hit clock.

### P0 — move-name projectile/cast tables are gated by `isSpecial`

At-risk names:
- `NIGHT SHADE` in `SPECIAL_CAST_DAMAGE_NAMES`
- `ACID`, `SLUDGE`, `SMOG` in `PROJECTILE_SPECIAL_NAMES`
- `SKY ATTACK`, `RAZOR WIND` in `BEAM_CHARGE_MOVE_NAMES`

If Gen1 metadata does not enter `isSpecial`, these name tables are never consulted and the move can fall to generic physical `strike`.

Recommended direction: move interaction/effect semantic selection ahead of Gen1 damage-category fallback for high-confidence move names.

### P1 — Electric species preference is too broad

`shouldUseShockMotion()` currently returns true immediately for Pikachu/Raichu/Jolteon, before several special move-name branches. Bubble/Bubblebeam already needed an explicit exception.

Risk: unrelated special moves used by these species can inherit `shock` body language because of species identity rather than move semantics.

Recommended direction: species preference may choose among compatible Electric body actions, but must not override a non-Electric move's interaction semantic.

### P1 — multi-hit literal semantics vs body safety

Current map:
- DoubleSlap -> strike
- Comet Punch -> punch
- Fury Attack -> strike
- Fury Swipes -> swing
- Double Kick -> strike
- Twineedle -> strike
- Pin Missile -> shot
- Barrage -> shot
- Spike Cannon -> shot

Do not automatically change `Double Kick` to `kick` or Fury Attack to a head/lunge body simply because the names suggest it. Visible body integrity is sealed above literal naming.

### P2 — A/V tail audit remains separate

The next runtime matrix should compare:
- source-body HANDOFF
- Stadium visual start/end
- native animation release
- HIT
- audio-tail release
- PMD recovery complete

A long sound tail is not automatically wrong. The audit must distinguish intentional release tails from visible desynchronization.

## v0.2.14a implementation gate

Do not change runtime until the following policy is encoded:

1. interaction semantic is resolved independently from damage category;
2. visible body semantic is resolved independently from interaction semantic;
3. move-name effect semantics may override category fallback where the visual behavior is unambiguous;
4. species preference cannot turn unrelated move effects into Electric body semantics;
5. unsafe visible head/native-lunge assets remain structurally impossible.

## Candidate focus after audit approval

First targeted candidate should cover only high-confidence structural corrections:
- Gust
- Night Shade
- Acid
- Sludge
- Smog
- Electric-species shock routing guard

Sky Attack / Razor Wind should remain audit-only until their intended charge/release body language is pinned, because their semantics are less trivial than a simple projectile rename.
