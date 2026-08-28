# SoulGold PMD G3R5B runtime diagnosis

Runtime video `2026-08-28 20:40:41` proves two G3R5 presentation defects:

1. Cyndaquil Idle frame 1 appears 1 px lower than Idle frame 0.
2. Player PMD shadow is horizontally too far right instead of centered beneath the battler.

## Root cause A: G3R5 moved the body from Shadow.png metadata

G3R5 used PMDCollab `*-Shadow.png` white-position changes to write body `presentationY`. That is the wrong ownership boundary: Shadow.png describes shadow placement, not body motion. The generated Cyndaquil Idle timeline was exactly `presentationY=[0,+1]`, so frame 1 was explicitly commanded one pixel downward.

A first G3R5B experiment tried deriving a generic foot/support baseline from `*-Anim.png`. CI rejected it because Cyndaquil still calculated as `[0,+1]`. That heuristic therefore is not promoted as authority.

Final G3R5B body rule:
- preserve the G3R4B OAM timing fix;
- restore G3R4B zero body presentation offsets for every ambient frame;
- apply exactly one runtime-acceptance override proven by the user's video: `Cyndaquil / UpRight / Idle / frame 1 = presentationY -1`;
- every other current Cyndaquil and Marill ambient body offset remains zero;
- PMD Shadow.png is forbidden from moving the body.

This is intentionally a narrow prototype/runtime acceptance correction, not a claimed universal PMD grounding formula. A general rule can be promoted only after more species are validated.

## Root cause B: player shadow inherited PMD-authored horizontal displacement

G3R5 translated the PMD Idle0 white shadow marker relative to the body center into the SoulGold shadow OBJ X offset. For Cyndaquil that generated `GroundShadowXOffset=+5`, matching the runtime-visible right shift.

Final G3R5B shadow rule:
- preserve the authentic PMDCollab shadow mask and `AnimData.xml ShadowSize`;
- center the separate ground-shadow OBJ on SoulGold battler base X, therefore battle `GroundShadowXOffset=0`;
- keep the PMD-authored Idle0 vertical ground offset for now;
- shadow follows battler base coordinates and never follows body `x2/y2` stabilization;
- native opponent shadow suppression/restoration remains ownership-safe.

## Acceptance gate

- Cyndaquil Idle frame 0 -> frame 1 has no 1 px downward step.
- Player shadow is centered beneath Cyndaquil instead of right-shifted.
- Shadow remains grounded while body ambient animation runs.
- Marill remains stable.
- Native move/sendout/switch ownership and G3R4B OAM timing remain unchanged.
- Runtime visual status remains PENDING until human/device validation.
