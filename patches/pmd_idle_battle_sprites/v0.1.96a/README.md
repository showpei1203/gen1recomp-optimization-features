# PMD v0.1.96a — Battle Presentation Timeline I

Status: **RUNTIME PASS / VISUAL ACCEPTANCE PENDING**

## Source authority

- PMD baseline: `pmd_idle_battle_sprites v0.1.95c`
- Baseline `main.lua` SHA-256: `11a1b8c3f8cdc098a8f7792b4b5fcb9557f62400999685dcc9337eb893a6f883`
- Candidate `main.lua` SHA-256: `698159d9fdab16633f29f8155740e5d4fdf3626648513bb0b834888cd3ed6031`
- Candidate ZIP SHA-256: `1a03ac8fbc728b136bde2c92a4c9d84b5a0c94f4abf3f9ce95b9a5e38eb3b00c`
- Google Drive candidate file ID: `1ForM1FjQk1POero3mJfdQzgGhompT6U7`
- Google Drive test folder ID: `15F3qVcvce9pn9g3PrYFPyf-VmFlbVEJH`

## Problem

v0.1.95c already synchronizes PMD body motion to the native animation handoff and briefly snaps the body pose when `playAnimSound` fires. That `sfxSnap` only represents **sound onset**, not the real lifetime of the LÖVE audio Source. Therefore native VFX can reach `AnimPlayer:isDone()` while move audio continues, and the PMD body can settle independently.

## Candidate behavior

v0.1.96a adds a narrow audio-tail presentation owner:

1. Immediately before the first native animation row sound, record `love.audio.getActiveSourceCount()` as the baseline.
2. Leave stock `Sound.playMove` completely untouched.
3. If `AnimPlayer` reaches visual DONE while active audio is still above baseline, temporarily keep the final non-empty animation sprite step alive.
4. Hold the PMD attacker on the family-appropriate hit/return pose during the same tail.
5. Release together into native hit feedback / PMD hurt / HP drain / recovery when active audio returns to baseline.
6. Hard cap at 180 visible frames to prevent a stray audio Source from deadlocking battle presentation.

## Runtime evidence — 2026-08-19

Evidence package: `GEN1RECOMP_PRESENTATION_TIMELINE_I_EVIDENCE_20260819_192121.zip`

- Evidence ZIP SHA-256: `a860df083c891cdfdaaf83d4dc03f8c78fc1dd8cd49c7e8aaa10bee1dad7100a`
- Evidence Drive file ID: `1bvsQir0nzFIAIoJqAFZQRSvZ1s3bjk1N`
- Installed candidate SHA matched `698159d9fdab16633f29f8155740e5d4fdf3626648513bb0b834888cd3ed6031`.
- Five audio-tail ownership windows were observed:
  - `THUNDER WAVE`: 68 frames, then 58 frames in a later battle.
  - `TAIL WHIP`: 7 frames, then 5 frames.
  - `QUICK ATTACK`: 14 frames.
- Every observed tail ended with `reason=audio_done`.
- 0 safety-cap timeouts.
- 0 new Lua errors in the session.
- FULL_LOGCAT showed no Android `FATAL EXCEPTION` or ANR.

This is strong runtime evidence that the candidate is detecting the real interval where native animation has ended but move audio is still active. It does **not** replace visual acceptance of the held final VFX frame and PMD body pose, so the candidate is not sealed yet.

Unrelated warnings were observed from `overworld_wild_spawns` world-billboard `pose() returned nil sprite` fallback and are tracked outside this candidate.

## Non-goals

This candidate does **not** modify damage, accuracy, hit timing, move data, pitch/tempo, sound playback, Gen2 palettes, or full-game runtime. It is an isolated presentation-layer experiment built byte-exact from the Thor v0.1.95c source snapshot.

## Acceptance

Priority moves: Quick Attack, Thunderbolt, Hydro Pump, Hyper Beam, Mega Punch/Kick, Blizzard, plus at least one multi-hit such as Fury Swipes.

PASS requires no battle hang, no multi-hit regression, no early PMD return-to-idle, and no obvious interval where native move visuals are gone while the detected move-audio tail continues.

Runtime trace markers:

- `PRESENTATION_TIMELINE audio-tail BEGIN`
- `PRESENTATION_TIMELINE audio-tail END`

## Next step

Presentation Timeline II will correlate, per move, PMD `nativeHandoff/nativeHitFrame`, native animation step progression, `playAnimSound` onset, `applyHitFx` impact, audio-tail begin/end, and recovery. The aim is to replace scattered hand-tuned `sfxSnap` behavior with an explicit HIT_FRAME authority before Gen2-colored animation work begins.
