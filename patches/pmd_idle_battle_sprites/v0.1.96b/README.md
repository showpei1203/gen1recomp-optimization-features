# PMD v0.1.96b — Battle Presentation Timeline II Trace

Status: **RUNTIME TRACE PASS WITH TRACE-LIFECYCLE DEFECTS**

## Scope

Diagnostic-only successor to `v0.1.96a`. It preserves the v0.1.96a audio-tail presentation behavior and adds correlated per-move trace markers. It does not tune animation timing, SFX lifetime, damage, accuracy, hit resolution, or Gen2 visual assets.

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

## Thor runtime evidence

Evidence captured on 2026-08-19 confirms that every observed damaging move resolves native `HIT` on the exact `ANIM_RELEASE` battle frame.

| Move | START→HIT | HANDOFF→HIT | SFX→HIT | ANIM_DONE→RELEASE | RELEASE→HIT |
|---|---:|---:|---:|---:|---:|
| Quick Attack | 94f | 69f | 64f | 16f | 0f |
| Thundershock | 137f | 102f | 97f | 27f | 0f |
| Ember #1 | 91f | 89f | 84f | 0f | 0f |
| Ember #2 | 91f | 89f | 84f | 0f | 0f |

The repeated Ember trace is byte-for-byte timing-consistent at the presentation-frame level, which is useful evidence that the measured relationship is deterministic rather than incidental wall-clock jitter.

### Trace-only defects found

1. `HIT fromHandoff/fromLastSfx` logged as `?` because those timestamps lived only on the PMD source `combatMotionCue`, which can be consumed/replaced before `applyHitFx`.
2. A completed Sand Attack trace id later appeared on unrelated BIND animation SFX because `self.pmdLastTelegraph` still retained the closed status-move trace.

These are classified as diagnostic trace-lifecycle defects. No candidate-caused battle crash, ANR, or new Lua error was observed.

## Google Drive evidence authority

- Evidence folder ID: `1zowHTeDUdcxy8BVfIC-JJv5YFn2KLU6G`
- Raw evidence ZIP ID: `1W86gi9rh77XLycfbzV1RGJ6Kx9BdQklc`
- Analysis TXT ID: `19pP6OtuGcQKeZogvRITPLKfX4OvdkV6s`
- Result Doc ID: `1_7BhOzPuYr7QH2OsaZ1A3YqfBW8-cOZzylDNCdC0ITs`

## Next

`v0.1.96c` fixes only trace-state persistence and closure. Presentation behavior must remain identical to v0.1.96b. HIT_FRAME behavioral tuning remains deferred until the corrected trace is confirmed on Thor.
