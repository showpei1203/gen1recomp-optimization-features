# SoulGoldRecomp S0-C3G — IntrMain Resume Gap Confirmed

Date: 2026-08-29
Branch: `feature/soulgold-recomp-s0`

## Evidence reviewed

`SOULGOLD_S0_C3G_EVIDENCE_20260829_204737.zip`

## Formal finding

S0-C3G static probe completed successfully and confirms the next runtime blocker after the C3F ROM-mirror candidate:

- `MISS_PC=0x0300012C`
- ELF symbol: `IntrMain_RetAddr`
- exact static dispatch entries at `0x0300012C`: **0**
- `.iwram` VMA: `0x03000000..0x03000198`
- `.iwram` LMA: `0x09E864A0`
- bytes at runtime `0x0300012C` match the ROM LMA bytes exactly
- the instruction at `0x0300012C` is the ARM IRQ-handler return continuation (`ldmfd sp!, {lr}`)
- nearby native dispatch currently starts at `CopyTable` / `0x0300015C`; `IntrMain` is not present as a native host

Classification:

`INTRMAIN_INTERIOR_PC_WITHOUT_EXACT_STATIC_DISPATCH`

## 0x030016AC is secondary fallout

The interpreter later reports Undefined at `0x030016AC`, but the executable `.iwram` section ends at `0x03000198`. Therefore `0x030016AC` is outside the copied executable IWRAM image and lies in IWRAM BSS/data territory. It is not a second legitimate code root. It is evidence that interpreter execution starting from the missing `IntrMain_RetAddr` resume path eventually wandered into data.

Do not add an opcode patch or a fake function at `0x030016AC`.

## Correct next mechanism

Pinned GBARecomp already supports native mid-function resume aliases:

- `[[extra_func]] resume = true`
- `[[resume_range]]`
- generated dispatch entries with `resume=1`
- emitted host functions route `g_runtime_resume_pc` to an interior `L_<PC>` label

C3H therefore must use the recompiler's existing resume model rather than a runtime address special-case.

Candidate plan:

1. keep the C3F ROM-mirror entry fix in a separate platform-neutral GBARecomp worktree;
2. add `IntrMain` root at runtime `0x03000000`, source `0x09E864A0`, ARM;
3. add bounded ARM `resume_range` covering `0x03000000..0x0300015C` (ending before `CopyTable`);
4. regenerate candidate SoulGold native shards in a separate runner tree;
5. hard-gate before launch that:
   - `0x03000000` has an ARM native root;
   - `0x0300012C` has an ARM `resume=1` dispatch entry;
   - generated host body contains the resume route/label for `0x0300012C`;
6. run the same Mom -> exit house A/B path;
7. collect coverage, miss, cadence, final framebuffer and save even on failure.

## Performance/audio significance

`0x0300012C` was already a high-frequency bridge in earlier C2 evidence. If native resume removes repeated interpreter trips in the IRQ path, C3H may improve both frame pacing and the previously reported dirty/fuzzy BGM. This is a hypothesis to be measured, not a reason to close `AUDIO/PERF-01` early.

## Sealed state

- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 = FORMAL PASS / SEALED
- S0-C2 = FORMAL PASS / SEALED
- S0-C3 = FAIL / NOT PROMOTED
- S0-C3F = FAIL / NOT PROMOTED, but ROM-mirror correction remains a confirmed prerequisite
- S0-C3G = STATIC PROBE PASS / finding confirmed

## Permanent project requirements

1. Every meaningful checkpoint ships a downloadable handoff.
2. Final product ships Traditional Chinese `zh-Hant-TW` through an external localization/glyph layer with English fallback.
3. Primary finished hardware target is AYN THOR / Android ARM64; correctness fixes must remain platform-neutral C/C++ unless isolated behind a host adapter.
