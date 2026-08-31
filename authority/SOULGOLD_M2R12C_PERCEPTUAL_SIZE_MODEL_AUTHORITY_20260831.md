# SOULGOLD M2R12C PERCEPTUAL SIZE MODEL AUTHORITY (2026-08-31)

## Status
Candidate. M2R11E remains the accepted presentation baseline. M2R12C changes only Gen1-2 automatic size-class derivation and adds visual-footprint auditing.

## Regression changes
- R-SD-045 is superseded by R-SD-049. Height-only is no longer sufficient authority.
- R-SD-049: Gen1-2 size class derives from exact SoulGold height + weight through the documented perceptual index.
- R-SD-050: a full 502-provider preparation must emit a class-relative visual-footprint audit.

## Locked scale ladder
XS=.60 / S=.72 / M=.84 / L=.96 / Huge=1.08 / Colossal=1.20.

## No per-species scale escape hatch
Geometry exceptions may tune only fit envelope, anchor, and geometry policy. They cannot alter base scale.

## Runtime non-goals
No battle-timeline, HUD, healthbox, provider ownership, monbg, animation-Z, teardown, or save semantics are changed by this milestone.
