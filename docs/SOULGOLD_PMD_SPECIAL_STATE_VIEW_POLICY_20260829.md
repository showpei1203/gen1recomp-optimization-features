# SoulGold PMD Special-State Source-View Authority

Date: 2026-08-29
Scope: Pokémon SoulGold PMD Animated Prototype

## Authority

Normal battle-facing body actions may use the established SoulGold presentation directions (player UpRight, opponent DownLeft) when the pinned PMDCollab action actually provides directional rows.

Special-state actions are exempt from that 45-degree presentation constraint. Sleep and future state-specific actions may preserve the exact PMDCollab-authored source view, including directionless single-row animation sheets.

The implementation must inspect the pinned PMDCollab source rather than infer a direction:

- `*-Anim.png`
- `*-Offsets.png`
- `*-Shadow.png`
- `AnimData.xml`

If all three action sheets are directionless, the runtime/converter must not invent an UpRight/DownLeft row, rotate the body, mirror the body, or reinterpret the shadow to force battle-facing perspective.

If an action genuinely provides the normal 8-row directional layout, the established requested battle direction may be used.

Mixed or inconsistent geometry among Anim / Offsets / Shadow is a hard source-audit failure.

## Preservation Rules

1. Preserve 100% of opaque source pixels. No scale, resample, crop, or heuristic re-angle is allowed.
2. Body anchoring still uses PMDCollab authored body-center metadata and the accepted SoulGold battle anchor.
3. Authentic action-specific PMDCollab shadow remains frame-synchronous with the body and uses the same resolved source layout.
4. Source view does not change SoulGold combat ownership. Status logic, damage, turn progression, move FX, controller timing, trainer choreography, and battle rules remain native SoulGold authority.
5. Persistent state presentation is lower priority than explicit reactive/native-owned presentation such as Hurt and move Attack/Shoot/Return.
6. Leaving a persistent special state must pass through clean HOME before ambient presentation restarts.
7. Visual PASS still requires runtime evidence on the target acceptance path. CI/build success is structural only.

## First Proven Source Case

G3R8 source audit proved Cyndaquil and Marill `Sleep` are directionless single-row special-state actions in the pinned SpriteCollab revision. Both use the source-authored view rather than a fabricated 45-degree row.

This policy is the baseline for future special-state action integration and supersedes any blanket assumption that every PMD action is an 8-direction sheet.
