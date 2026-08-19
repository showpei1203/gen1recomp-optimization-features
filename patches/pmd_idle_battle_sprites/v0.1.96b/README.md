# PMD v0.1.96b — Battle Presentation Timeline II Trace

Status: **STATIC PASS / WAITING THOR RUNTIME TRACE**

## Scope

Diagnostic-only successor to `v0.1.96a`. It intentionally preserves the v0.1.96a audio-tail presentation behavior and adds correlated per-move trace markers. It does not tune animation timing, SFX lifetime, damage, accuracy, hit resolution, or Gen2 visual assets.

## Source authority

- Source: `pmd_idle_battle_sprites v0.1.96a`
- Source `main.lua` SHA-256: `698159d9fdab16633f29f8155740e5d4fdf3626648513bb0b834888cd3ed6031`
- Source `manifest.json` SHA-256: `1164c12db4bf36bdae9d2a6c9e4788b2538977d8f295a35ab616e7c597c96634`
- Formal rollback source: `v0.1.95c`
- Formal `main.lua` SHA-256: `11a1b8c3f8cdc098a8f7792b4b5fcb9557f62400999685dcc9337eb893a6f883`

## Candidate identity

- Candidate `main.lua` SHA-256: `126f645f9c18b1c258265045045d017e5bddd8c07198c68be2d6eccc1184b52f`
- Candidate `manifest.json` SHA-256: `05719ed704a9052ab51a305f0d2e4c54576a3548aa89a5ca5cb9a92706da33bf`
- Candidate ZIP SHA-256: `ec1df1b771f2ae89e8df8ecf22e9bc3698d38bf3f71728cede6802fb2e13085c`

## Google Drive authority

- Test folder ID: `1mQntf-9hrMakLTHDHPweDbu9T44McWzi`
- Candidate ZIP ID: `1VkznGO7vShXiBaYOXlZt5yOjErb-m8-4`
- Candidate `main.lua` ID: `1JHlQu5pmoEMVMYpbi5Djnd2tYyF-tSnA`
- Candidate `manifest.json` ID: `1iS8GJ06nUko4iWz0IMo-cMbi_9c9JP_2`
- Diff ID: `1ztJxRgWEZ5Js4mX46VJwEADFvws4HRmI`
- Static validation ID: `1QQRaDw2eq2sZX0L_-vtWoag9ED8cpfSa`

## Timeline II trace

Each real move presentation receives one monotonically increasing trace id. The same id correlates:

`START -> HANDOFF -> NATIVE_RELEASE -> ANIM_ACTIVE -> SFX -> ANIM_DONE -> ANIM_RELEASE -> HIT`

The final `HIT` line records frame deltas from move start, PMD/native handoff, and the most recent native move-SFX trigger. This makes the next HIT_FRAME design evidence-driven rather than dependent on hand-tuned `sfxSnap` guesses.

Trace markers:

- `PRESENTATION_TIMELINE2 START`
- `PRESENTATION_TIMELINE2 HANDOFF`
- `PRESENTATION_TIMELINE2 NATIVE_RELEASE`
- `PRESENTATION_TIMELINE2 ANIM_ACTIVE`
- `PRESENTATION_TIMELINE2 SFX`
- `PRESENTATION_TIMELINE2 ANIM_DONE`
- `PRESENTATION_TIMELINE2 ANIM_RELEASE`
- `PRESENTATION_TIMELINE2 HIT`

## Rollback

The test package contains byte-exact rollback sources for both:

- `v0.1.96a`, the previous Runtime-pass / visual-pending candidate.
- `v0.1.95c`, the formal PMD source authority.

Runtime evidence is required before this trace candidate can be used to choose new HIT_FRAME policies.
