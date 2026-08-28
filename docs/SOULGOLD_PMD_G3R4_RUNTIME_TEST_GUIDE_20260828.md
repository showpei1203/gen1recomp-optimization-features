# Pokémon SoulGold PMD Animated Prototype — G3R4 Runtime Test Guide

Date: 2026-08-28

## Authority

- Project: Pokémon SoulGold PMD Animated Prototype
- Branch: `feature/pmd-portable-battle-framework`
- SoulGold baseline: `b5122bdf188943862c13abe4938e88b7bb3c5c4a`
- SpriteCollab baseline: `4b6b72aacde89abecf8d8e2f6b9e4c8a778570d7`
- G3R4 framework build commit: `9c6cb3fe57be815ba51283d6b74c80c80f360f23`
- CI run: `33165095018`
- CI result: **PASS**
- Runtime visual result: **PENDING USER ACCEPTANCE**

## Why G3R4 exists

G3R4 is a regression-recovery gate after G3R3 runtime testing. It does not add Attack/Hurt yet.

It isolates and repairs three presentation/ownership problems:

1. PMD data staged in RAM did not guarantee that the first visible OBJ frame was PMD. G3R4 explicitly queues the PMD HOME image to OBJ VRAM after authoritative battler `CreateSprite` paths and before normal visible presentation can win ownership.
2. Opponent PMD ownership was incorrectly constrained by a `SpriteCallbackDummy` whitelist. The whitelist is removed.
3. Body geometry returns to PMD green body-center alignment, with clip-safe per-species anchor targets. The PMD shadow is deliberately excluded from the body OBJ and will become a separate ground layer only after body recovery is accepted.

The installer identifies exactly two semantic battler creation chains:

`SetMultiuseSpriteTemplateToPokemon -> CreateSprite(gMultiuseSpriteTemplate) -> StartSpriteAnim -> PrimeCreatedSpriteBody`

It deliberately does **not** patch the other `StartSpriteAnim` occurrences used by reload/switch-in flows.

## Generated ROM

- File: `SoulGold-PMD-G3R4.gba`
- Size: `33,554,432` bytes
- SHA-256: `f4590be32eb665ce64e542a5936a69dfe0a3aeed0800d331e9927272c7323bb1`
- CRC32: `23958B60`

## G3R4 PMD targets

### Player

- Species: Cyndaquil
- Direction: UpRight
- Ambient actions: HOME, Idle, Walk, Nod, Rotate
- Clip-safe body anchor: `(32, 44)`

### Opponent

- Species: Marill
- Direction: DownLeft
- Ambient actions: HOME, Idle, Walk, Nod, Rotate
- Clip-safe body anchor: `(32, 41)`

Banned from this test: Pose, LookUp, DeepBreath, Sit.

## Runtime acceptance checklist

Test on the real target path whenever possible: AYN THOR -> RetroArch -> mGBA core. A desktop mGBA pass is useful but does not replace the target-device check.

### A. First-visible ownership

**PASS:**
- Cyndaquil is already PMD on the first visible battler frame.
- No one-frame native/original Cyndaquil flash during send-out.

**FAIL:**
- Any original Cyndaquil body appears before the PMD HOME frame.
- PMD appears only after an obvious late swap.

### B. Opponent ownership and species isolation

**PASS:**
- Marill appears complete and stable in DownLeft.
- No Cyndaquil tiles, palette contamination, slivers, chopped body, or cross-species corruption.

**FAIL:**
- Red/blue fragment, missing body region, wrong species tiles, or intermittent corruption.

### C. Body geometry

Watch multiple loops of HOME -> action -> HOME for Idle, Walk, Nod, Rotate.

**PASS:**
- Feet/body relationship to battlefield stays visually coherent.
- Character does not jump vertically simply because the PMD frame's body center changes.
- No clipping at top/bottom/left/right of the 64x64 SoulGold body canvas.

**FAIL:**
- Whole character bobs, teleports, or walks upward/downward as an artifact of frame alignment.
- Any body frame is clipped.

### D. Shadow policy

G3R4 intentionally has **no PMD shadow baked into the body OBJ**.

Do not fail G3R4 merely because an authentic separate PMD shadow is not yet present. The separate ground-anchored shadow layer is deferred until body ownership/geometry is accepted.

**FAIL only if:**
- A black/colored PMD shadow is visibly embedded in the animated body canvas and moves with the body.

### E. Native battle choreography

**PASS:**
- Poké Ball/send-out timing remains native SoulGold behavior.
- Healthbox and normal battle state progression remain intact.
- No freeze, softlock, crash, or input loss.

### F. Native move interruption and PMD resume

Use a simple move such as Tackle.

**PASS:**
- Native battle move/effect can temporarily own the battler as before.
- PMD ambient does not fight the native animation while it is active.
- After native ownership ends, battler returns through PMD HOME and ambient resumes.

**FAIL:**
- PMD ambient overwrites native move choreography.
- Sprite disappears/corrupts after a move.
- Ambient never resumes after native ownership returns.

## What to report

For the fastest diagnosis, report these six items only:

1. First visible Cyndaquil: PMD immediately / native flash first
2. Marill: complete / corrupted
3. Body bobbing: none / slight / obvious
4. Clipping: none / action + frame if seen
5. Tackle interruption/resume: normal / abnormal
6. Crash/freeze: none / where it occurs

A short video covering send-out, ~15 seconds of ambient, and one Tackle is stronger evidence than many screenshots because first-frame ownership and vertical drift are temporal bugs.

## Promotion rule

G3R4 can be promoted to the next baseline only when:

- CI/build gate = PASS
- first-visible ownership = PASS
- opponent species isolation = PASS
- body geometry/clipping = PASS
- native interruption/resume = PASS

Only then proceed to the separate authentic PMD shadow layer. Attack/Hurt integration remains after the body/shadow ownership path is stable.

## Current gate

**G3R4 STRUCTURAL / BUILD: PASS**  
**G3R4 HUMAN RUNTIME VISUAL: PENDING**
