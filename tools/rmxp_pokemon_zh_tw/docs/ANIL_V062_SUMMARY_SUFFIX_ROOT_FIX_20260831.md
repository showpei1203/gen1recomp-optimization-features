# Pokémon Anil DE 1.0.23 zh-TW v0.6.2 Summary Suffix Root Fix

## Exact root cause

The remaining black Trainer Notes page was not a missing PNG or a generic Summary renderer failure.

The exact Anil 1.0.23 runtime stacks Modular UI Scenes, [SV] Summary Screen, [MUI] Enhanced Pokemon UI and Translation_Patches. Modular UI Scenes implements:

```ruby
def self.get_info(menu, option, type = nil)
  option_hash = @@handlers[menu][option]
  ...
  when :suffix then return _INTL(option_hash["suffix"])
end
```

The exact handler for `:page_memo` has:

```ruby
"suffix" => "memo"
```

The generated zh-TW DAT contained the machine-translated runtime pair:

```text
memo -> 備忘
```

Therefore this line:

```ruby
suffix = UIHandlers.get_info(:summary, @page_id, :suffix)
@sprites["background"].setBitmap("Graphics/UI/Summary/bg_#{suffix}")
```

resolved to the nonexistent path:

```text
Graphics/UI/Summary/bg_備忘
```

instead of:

```text
Graphics/UI/Summary/bg_memo
```

This exactly matches physical behavior: overlay text, Pokémon sprites and separate controls render normally while only the full-page memo background is absent.

## Evidence

- Exact source baseline: `Pokemon Anil DE 1.0.23 ENGLISH.zip`
- Exact source SHA256: `759bf293d9adc45c85f1dd7c5756f097570d8ad464204f313b9b8575e0517fb3`
- Exact reference workflow: `33359850789`
- Exact reference workflow commit: `993b0963b60a118efdf50ad4f9468a4212ec38ce`
- Exact `bg_memo.png` exists, 512x384 RGBA.
- Exact `bg_memo.png` SHA256: `d5cbc6ff4e4ae99c481f3fb1552c0a3f71043f2f11170cf787ca25a6be4b976f`
- Core Summary scripts 303 and 410 were unchanged between exact source and v0.6.1.
- All known UI handler suffixes were audited: `allstats`, `area`, `data`, `egg`, `forms`, `info`, `memo`, `moves`, `ribbons`, `skills`.
- Before fix, the only translated suffix mismatch was `memo -> 備忘`.
- After fix, suffix mismatches = 0.

## v0.6.2 fix

1. Preserve the internal DAT key/value `memo -> memo`; mark it as `v062_internal_ui_suffix_protected` in the master TSV.
2. Restore exact Anil 1.0.23 `Graphics/UI/Summary/bg_memo.png` instead of the v4.0.2 diagnostic asset used by v0.6.1.
3. Do not add a global Bitmap hook, cache bypass, viewport workaround or duplicate underlay. The root cause is fixed at the source.
4. Fix the Trainer Notes starter literal `Laboratory` to display `大木研究所`; this value comes from `@pokemon.obtain_text` and bypasses `_INTL`.
5. Logical DAT diff vs v0.6.1 is exactly one mapping: `memo: 備忘 -> memo`.
6. Scripts diff vs v0.6.1 is only entry 449 `Translation_Patches`, for the `Laboratory` display correction.

## Prevention rule for the reusable RMXP localization toolchain

Do not machine-translate strings that are consumed as runtime identifiers, asset suffixes, filenames, paths, command IDs, symbols, handler keys or other non-display data, even when the original engine incorrectly wraps them in `_INTL`.

For Modular UI Scenes specifically, all `UIHandlers` `suffix` values must be protected and validated before DAT build. A post-build QA should fail if any discovered suffix resolves through the target language DAT to a different string unless an explicit language-specific asset with that translated suffix exists.

## Candidate

`ANIL_DE_1.0.23_ZH_TW_FULL_BETA_v0.6.2_SUMMARY_SUFFIX_ROOT_FIX_20260831.zip`

SHA256: `8c5dc7e8efbc3619714e6100d838ccc7b50254561a692acc01366af32c1ac7a4`

Drive candidate ID: `1Xk4KPIzP-22wR0yapIvfWFIiXjV8L7dh`

Status: static/root-cause QA PASS; AYN THOR/JoiPlay physical validation pending.
