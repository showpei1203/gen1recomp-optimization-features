# SoulGold Showdown S1E v1.0.5 Runtime Candidate

Date: 2026-08-29

## Authority

- SoulGold baseline: `77ec3fc6275bb94dd703f4c1976f1457cc44a60b` (`v1.0.5`)
- Framework candidate head: `c11f5acbe2d7c719b976dd3853365d7a04e0adbe`
- GitHub Actions run: `33229313545`
- CI/build result: **PASS**
- Human runtime result: **PENDING**

## ROM

- Size: `33,554,432` bytes
- SHA-256: `b65e2ad9e0c143be2c29c04efaa76887d83b76f65e140dee4feb79451405138a`
- CRC32: `E5A455A7`

## S1D video findings

The user runtime video showed two separate defects:

1. Native/legacy battler bodies were visible during send-out before Showdown idle ownership began.
2. The player battler and player healthbox moved vertically during move-selection idle while the bottom command UI remained fixed.

## S1E fixes

### First-visible body ownership

S1E ports only the generic ownership technique proven in the independent PMD lane. There is no PMD runtime dependency.

Showdown frame 0 becomes the final body-pixel writer at these points:

1. after `BattleLoadMonSpriteGfx(...)` native loading,
2. after `SetMultiuseSpriteTemplateToPokemon(...)` on exactly two battler template paths,
3. after the two authoritative `CreateSprite(gMultiuseSpriteTemplate) -> StartSpriteAnim(...)` creation chains, followed by an explicit OBJ frame copy.

### Spatial ownership

SoulGold update order is `AnimateSprites -> BuildOamBuffer -> ... -> RunTasks`.

S1D's Showdown tick occurred after `BuildOamBuffer`, so it could not be the final spatial writer for that rendered frame. S1E inserts `ShowdownSoulGoldPrototype_PrepareOam()` after `AnimateSprites()` and before `BuildOamBuffer()`.

Only while Showdown owns move-selection idle:

- battler `x2/y2` are reset,
- healthbox base coordinates are restored through `InitBattlerHealthboxCoords`,
- healthbox and its companion sprites have `x2/y2` reset.

Native send-out choreography and native move/hit/faint spatial ownership remain unchanged.

## Raw official Showdown GIF audit

### Sprigatito back

- source canvas: `45x53`
- frames: `51`
- bottom y: `52` on every frame
- bottom span: `0 px`
- centroid-y span: `0.3792 px`

This rules out whole-frame ground-line drift in the original Sprigatito back GIF as the main cause of the large S1D player bob.

### Marill front

- source canvas: `51x48`
- frames: `54`
- bottom y: `46..47`
- bottom span: `1 px`
- centroid-y span: `2.1739 px`

Some internal Marill source-animation motion may remain even after host spatial ownership is stable.

## Human acceptance test

1. New Game -> leave house -> normal starter flow.
2. Choose left Sprigatito.
3. First battle should be Lv5 Marill.
4. Neither battler should show a native/old body before the Showdown body during send-out.
5. During move-selection idle, Sprigatito healthbox should no longer periodically shift vertically.
6. Observe body bob separately from UI/healthbox movement.
7. Use one move and confirm native move animation runs, then Showdown idle resumes.

Promotion remains blocked until human runtime evidence passes these checks.
