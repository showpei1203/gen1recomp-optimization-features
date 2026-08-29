# SoulGoldRecomp S0-C2 Toolfix10 — Trace EOL Fix

Date: 2026-08-29

## Sealed baseline
- S0-A = FORMAL PASS / SEALED
- S0-B = FORMAL PASS / SEALED
- S0-C1 CART BOOT / RENDER = FORMAL PASS / SEALED

## Observed S0-C2 failure
The sealed runner, ROM and BIOS identities all matched, then GBARecomp rejected the replay file with `invalid input trace line:` and exit code 6.

Root cause: the PowerShell trace string already ended in LF, then `Set-Content` appended a Windows CRLF terminator. The resulting EOF was `...0x03FF\n\r\n`; `std::getline()` yielded a final line containing only `\r`, which the input-trace parser correctly rejected.

The START input itself is correct: KEYINPUT is active-low, all released is `0x03FF`, START pressed is `0x03F7` (bit 3 cleared).

## Toolfix10
- remove the trailing newline from the trace payload;
- write exact ASCII bytes with `.NET File.WriteAllText()`;
- preserve input timing: frame 0 `0x03FF`, frame 1250 `0x03F7`, frame 1270 `0x03FF`;
- keep captures at frames 1600 and 3000;
- no sealed runtime/ROM/BIOS artifact changes.

Formal S0-C2 promotion still requires visual review of both framebuffer captures and coverage evidence.

Permanent project rules remain: every meaningful checkpoint ships a downloadable handoff; final product must ship Traditional Chinese `zh-Hant-TW` through external localization/glyph assets with English fallback.
