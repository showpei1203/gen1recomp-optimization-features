# PMD v0.1.96c — Presentation Timeline II Trace Integrity

Status: **STATIC PASS / WAITING THOR RUNTIME TRACE**

## Purpose

Trace-only successor to v0.1.96b. It does not intentionally change animation timing, PMD body timing, audio lifetime, queue behavior, hit resolution, damage, accuracy, or Gen2 visual assets.

v0.1.96b proved that observed damaging moves resolve native `HIT` on the exact `ANIM_RELEASE` battle frame, but its diagnostic timestamps had two lifecycle defects. v0.1.96c fixes those defects before any HIT_FRAME behavioral work begins.

## Source authority

- Source: `pmd_idle_battle_sprites v0.1.96b`
- Source `main.lua` SHA-256: `126f645f9c18b1c258265045045d017e5bddd8c07198c68be2d6eccc1184b52f`
- Source `manifest.json` SHA-256: `05719ed704a9052ab51a305f0d2e4c54576a3548aa89a5ca5cb9a92706da33bf`

## Candidate identity

- Candidate `main.lua` SHA-256: `1169cf78409c9b01e7a06d42e3a91b1702e2a95a82f80b736d2a5a7b7d31556b`
- Candidate `manifest.json` SHA-256: `63371f9fef4996eef71b77b1ec4697a8bdac04c07bd59f068077449f1d7c0044`
- Candidate ZIP SHA-256: `22a50cdee8331a6b3013895826158363bc6d84e71d49dec8bd831e639ee99733`
- Static validation: PASS

## Trace-integrity fixes

1. Persist `HANDOFF`, `NATIVE_RELEASE`, `ANIM_ACTIVE`, last `SFX`, `ANIM_DONE`, and `ANIM_RELEASE` battle frames on the per-move telegraph context, not only on the source PMD cue.
2. Mark the trace closed at `ANIM_RELEASE` so unrelated later animation SFX cannot inherit a stale status-move id.
3. `HIT` now reports deltas from:
   - START
   - HANDOFF
   - last SFX
   - ANIM_DONE
   - ANIM_RELEASE
4. No presentation-clock or combat-runtime behavior is intentionally changed.

## Google Drive authority

- Candidate folder ID: `1MrUXayXzlv7-ky8xMnLjZt2MyZz_nhqg`
- Candidate ZIP ID: `1fTumXhbn3HlWmlFjZjKV5duBgpGGPgLE`
- Candidate `main.lua` ID: `1--96Z16BzkCcgxih0s1eZ3gZcSaerAlB`
- Candidate `manifest.json` ID: `1YseUKtjSNoLWYUElE1qTFMWNdy2STCIL`
- Diff ID: `1z7yq5oeD3qnJwEoGegorn94ELZSS_UyU`
- Static validation ID: `1pUax-He6muKxsBsV1mQbRp9Pv9LRmt2O`
- Package record ID: `1Y0bqahhyObuGYXwgVkf6GjHSvd8aqhry`

## Acceptance

Runtime trace PASS requires:

- `fromHandoff`, `fromLastSfx`, `fromAnimDone`, and `fromAnimRelease` are populated for damaging moves when the corresponding event exists.
- No unrelated post-release SFX is logged under a closed trace id.
- Presentation and combat behavior remain visually/functionally unchanged from v0.1.96b.
- No new Lua error, ANR, crash, or multi-hit regression.

Only after this corrected trace passes should HIT_FRAME behavioral tuning begin.
