# M2R12 Source Delta Summary

Files changed from M2R11E candidate:

- `tools/generate_gen1_2_size_classes.py` (new): parses exact local SoulGold `species.h` + `species_info.h` and emits 251 height-derived size classes.
- `tools/generate_showdown_gen1_2_catalog.py`: rewritten so class table is the sole base-scale authority; emits 502 BACK/FRONT provider rows; geometry exceptions are scale-free.
- `SHOWDOWN_GEN1_2_GEOMETRY_EXCEPTIONS.tsv` (new): fit/anchor/policy-only overrides for known shape outliers.
- `tools/fetch_prepare_showdown_sprite.py`: manifest v4 plus local `source.gif` reuse on scale/geometry retune.
- `tools/validate_m2r12_full_size_class_scaleout.py` (new): synthetic 251/502 fixture, exact class ladder checks, no scale override and no front-upshift checks.
- `tools/validate_validator_contracts.py`: activates R-SD-045/R-SD-046 and tracks the M2R12 stage/contract table.
- `tools/soulgold_mgba/M2R12_STAGE_FULL_GEN1_2_SCALEOUT.sh` + `START_M2R12_FULL_GEN1_2_SCALEOUT.bat` (new): exact-source class generation, 502-provider cache migration, strict 502/502 gate, then full-catalog Sprite Lab runtime.
- `src/m2_showdown_overlay.cpp`: window title updated to M2R12 only; presentation semantics remain M2R11E.

Static status before handoff: PASS for synthetic 251 classes, synthetic 502 catalog, current presentation contract, provider registry, Sprite Lab, compile-order, size/perceptual gates, boot sync, teardown Z, scaleout and bash syntax.