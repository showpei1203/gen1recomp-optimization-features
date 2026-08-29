# SoulGoldRecomp S0-C3E Confirmed Finding + Primary Platform Rule

Date: 2026-08-29
Status: AUTHORITY

## Sealed baseline
- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 = FORMAL PASS / SEALED
- S0-C2 = FORMAL PASS / SEALED
- S0-C3 = FAIL / NOT PROMOTED

## S0-C3E confirmed finding
The no-game probe against exact sealed SoulGold artifacts returned:

`CLASSIFICATION=CANONICAL_STATIC_ENTRY_CONFIRMED`

Exact evidence:
- fatal alias PC: `0x0A23E920`
- canonical PC: `0x0823E920`
- physical ROM offset: `0x0023E920`
- ELF/imported symbol: `ScrCmd_lock`
- mode: THUMB
- generated dispatch: `{0x0823E920u, 1u, 0u, gf_ScrCmd_lock}`
- native entry `resume=0`
- stop PC `0x082414FC` resolves inside `RunScriptImmediatelyUntilEffect_InternalLoop`

Pinned GBARecomp memory mapping already treats 0x08/09, 0x0A/0B and 0x0C/0x0D as mirrors of the same physical Game Pak ROM, while pinned native dispatch uses the guest execution PC as an exact dispatch-table key.

Therefore the observed C3 fatal path is promoted from hypothesis to confirmed compatibility defect:

**SoulGold executes a valid Game Pak ROM mirror alias at 0x0A23E920, but native dispatch only contains canonical 0x0823E920. The exact-address miss incorrectly falls into self-heal instead of using the already-generated native ScrCmd_lock entry.**

The later IRQ/reset failure remains classified as downstream damage.

## Next gate
S0-C3F = separate ROM-mirror entry-only native-dispatch candidate.

Candidate safety policy:
1. exact dispatch lookup always wins;
2. alias fallback only after exact miss;
3. only 0x0A000000..0x0DFFFFFF Game Pak aliases;
4. canonicalize physical identity with `0x08000000 | (pc & 0x01FFFFFF)`;
5. use canonical native code only when the same-mode static entry exists and `resume == 0`;
6. do not canonicalize interior/resume entries in this candidate;
7. do not change BIOS, RAM dispatch, data addressing, PPU, save, or audio behavior;
8. build in a separate diagnostic/candidate GBARecomp worktree; sealed S0-B remains untouched.

## Audio/performance track
`AUDIO/PERF-01` remains OPEN.

User observation predates the outdoor crash:
- Mom dialogue already feels laggy;
- BGM already sounds fuzzy/dirty/crackly indoors.

C3F intentionally does not modify audio so crash progression and audio quality remain separable variables.

## Primary finished platform rule — AYN THOR
The primary finished hardware target is now formally:

**AYN THOR / Android ARM64**

PC/WSL is a development and diagnostic platform only.

From this checkpoint onward:
- runtime correctness fixes must be host-platform-neutral C/C++ unless isolated behind a host adapter;
- no correctness path may depend on Win32, DWM, PowerShell, WSL, or x86-64 behavior;
- after core S0-C runtime stability, SoulGoldRecomp must add Android NDK / ARM64 packaging;
- final validation must include AYN THOR real-device controller input, audio cleanliness, frame pacing/performance, save persistence, external mods/assets, and zh-Hant-TW rendering;
- PC PASS alone can never constitute final release PASS.

Pinned GBARecomp's SDL host already contains SDL GameController and touch-input machinery, which is useful for the Android direction, but the SoulGoldRecomp project still needs its own complete Android packaging/host integration and device QA gate.

## Permanent delivery requirements
1. Every meaningful checkpoint ships a user-downloadable handoff.
2. Final product ships Traditional Chinese `zh-Hant-TW` via external localization/glyph architecture with English fallback.
3. Final product must run acceptably on AYN THOR / Android ARM64; PC-only success is insufficient.
