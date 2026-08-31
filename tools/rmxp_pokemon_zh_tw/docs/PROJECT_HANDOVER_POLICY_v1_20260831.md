# Project HANDOVER Policy v1

Effective: 2026-08-31
Scope: Gen1recomp-related development and reusable toolchains, beginning with RMXP/Pokémon Essentials zh-TW.

## Mandatory rule
From this checkpoint onward, every development turn that changes code, data, rules, QA, or a deliverable MUST create or refresh a HANDOVER.

This rule also applies to INTERNAL checkpoints. A version does not need to be public/test-ready before it gets a handover.

## Packaging rule
Every generated project/checkpoint ZIP MUST contain `handoff/CURRENT_HANDOVER.md`.

When tool access is available, the same handover state MUST also be synchronized to GitHub and Google Drive.

## Minimum HANDOVER contents
1. Project and checkpoint/version.
2. Date and exact authority/baseline.
3. Latest artifact filename.
4. Final ZIP SHA256 recorded externally after packaging. A ZIP cannot safely contain its own final hash without changing that hash.
5. Drive ID and GitHub synchronization reference when available.
6. Exact completed work with counts when possible.
7. QA results/evidence.
8. SEALED / do-not-regress rules.
9. Known issues and unverified assumptions.
10. Exact next starting point.
11. Important resume files/scripts/paths.
12. User test feedback not yet folded into a public build.

## Resume rule
A new chat/session must read the latest HANDOVER before changing the project. The handover is the first resume authority; older conversational recollection is secondary.

## No-background-work rule
A handover must never imply that development is continuing while no execution is occurring. It records the exact saved state so work can resume without pretending a background worker exists.

## Regression rule
Any user-visible bug that is fixed must become at least one of: automated lint/test, protected path/key/term, exact phrase template, or explicit SEALED regression item.

## Final-turn checklist
Before ending a development turn: save a checkpoint, run QA, refresh CURRENT_HANDOVER.md, calculate hashes, upload to Drive when available, sync rules/handover to GitHub when available, and report the saved checkpoint rather than a future promise.
