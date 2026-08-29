# SoulGold S1E Ownership / PMD Port Authority

Date: 2026-08-29
Status: HUMAN PASS on AYN THOR / RetroArch mGBA for S1E prototype
Authority baseline: SoulGold v1.0.5, `77ec3fc6275bb94dd703f4c1976f1457cc44a60b`

## Human-verified S1E result

The user verified that S1E fixed both visible defects from S1D:

1. native/legacy battler body no longer flashes during send-out before the custom animated body appears;
2. player battler / healthbox periodic idle bob is fixed.

Native battle choreography remains present. The user specifically observed opponent Tail Whip still moving the whole battler sprite. Source inspection confirms the same native battler-transform path is available to player and opponent battlers.

## Root cause A: first-visible body ownership was too late

Replacing backing graphics RAM during move-selection is insufficient. SoulGold can write or expose native body pixels after the custom runtime has already primed its buffers.

The proven S1E ownership chain makes custom frame 0 the final body-pixel writer at every authoritative creation/load boundary:

1. after native `BattleLoadMonSpriteGfx(...)`;
2. after `SetMultiuseSpriteTemplateToPokemon(...)` on both battler template paths;
3. after the two authoritative `CreateSprite(&gMultiuseSpriteTemplate, ...) -> StartSpriteAnim(...)` chains;
4. immediately request OBJ frame copy for custom frame 0 after sprite creation.

Rule for PMD: port this ownership technique, not Showdown-specific symbols. PMD should re-prime its HOME/idle frame at the same native boundaries.

## Root cause B: idle spatial ownership happened after OAM snapshot

SoulGold battle frame order includes:

`AnimateSprites() -> BuildOamBuffer() -> ... -> RunTasks()`

The earlier prototype updated custom runtime state after `BuildOamBuffer()`. Native callbacks could therefore remain the final spatial writer for the rendered frame, producing periodic player battler / healthbox movement.

S1E inserts a custom pre-OAM ownership pass:

`AnimateSprites() -> CustomIdlePrepareOam() -> BuildOamBuffer()`

Only while the custom animated body owns move-selection idle:

- battler `x2/y2` idle residue is reset;
- healthbox base coordinates are restored with SoulGold canonical healthbox positioning;
- healthbox companion sprite offsets are normalized.

Do not apply this unconditionally.

## Native battler transform must remain authoritative during battle animation

The custom runtime changes body frame pixels. It must not replace SoulGold's battle choreography layer.

During native battle animation / move execution, custom idle presentation is suspended. In S1E this is enforced by the same ownership gate that rejects custom presentation while `gDoingBattleAnim` or related native special-animation flags are active.

SoulGold native animation code resolves battlers through `GetAnimBattlerSpriteId(...)` / `gBattlerSpriteIds[...]` and then modifies the existing sprite, including:

- `x2/y2` translation;
- shake;
- horizontal lunge;
- vertical dip;
- elliptical translation;
- scale;
- rotation / affine transforms;
- hit / move choreography.

These paths are battler-based, not enemy-only. Player and opponent animated bodies can therefore retain native battler transforms as long as custom code does not continuously overwrite them.

### Required ownership model

```text
Move-selection idle
  custom HOME/idle frame animation owns body pixels
  custom pre-OAM pass removes only proven idle spatial residue

Move / battle animation starts
  suspend custom idle frame presentation
  SoulGold native battler transform owns x/y/x2/y2/affine/choreography
  SoulGold battle FX remain authoritative

Move animation ends
  refresh current custom idle frame
  resume custom idle ownership
```

## Do not reintroduce these failed assumptions

1. Do not require `SpriteCallbackDummy` / `SpriteCallbackDummy_2` as the only safe ownership callbacks. Opponent/front paths can legitimately retain native callbacks while otherwise being safe for custom idle ownership.
2. Do not zero battler transform continuously during native move animation.
3. Do not replace SoulGold move choreography with sprite-source animation unless a future feature explicitly requires it.
4. Do not infer frame jitter from visual impression alone. Audit raw GIF alpha geometry first.
5. Do not rebuild against an arbitrary SoulGold revision. The original S1A/S1B/S1C crash investigation was polluted by building against v1.0.6.1 while the user's known-good release ROM was v1.0.5.

## Raw Showdown geometry evidence from S1E

Sprigatito back official Showdown GIF:

- 51 frames;
- source canvas 45x53;
- bottom opaque y = 52 for every frame;
- bottom-line span = 0 px;
- centroid-y span ~= 0.3792 px.

Therefore the large player-side S1D bob was not caused by whole-frame ground-line drift in the source GIF.

Marill front has a 1 px bottom-line span, so small natural internal motion can remain after host spatial ownership is stable.

## PMD port checklist

PMD project should apply the following in order:

1. keep PMD and Showdown runtimes independent;
2. use the exact SoulGold baseline used by the target ROM;
3. prime PMD HOME frame after native body load;
4. prime PMD HOME frame after battler template selection;
5. prime PMD HOME frame after authoritative battler `CreateSprite` and request OBJ copy immediately;
6. add a pre-`BuildOamBuffer` PMD idle spatial pass after `AnimateSprites`;
7. limit that pass to PMD idle ownership only;
8. suspend PMD pixel/spatial ownership while native move / hit / faint / special animation owns the battler;
9. preserve native battler transforms for both player and opponent;
10. audit raw PMD frame anchor/ground geometry independently before compensating coordinates.

## Promotion rule

The S1E ownership method is the current formal reference for first-visible custom battler body ownership and move-selection idle spatial stability. Any PMD implementation should demonstrate equivalent runtime behavior before promotion.
