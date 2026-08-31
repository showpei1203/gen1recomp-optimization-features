# M2R12D GLOBAL OCCUPANCY NORMALIZATION AUTHORITY (2026-09-01)

## User rule
1. Add an actual on-screen occupancy rule.
2. If a displayed Pokemon exceeds the safe range, compute the required shrink.
3. Use the strongest required shrink as one synchronized global shrink for every Pokemon.
4. Then shrink again according to size class.

## Important implementation choice
The baseline is derived from rendered alpha footprint in the successful M2R12C 502-provider evidence, not raw GIF canvas. Raw canvas would let one extreme animation pose shrink the entire Pokedex absurdly.

## Evidence-derived baseline
- Providers measured: 502
- Common safe rendered envelope: 100 x 88 px
- Occupancy vs 240x160 battle view: 41.67% width / 55.00% height
- Strongest synchronized shrink: 0.877192982456
- Limiting set includes Mantine front, Entei back, Mantine back, Lugia back

## Post-global class multipliers
- XS 0.60
- S 0.68
- M 0.76
- L 0.84
- XL/Huge 0.92
- XXL/Colossal 1.00

All class multipliers are <=1.0. Size class may only shrink further after global normalization.

## Final emergency cap
Every provider still carries the same 100x88 fit cap. This is a safety net for unusual animation frames, not a per-species sizing authority.

## Geometry exception rule
Per-species geometry exceptions may change anchor/policy only. They may not override fit dimensions or scale.

## Regression IDs
- R-SD-051: global occupancy normalization precedes class scale.
- R-SD-052: global baseline uses maximum required shrink across the 502 rendered footprints.
- R-SD-053: post-global class multipliers must be <=1.0.
