# SoulGold PMD G3R5B runtime diagnosis

Runtime video `2026-08-28 20:40:41` proves two G3R5 presentation defects:

1. Cyndaquil Idle frame 1 still appears 1 px lower than Idle frame 0.
2. Player PMD shadow is horizontally too far right instead of centered beneath the battler.

Root cause A: G3R5 incorrectly used PMDCollab `*-Shadow.png` white-position changes to move the **body** via `presentationY`. PMD format semantics say Shadow.png describes where the **shadow** appears for each animation frame. It is not a body-ground anchor. This produced `Idle=[0,+1]` for Cyndaquil, directly commanding frame 1 downward.

G3R5B rule:
- keep G3R4B OAM timing;
- derive body-only vertical ground stabilization from a bounded visual support baseline on `*-Anim.png` after body-center normalization;
- PMD Shadow.png never writes body presentation offsets.

Root cause B: G3R5 translated the PMD Idle0 white shadow marker relative to the green body-center directly into the SoulGold shadow OBJ X offset. In the SoulGold battle presentation this placed Cyndaquil's ground shadow visibly to the right.

G3R5B shadow rule:
- preserve authentic PMDCollab shadow mask/ShadowSize;
- center the separate ground-shadow OBJ on the SoulGold battler base X;
- keep shadow on battler base Y + PMD-authored Idle0 vertical ground offset;
- never follow body `x2/y2` stabilization.

Acceptance:
- Cyndaquil Idle frame 0 -> frame 1 has no 1 px downward step.
- player shadow center is beneath the battler rather than right-shifted.
- Marill remains stable.
- native move/sendout/switch ownership and G3R4B OAM timing remain unchanged.
