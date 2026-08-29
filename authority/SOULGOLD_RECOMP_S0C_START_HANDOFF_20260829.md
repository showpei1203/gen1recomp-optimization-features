# SoulGoldRecomp — S0-C Start Handoff

Date: 2026-08-29
Branch: `feature/soulgold-recomp-s0`

## Sealed baseline

- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED

S0-B verified:
- SoulGold exact ROM SHA-1 `d88b6a59802ccd442275ecbcfc9140fff34556dc`
- 64 generated native shards
- runner SHA-256 `08647605065305fda3bdd9c13954a5626c500b95b48c790c8f7d00ccb3cf7200`
- runner size `189473904` bytes

## S0-C purpose

Prove the linked SoulGoldRecomp runtime can actually boot the exact SoulGold image far enough to produce a meaningful framebuffer, while collecting self-heal coverage evidence.

S0-C first uses a deterministic headless gate rather than asking the user to judge a transient window.

## BIOS policy

GBARecomp's runtime asset gate requires a user-supplied GBA BIOS image even when `--bios-hle` is used for the boot path.

Required identity:
- size: 16,384 bytes
- SHA-1: `300c20df6731a33952ded8c436f7f186d25d3492`

No BIOS is included in this repository or handoff.

If the expected BIOS is not already at `~/SoulGoldRecomp_S0/gbarecomp/bios/gba_bios.bin`, `START_S0_C.bat` opens a Windows file picker once and copies only a hash-verified user-supplied image into the private WSL workspace.

## Candidate gate

`START_S0_C.bat` performs:

1. exact S0-B runner SHA-256 check;
2. exact SoulGold ROM SHA-1 check;
3. exact BIOS size/SHA-1 check;
4. 1200-frame headless run with `--bios-hle --no-window`;
5. PNG framebuffer dump;
6. self-heal coverage JSON / miss-fragment capture when emitted;
7. evidence ZIP creation.

Script success is `RESULT=CANDIDATE_PASS`, **not** a formal S0-C pass.

Formal S0-C requires review of the returned framebuffer and coverage evidence. A zero exit code with a blank/invalid framebuffer must not be promoted.

## Run

Extract the handoff ZIP at the root of the existing `gen1recomp-optimization-features` folder, overwrite/add files, then run:

`tools\soulgold_recomp\START_S0_C.bat`

Return on candidate pass:

`C:\Users\User\SoulGoldRecomp_S0\_evidence\SOULGOLD_S0_C_EVIDENCE_*.zip`

On fail return the newest `S0_STAGE_C_*.log`.

## Permanent project requirements

1. Every meaningful checkpoint ships a downloadable handoff.
2. Finished product must ship Traditional Chinese (`zh-Hant-TW`) via an external localization and glyph layer, using Taiwan official Pokémon terminology when available and English fallback for missing entries.

## Next if healthy

After framebuffer/coverage review:
- S0-C interactive title-screen validation;
- seal runtime boot;
- then start S1 external-asset proof and T0 Traditional Chinese text-engine audit.
