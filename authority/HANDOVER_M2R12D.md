# SOULGOLD HANDOVER M2R12D (2026-09-01)

## Accepted baseline
- M1.4 sealed.
- M2R5D / M2R8F presentation semantics accepted.
- M2R11E HUD alpha-mask visual fix accepted by user.
- M2R12C successfully prepared and ran all 502 Gen1-2 providers; evidence dated 20260901_061234 is the sizing-data authority for M2R12D.

## Current problem
User reports that M2R12C still makes many Pokemon too large. Evidence review supports systemic oversizing rather than isolated species errors.

## Current solution
M2R12D implements global rendered-footprint normalization before class-relative scaling.
- safe envelope: 100x88
- synchronized global factor: 0.877192982456
- class multipliers: XS .60, S .68, M .76, L .84, XL .92, XXL 1.00
- final emergency 100x88 cap remains
- geometry exceptions cannot override scale or fit

## New regression contracts
- R-SD-051 GLOBAL_OCCUPANCY_NORMALIZATION_PRECEDES_CLASS_SCALE
- R-SD-052 GLOBAL_BASELINE_USES_MAXIMUM_REQUIRED_SHRINK_ACROSS_502
- R-SD-053 POST_GLOBAL_CLASS_MULTIPLIERS_MUST_BE_LE_1

## Test
Run `tools\soulgold_mgba\START_M2R12D_FULL_GEN1_2_SCALEOUT.bat`. Upload the resulting M2R12D evidence ZIP. Inspect `M2R12D_VISUAL_SIZE_AUDIT_*.tsv/json` plus representative screenshots.

## Do not regress
Directional HUD ownership, healthbox alpha masking, native fallback, HUD decouple, monbg suppression, teardown dialogue Z, provider registry, Sprite Lab, and source-GIF cache reuse remain locked.
