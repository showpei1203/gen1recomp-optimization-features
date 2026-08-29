# SoulGoldRecomp S0-B — FORMAL PASS

Date: 2026-08-29
Branch: `feature/soulgold-recomp-s0`

## Gate result

`S0-B = FORMAL PASS / SEALED`

User runtime evidence: `SOULGOLD_S0_B_EVIDENCE_20260829_185543.zip`

Verified evidence:

- `RESULT=PASS`
- SoulGold commit `a6efa38348f978348da9dc4f4a7878cccf27bfd0`
- GBARecomp commit `ed9824b70aa350cd9e1653894beaf6b1b6b27787`
- exact SoulGold ROM SHA-1 `d88b6a59802ccd442275ecbcfc9140fff34556dc`
- `gba_recompile` SHA-256 `ada6af9851167a1c3958f98db8522f6c42a26e52d7f916ad142017350ac528dd`
- generated native shard count `64`
- runner linked at `/home/user/SoulGoldRecomp_S0/SoulGoldRecomp/build-s0/SoulGoldRecomp`
- runner size `189473904` bytes
- runner SHA-256 `08647605065305fda3bdd9c13954a5626c500b95b48c790c8f7d00ccb3cf7200`
- SDL2 `2.32.10`

The build log reaches `138/138` and links the `SoulGoldRecomp` executable successfully.

## What S0-B proves

SoulGold's exact decomp build can be transformed through the pinned GBARecomp analyzer/emitter into sharded native C++ and linked against the shared GBA runtime as a native host executable.

S0-B does **not** claim that the executable boots correctly. Runtime boot, framebuffer output, self-heal coverage, and visual validation belong to S0-C.

## Rollback rule

S0-A and S0-B are now sealed baselines. S0-C failures must not cause regeneration or mutation of the S0-A ROM/symbol authority or the S0-B generated corpus unless evidence proves a problem in those layers.

## Permanent product requirements

1. Every meaningful checkpoint ships a user-downloadable handoff ZIP.
2. Final product must ship Traditional Chinese (`zh-Hant-TW`) via the planned external localization/glyph layer with English fallback.

## Next gate

`S0-C = runtime boot / framebuffer evidence`

Initial acceptance is headless and deterministic:
- exact runner/ROM/BIOS identity check;
- BIOS-HLE cart boot;
- bounded frame run;
- automatic PNG framebuffer dump;
- self-heal coverage/miss evidence;
- zero process exit code.

Interactive window/title-screen visual validation follows once the headless boot evidence is healthy.
