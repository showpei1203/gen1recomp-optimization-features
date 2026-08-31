# SoulGold M2R12 Current Handoff

Current candidate: **M2R12 Full Gen1-2 Size-Class Scaleout**.

Run: `tools\soulgold_mgba\START_M2R12_FULL_GEN1_2_SCALEOUT.bat`

Promotion basis: M2R11E user visual acceptance.

M2R12 changes:
- generates 251 size classes from exact local SoulGold `species_info.h` height values;
- generates 502 BACK/FRONT provider rows with class-only base scale;
- size ladder XS=.60, S=.72, M=.84, L=.96, XL=1.08, XXL=1.20;
- geometry exceptions cannot override scale;
- manifest v4 reuses local `source.gif` on geometry/scale retune;
- full provider gate requires 502 requested / 502 prepared / 0 failed;
- Sprite Lab PageUp/PageDown remains visual-only and can cycle IDs 1..251.

Permanent non-regression: R-SD-042, R-SD-043, R-SD-044 plus new R-SD-045 and R-SD-046.