# SOULGOLD M6X1R2 — Final Showdown Presentation Handover

Date: 2026-09-04
Branch: feature/soulgold-showdown-m6x1
Status: BUILD/STATIC PASS; AYN THOR R2 runtime gate PENDING.

Canonical build: GitHub Actions Run #9 / 33864081085 at 6a96944d054bdb15c11a00904986e4c57f78e881.

R2 exists because R1 showed two runtime regressions: player Showdown BACK flicker when switching Battle command <-> MOVE command, and stat-decrease presentation rendered as segmented/blocky strips.

The restored final authority chain is M2R5D -> M2R11E -> M2R12G -> M3S1. R2 uses bridge ABI v3, separates nativeVisible from presentationVisible, exports monBgActive and spriteId generation identity, keeps a last-known-good Android bridge snapshot, uses ROM-frame provider animation timing, suppresses provider-owned native monbg pixels, composites body/stat/lower UI at native mGBA resolution before one final scale, preserves x2/y2, removes BOUNCE_MON while retaining BOUNCE_HEALTHBOX, and forbids host raw BattleHealthboxInfo stride writes.

Run #9 passed permanent R2 presentation validation, SoulGold ROM compile, exact 32 MiB sealing, SGXP build, patched mGBA ARM64, Android contract audit and APK build. Artifact upload passed. The final compact-authority persistence step alone failed because tracked generated_bridge.h still held the pre-R2 address; the branch is now corrected to 0x02002ad4.

Binary authority:
- ROM SHA-256: 9030606040c40e81dff820489dcd9cd57ea4619e7c1a3b5bfeb7e702c9018c0e
- SGXP SHA-256: d149baa6e0c3a9cb57a28841f1687c825090f62234a82f5707a588f3d9313ccb
- APK SHA-256: 857e88e09e21d0b0e93223f20cd0641c3bebaae3cf9b20ee1f245131104eab07
- bridge EWRAM address: 0x02002ad4

Next device gate remains Sprigatito player BACK only. Required visual checks: zero flicker across repeated Battle/MOVE command transitions, continuous stat-decrease presentation with no block/stripe segmentation, no native first-frame flash, correct HUD/dialogue/monbg/stat layering, and no HUD/body coupling. Registry/audio sealed metrics must remain passing. FRONT and broad roster expansion remain blocked until this gate passes.
