# SOULGOLD M2R12 FULL GEN1-2 SIZE-CLASS SCALEOUT AUTHORITY (2026-08-31)

## Promotion basis
M2R11E is user-accepted as good enough to continue. M2R12 promotes the size-class rule from representative QA to every base Gen1-2 species.

## Exact data authority
- `include/constants/species.h`: species IDs 1..251.
- `src/data/pokemon/species_info.h`: exact local SoulGold `.height` data.

No web Pokédex table and no hand-copied 251-row size list is authoritative.

## Size ladder
- XS <=0.5m => 0.60
- S 0.6-0.9m => 0.72
- M 1.0-1.4m => 0.84
- L 1.5-1.9m => 0.96
- XL 2.0-2.9m => 1.08
- XXL >=3.0m => 1.20

R-SD-045 locks the exact-source height mapping. Geometry exceptions may tune fit/anchor only and cannot override base scale, preserving R-SD-043.

## Cache migration
Prepared manifest v4 reuses each existing local `source.gif` when scale/geometry changes, then rebuilds BMP/timing data without downloading the same Showdown GIF again. R-SD-046 locks this behavior.

## Runtime QA
The Sprite Lab already cycles provider IDs 1..251. M2R12 prepares the complete 502-provider Gen1-2 catalog so PageUp/PageDown and Shift+PageUp/PageDown can QA the full catalog.

## Non-regression
M2R11E remains sealed: directional HUD ownership, alpha-masked player healthbox restore, class-only scale authority, native proxy ownership, safe fallback, animation foreground, monbg suppression, HUD decouple and teardown lifetime.