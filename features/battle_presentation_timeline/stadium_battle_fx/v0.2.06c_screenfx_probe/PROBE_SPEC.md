# SBFX ScreenFx.present Bypass Probe I

Date: 2026-08-22  
Status: TEST-only / A-B localization probe

## Proven preconditions

- `STADIUM FX=OFF` removes the square battle mask but also removes Stadium move animations.
- With `STADIUM FX=ON`, disabling the other visible StadiumBattleFX options does not remove the square mask.
- PMD v0.2.06b core/HIT/Action Binding remained healthy in prior evidence; current Formal Authority remains PMD v0.2.04a.

## Single mutation

Patch the installed external StadiumBattleFX `main.lua` at the `render.hud` hook so that only:

`StadiumScreenFx.present(game, viewport)`

is bypassed. No StadiumBattleFX source is redistributed. The patcher requires exactly one matching call, backs up the exact installed `main.lua`, writes the patched source through ADB, and verifies the remote SHA-256.

## A/B gate

Primary observations:

1. square battle mask gone/still present;
2. Quick Attack / Ember / Fury Swipes move animations remain/vanish.

Surf fidelity is explicitly not the pass/fail gate for this probe.

## Interpretation

- Mask gone + move animation retained: localize to post-compose ScreenFx presentation path.
- Mask still present + move animation retained: move next to BattleHost/animation-layer projection.
- Move animation lost: restore immediately; ScreenFx.present has broader dependency than expected.

## Package

Chat delivery ZIP: `GEN1RECOMP_SBFX_SCREENFX_PRESENT_BYPASS_PROBE_I_20260822.zip`

SHA-256: `01d8d1cf557017a24316447e6c98537e5e1706849b70eaae8995dcacee550c24`

The ZIP contains only patch/restore/collector tooling plus documentation. It contains no StadiumBattleFX source, ROM, or ROM-derived assets.
