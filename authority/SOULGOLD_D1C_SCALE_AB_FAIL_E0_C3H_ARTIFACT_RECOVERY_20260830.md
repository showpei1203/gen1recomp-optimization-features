# SoulGoldRecomp D1C Scale A/B Failure -> E0 C3H Artifact Recovery Authority

Date: 2026-08-30

## User result

D1C C3H-controlled presentation A/B was successfully executed after build throttling repair.

Manual result:
- Candidate A: 240x160 / scale 1 / LCD OFF / interframe OFF -> battle very laggy.
- Candidate B: 480x320 / scale 2 / LCD OFF / interframe OFF -> battle very laggy.

Evidence:
`SOULGOLD_S0_D1C_C3H_AB_EVIDENCE_20260830_065944.zip`

## Runtime interpretation

Candidate A remains near the expected ~59.7 FPS before battle, then collapses near battle transition to roughly the high-20 FPS range and reproduces the established IRQ non-return shape:

- PC / R15 = `0x00000018`
- CPSR = `0x60000092`
- `runtime_irq` handler fails to iret within the 4,000,000-dispatch watchdog.

Candidate B is also visibly very laggy in battle.

Therefore the primary regression is NOT explained by:
- LCD presentation filter;
- interframe persistence;
- scale 2 / 480x320 windowing alone.

D1C is rejected as a faithful replay of the known-good C3H runtime.

## Critical reconstruction flaw identified

D1B/D1C reconstruction scripts validated the original `~/SoulGoldRecomp_S0/gbarecomp` repository using only:

`git rev-parse HEAD == ed9824b70aa350cd9e1653894beaf6b1b6b27787`

They then created clean detached worktrees at that commit.

This proves Git commit identity but does NOT prove working-tree identity.

If C3A-C3H runtime debugging left tracked modifications or untracked runtime source in the original gbarecomp working tree, the later clean detached worktrees silently discarded those changes while still reporting the same HEAD.

Therefore the previous assumption:

`same HEAD + same C3H roots == same C3H runtime`

is invalid.

This is a high-priority hypothesis, not yet promoted as proven root cause.

## E0 recovery lane

Next checkpoint is `S0-E0 C3H Artifact Recovery`.

Recovery order:
1. capture the original gbarecomp working-tree status, worktree list, critical runtime diff and source hashes before changing anything;
2. inventory surviving SoulGoldRecomp executables;
3. if an executable whose build path explicitly identifies C3H survives, run that old binary directly with no rebuild;
4. otherwise copy the ORIGINAL dirty gbarecomp working tree, preserving uncommitted source, then rebuild from that snapshot;
5. preserve only C3F ROM-mirror dispatch compatibility + C3H IntrMain / IntrMain_RetAddr roots;
6. do not add D1 FastUnsafeCopy32 or SoundMainRAM roots;
7. do not add P1 LCD/interframe presentation changes;
8. run one battle and capture performance/audio evidence.

## Process correction

The E0 handoff intentionally removes PowerShell from the launch path. It uses BAT + Bash so the recurring generated-PowerShell parser/quoting failure class cannot block this checkpoint.

## Decision gate

- recovered old/dirty C3H is smooth with clean BGM -> freeze exact binary SHA-256 and exact dirty source snapshot as the true C3H runtime authority; all later optimization work branches from that snapshot.
- recovered old/dirty C3H is still laggy -> use the captured original source diff and runtime hashes to audit IRQ source/return semantics; do not return to presentation tuning.
