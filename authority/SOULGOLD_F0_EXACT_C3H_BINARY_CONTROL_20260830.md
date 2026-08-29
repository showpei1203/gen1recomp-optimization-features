# SoulGoldRecomp F0 Exact C3H Binary Control

Date: 2026-08-30

## Trigger
E0 recovery still reproduced severe battle lag and the same IRQ non-return shape. E0 evidence then revealed that the exact historical C3H executable still survives at:

`/home/user/SoulGoldRecomp_S0/SoulGoldRecomp_c3h/build-c3h/SoulGoldRecomp`

Inventory metadata:
- mtime: `2026-08-30 02:56:50`
- size: `208,485,656 bytes`

This aligns with the original known-good C3H acceptance window:
- evidence archive around 02:53;
- formal promotion around 03:11;
- user acceptance recorded `BGM normal / clean`, `no perceived lag`, `battle entry works`.

## E0 mistake
E0 only searched the non-suffixed runner root:
`/home/user/SoulGoldRecomp_S0/SoulGoldRecomp/build-c3h/...`

The historical artifact is under the separate C3H runner tree:
`/home/user/SoulGoldRecomp_S0/SoulGoldRecomp_c3h/build-c3h/...`

Therefore E0 never executed the surviving historical C3H binary. Its dirty-tree rebuild result does not invalidate the original C3H artifact.

## F0 rule
Run that executable byte-for-byte:
- no compile;
- no recompile;
- no patch;
- no D1 static roots;
- no P1 LCD/interframe changes.

Capture:
- exact binary SHA-256 / size / mtime;
- `SoulGoldRecomp_c3h` HEAD/status/diff;
- `gbarecomp_c3h` HEAD/status/diff;
- critical engine source hashes;
- runtime cadence/coverage/log.

## Handoff
`SOULGOLD_RECOMP_HANDOFF_S0_F0_EXACT_C3H_BINARY_20260830.zip`

SHA-256:
`be27c4de02f622c0e37cbf40297ecf80c7dfc01b0fd6f61cddd7e33f1a7d2829`

## Decision
- If F0 is smooth with normal BGM, freeze the exact artifact and associated source trees as the true C3H runtime authority. All later optimization/presentation work must branch from this artifact lineage, not from reconstructed HEAD-only state.
- If F0 still lags, the original C3H acceptance did not exercise the same battle path/state or external runtime environment; investigate the difference using the exact artifact rather than further reconstruction.
