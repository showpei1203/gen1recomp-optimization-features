# SoulGoldRecomp — S0-B Start Handoff

Date: 2026-08-29
Branch: `feature/soulgold-recomp-s0`
Parent implementation head before this handoff doc: `95868bd9c0e5c77f17118ff225a6fc60815d20bb`

## 1. Project contract

Build a SoulGold-native GBARecomp application/runtime. SoulGold remains the game; GBARecomp supplies the native runtime/platform. Large presentation/localization assets must be able to live outside the original 32 MiB cartridge image.

New mandatory rules:
1. Every meaningful development/test stage ships a user-downloadable handoff artifact.
2. The finished product must ship Traditional Chinese (`zh-Hant-TW`) support.

Authority:
- `authority/SOULGOLD_RECOMP_PROJECT_RULES_V1_20260829.md`
- `authority/SOULGOLD_ZH_HANT_TRANSLATION_AUTHORITY_V0_1_20260829.md`

## 2. S0-A sealed state

Status: **FORMAL PASS**

User evidence received: `SOULGOLD_S0_A_EVIDENCE_20260829_184108.zip`

Pinned source authority:
- SoulGold: `Eemeliri/soulgold` @ `a6efa38348f978348da9dc4f4a7878cccf27bfd0`
- GBARecomp: `mstan/gbarecomp` @ `ed9824b70aa350cd9e1653894beaf6b1b6b27787`
- EmeraldRecomp reference scaffold: `4e1f89669b9945e338c0f2e52816aa0533fa30d3`

S0-A exact ROM identity:
- bytes: `33,554,432`
- SHA-1: `d88b6a59802ccd442275ecbcfc9140fff34556dc`
- SHA-256: `f87a597e3034b9208ea1fb2637ad818d9ff14744433467f2454b4235b6482370`
- CRC32: `e3d02597`

Imported corpus reported by S0-A:
- functions: `15,519`
- ARM: `66`
- THUMB: `15,453`
- data symbols: `51,513`
- placeholder function names: `0`

Do not rerun S0-A unless its authority inputs are intentionally changed.

## 3. Current gate — S0-B

Goal: prove that the sealed SoulGold ROM/symbol corpus can become native generated C++ and link into a minimal SoulGoldRecomp runner.

New files:
- `tools/soulgold_recomp/S0_STAGE_B.ps1`
- `tools/soulgold_recomp/START_S0_B.bat`

S0-B pipeline:
1. verify S0-A WSL workspace and exact pins;
2. install missing host build prerequisites inside WSL (`cmake`, `ninja-build`, `pkg-config`, `libsdl2-dev`) when needed;
3. configure pinned GBARecomp;
4. build `gba_recompile`;
5. run `gba_recompile` against SoulGold with the imported function/data symbols and runtime code-copy overlay;
6. emit 64 deterministic native C++ shards;
7. configure the minimal SoulGoldRecomp runner;
8. link `SoulGoldRecomp`;
9. produce `SOULGOLD_S0_B_EVIDENCE_*.zip` under the Windows evidence directory.

S0-B PASS requires:
- `gba_recompile` built;
- generated `recompiled.h` present;
- generated `dispatch_table.cpp` present;
- generated symbol/data maps present;
- at least 2 native shards (target 64);
- minimal `SoulGoldRecomp` runner linked;
- evidence authority reports `RESULT=PASS`.

S0-B does **not** claim runtime/title-screen PASS. That belongs to S0-C.

## 4. User execution

After applying the S0-B handoff package to the existing project root, run:

`tools\soulgold_recomp\START_S0_B.bat`

If WSL asks for a sudo password while installing missing CMake/SDL dependencies, enter the WSL/Linux password. No characters are shown while typing.

Return either:
- `SOULGOLD_S0_B_EVIDENCE_*.zip` on PASS; or
- the latest `S0_STAGE_B_*.log` on FAIL.

Do not delete `~/SoulGoldRecomp_S0`; S0-B intentionally reuses the sealed S0-A build and symbols.

## 5. Traditional Chinese release lane

Traditional Chinese is mandatory, but implementation waits until native runtime boot is proven so text hooks are audited against a working executable rather than guessed.

Planned sequence:
- T0: discover exact SoulGold text engine / printer hook points from the sealed ELF symbols;
- T1: external UTF-8 `zh-Hant-TW` catalog with English fallback;
- T2: external CJK glyph asset/render path;
- T3: Taiwan official Pokémon terminology glossary + SoulGold-specific glossary;
- T4: full coverage and layout/control-code QA.

Do not consume the remaining ROM budget with a full CJK font/text duplicate. The translation layer belongs to the recomp/external asset architecture.

## 6. Next gate after S0-B

S0-C: first native runtime boot/title-screen validation.

Do not promote S0-C based on successful compilation alone. Runtime visual acceptance requires an actual launch result/screenshot/log.
