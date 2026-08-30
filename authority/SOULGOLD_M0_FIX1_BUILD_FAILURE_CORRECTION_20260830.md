# SoulGold M0 FIX1 Build Failure Correction

Date: 2026-08-30

## Initial M0 status

BUILD FAIL. This was not an mGBA runtime failure.

Observed compiler errors in `mgba_bridge_probe.cpp`:
- `va_start` was not declared
- `va_end` was not declared

Root cause: the bridge used `va_list`, `va_start`, and `va_end` but omitted `<cstdarg>`. The original local generation check used a permissive stub header that masked the missing dependency.

## FIX1

1. Add `<cstdarg>` explicitly.
2. Add `g++ -fsyntax-only` against the actual pinned mGBA `libretro.h` after checkout.
3. Add an EXIT trap so any non-zero stage exit attempts evidence packaging.
4. Copy `SOULGOLD_M0_MGBA_BRIDGE_EVIDENCE_*.zip` to the handoff root as well as the WSL evidence store.
5. Preserve the architecture reset: mGBA remains GBA hardware authority; Gen1recomp remains the enhancement layer; gbarecomp is experimental only.

No emulator or SoulGold behavior is changed by FIX1.
