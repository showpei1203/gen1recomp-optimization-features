# SoulGold M1 mGBA Live State Correlator Handoff
Date: 2026-08-30

## Baseline
M0 mGBA Hardware Authority is FORMAL PASS.

mGBA pin:
`c65e8a3d4666b0ea68a01578232452f31b185332`

## M1 goal
Build a read-only live state bridge on top of the same mGBA core. Correlate SoulGold EWRAM/IWRAM with user-labelled gameplay states without modifying emulator correctness.

Markers:
- F1 OVERWORLD
- F2 NPC_DIALOGUE
- F3 POST_DIALOGUE
- F4 SCRIPTED_EVENT
- F5 BATTLE_IDLE
- F6 MOVE_MENU
- F7 MOVE_EXECUTION
- F8 EXIT

Each marker captures 12 EWRAM+IWRAM samples over roughly 1.1 seconds. The analyzer computes stable-byte contrasts and searches the existing SoulGold symbol corpus for exact battle/script data-symbol candidates.

## Delivery
`SOULGOLD_RECOMP_HANDOFF_M1_MGBA_LIVE_STATE_CORRELATOR_20260830.zip`

SHA-256:
`3fe8cb1ad68a8a9a0507bc08eb275fa5e03ee14d604a6d2866798eba9023ea9c`

## Guardrails
- mGBA remains sole hardware authority.
- M1 is observation-only.
- No gbarecomp runtime repair work.
- No PMD rendering yet.
- Promotion to M1 state API requires evidence-backed stable addresses.
