# SoulGoldRecomp S0-C3H Fix1 — Per-document TOML Validation

Date: 2026-08-29
Branch: `feature/soulgold-recomp-s0`

## Observed C3H result

The first C3H candidate did **not** launch the game. This was a correct safe-stop before runtime.

Evidence:

- `RUN_EXIT_CODE=-999`
- `S0C3H_codegen_proof` is empty
- recompiler stopped before generation with:

```text
CONFIG ERROR [[resume_range]] [0x03000000,0x03000154)
is outside the program image and declared [[code_copy]] spans
```

## Cause

The IWRAM `[[code_copy]]` declaration exists in `SOULGOLD_runtime_copies.toml`.
The new C3H `[[resume_range]]` was provided in a separate overlay TOML.

Pinned GBARecomp structurally validates each TOML document before overlay merge. Therefore the C3H resume document could not see the `code_copy` from the previous document and was rejected before code generation.

This is a configuration packaging error, not evidence against the C3G diagnosis.

## Fix1

Create a candidate-only combined runtime config by concatenating:

1. the exact existing `SOULGOLD_runtime_copies.toml`, and
2. the reviewed C3H IntrMain `extra_func` + `resume_range` overlay.

Then pass the combined document once to `gba_recompile` instead of passing the two TOMLs separately.

The following remain unchanged:

- C3F ROM-mirror native-entry correction
- IntrMain runtime root `0x03000000`
- ROM source `0x09E864A0`
- required resume PC `0x0300012C = IntrMain_RetAddr`
- bounded resume range `0x03000000..0x03000154`
- four-item codegen hard gate
- sealed S0-A / S0-B / S0-C1 / S0-C2
- AYN THOR / Android ARM64 as the primary finished target
- Traditional Chinese `zh-Hant-TW` as a final-product requirement

## Promotion rule

C3H remains candidate-only until:

1. combined TOML passes structural validation;
2. generated dispatch contains `0x0300012C` as ARM `resume=1` routed to `gf_IntrMain`;
3. generated function contains `case 0x0300012C: goto L_0300012C` and label `L_0300012C`;
4. manual outdoor transition and performance/audio A/B are reviewed.
