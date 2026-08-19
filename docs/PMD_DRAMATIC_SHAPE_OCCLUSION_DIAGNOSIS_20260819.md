# PMD × DRAMATIC_SHAPE Battle Occlusion Diagnosis

Date: 2026-08-19

## Finding

The reported tree/foreground occlusion problem is **not** a Presentation Timeline I/II regression.

Byte-exact comparison:

- Formal PMD source authority: `pmd_idle_battle_sprites v0.1.95c`
- v0.1.95c `main.lua` SHA-256: `11a1b8c3f8cdc098a8f7792b4b5fcb9557f62400999685dcc9337eb893a6f883`
- Current tested PMD candidate: `v0.1.96c`
- v0.1.96c `main.lua` SHA-256: `1169cf78409c9b01e7a06d42e3a91b1702e2a95a82f80b736d2a5a7b7d31556b`

The `battle.overlay` draw-order block is functionally unchanged between the two versions. Both versions draw PMD switch/body sprites as a screen-space overlay and contain no z/depth/occlusion integration. The v0.1.95c source itself states that PMD sprites are drawn later in `battle.overlay`.

## Runtime context

Current evidence confirms:

- `DRAMATIC_SHAPE 1.8.2` loaded
- `pmd_idle_battle_sprites 0.1.96c` loaded
- `thor_battle_ui` reports DRAMATIC_SHAPE 3D battle compatibility enabled

Evidence ZIP:
`GEN1RECOMP_PRESENTATION_TIMELINE_IIc_EVIDENCE_20260819_200104.zip`

SHA-256:
`0420ce211035f86584a1271da20232f7b16d862bf815184c0f4c93b045b3786a`

Drive evidence ID: `1OBxDEWpLRjgfSj04beGNXvraJ1hl5nK7`
Drive diagnosis ID: `1tqwHgGOSDP3DfXw-Shv_OkkwbvQmfiww`

## Classification

`PMD × DRAMATIC_SHAPE Integration Defect`

The PMD renderer replaces the native battler with a 2D overlay. DRAMATIC_SHAPE's battle system is depth-buffer based. A screen-space overlay does not naturally participate in tree/building occlusion.

## Preferred fix

Do **not** mix this into Presentation Timeline II.

Create a dedicated integration candidate that feeds the animated PMD frame into DRAMATIC_SHAPE's per-side battle texture / world billboard path so the battler participates in the 3D depth buffer.

Fallback only if that path is unavailable: use a DRAMATIC_SHAPE foreground/depth occlusion composite after PMD draw.

Avoid hard-coded tree masks, map-specific clip rectangles, or manual y-sort hacks.

## Timeline IIc side result

The same evidence run confirms the IIc trace-integrity fix is working: damaging HIT records now contain concrete `fromHandoff`, `fromLastSfx`, `fromAnimDone`, and `fromAnimRelease` deltas, with observed damaging moves still resolving at `fromAnimRelease=0`.
