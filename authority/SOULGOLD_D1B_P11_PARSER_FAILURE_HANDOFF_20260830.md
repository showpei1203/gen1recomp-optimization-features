# SoulGoldRecomp D1B + P1.1 Parser Failure / Handoff Authority

Date: 2026-08-30

## Current failure

`START_S0_D1B_P11.bat` correctly stopped at its PowerShell parser precheck:

- `POWERSHELL_PARSE_FAIL`
- `S0_STAGE_D1B_P11.ps1:315:79`
- parser reports a missing expression.

Inspection of the delivered handoff shows the evidence `$pairs` array was malformed during package generation. Two array entries were concatenated without the required comma/newline separator around lines 314-315.

The game/recompiler did not run. C3H sealed correctness was not touched.

## Recurrence acknowledgement

This is not the first packaging/PowerShell failure in the SoulGoldRecomp bring-up. The exact token differs, but the same broad engineering failure class has repeated:

1. PowerShell automatic-variable collision (`$HOME` / `$home`).
2. Literal backtick-newline emitted outside a string in a PowerShell authority array.
3. CMD caret escaping leaked into an inline PowerShell parser command (`UnexpectedToken '^'`).
4. Current D1B package: malformed `$pairs` array / missing separator.

Earlier bootstrap work also had shell quoting / loop syntax failures. The repeated pattern is therefore **generated harness syntax reaching the user before package-level validation**, not four unrelated runtime bugs.

## New hard rule

From this checkpoint onward, a handoff that contains PowerShell launch scripts is not considered deliverable until it has a package-level preflight contract:

- parse every `.ps1` file using `System.Management.Automation.Language.Parser` on Windows before any build/game action;
- fail before WSL/recompiler/game startup if any parser error exists;
- verify required companion `.py` / `.sh` / `.toml` files exist;
- keep the launcher open on failure;
- preserve non-zero exit status;
- evidence packaging must remain reachable after runtime hang where technically possible.

The existing user-side parser gate was valuable because it caught this package before touching the project, but package generation must also be structurally reviewed before delivery.

## Project state for next chat

- C3H = FORMAL PASS / SEALED interactive correctness baseline.
- D1P1 = REJECTED: SoundMainRAM native caused BGM regression.
- D1A/P1.1 = REJECTED: map audio recovered, but battle caused lag/audio corruption and non-returning IRQ-vector logging.
- D1B/P1.1 = intended A/B isolation, but **NOT TESTED** because the delivered PowerShell stage failed parsing before execution.
- D1B intended correctness state:
  - FastUnsafeCopy32 native OFF;
  - SoundMainRAM native OFF;
  - C3H IntrMain / IntrMain_RetAddr + ROM-mirror correction ON;
  - P1.1 480x320 + LCD presentation ON.

## Permanent release requirements

- One shared core.
- Showdown Sprite Edition and PMD Sprite Edition as separate content providers.
- Traditional Chinese `zh-Hant-TW` required.
- Desktop target viewport/window: 480x320 (2x GBA framebuffer).
- mGBA-like LCD presentation track continues.
- Primary finished device: AYN THOR / Android ARM64.
