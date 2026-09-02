# SoulGold M5A3 Representative Normal-Play Action Coverage Gate

Date: 2026-09-02

## Direction
Original SoulGold remains Action Presentation authority. M5A3 adds evidence quality, not choreography.

## Changes
- Adds observation-only monotonically increasing `context_id` for each SoulGold attacker/target context.
- Adds `analyze_m5a3_action_coverage.py` to summarize real normal-play action evidence.
- Attacker, target, self-target, auxiliary native motion and body-motion coverage are reported separately.
- Body motion and self-target are optional coverage. Some valid original actions do not translate/affine the battler.
- Static preflight can never promote M5 runtime PASS.
- Clip policy remains preserve-current; no rebind, epoch reset, or second clock.

## Rules
R-SD-120 through R-SD-125.

## Promotion
A runtime report with canonical attacker + target observations, completed action ends, and zero policy violations can promote M5 action mirroring. Until then M5A3 remains runtime-pending.
