# HANDOVER M5A2 — Original Action Participant Authority

## User-approved direction
- Action Presentation follows original SoulGold.
- No bespoke Showdown action choreography by default.

## M5A2 changes
- Added `gBattleAnimAttacker` / `gBattleAnimTarget` to runtime symbol authority.
- Canonical attacker / target now come from SoulGold instead of treating every visible battler as an action participant during global `gAnimScriptActive`.
- Self-target is one canonical participant.
- Non-participant native motion is telemetry-only auxiliary motion.
- Current Showdown clip, native transform mirror, no epoch reset, and no second clock remain locked.

## New rules
R-SD-114 through R-SD-119.

## Run
`tools\soulgold_mgba\START_M5A2_ORIGINAL_ACTION_PARTICIPANT_AUTHORITY.bat`

## Next
M5A3: representative normal-play action evidence / coverage gate. If no visible defect remains, seal M5 and move to M6 Android ARM64 / AYN THOR. Add generic action enhancement only if runtime evidence proves a real need.
