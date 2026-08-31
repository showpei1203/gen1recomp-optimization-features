# Pokémon Anil zh-TW v0.8.7 INTERNAL HANDOVER — 2026-08-31

## Identity
- Project: Pokémon Anil DE 1.0.23 Traditional Chinese localization
- Checkpoint: v0.8.7 INTERNAL — Map81–85 + QA v1.7
- Status: INTERNAL CHECKPOINT, not yet device-promoted.

## Artifact authority
- ZIP: `ANIL_DE_1.0.23_ZH_TW_v0.8.7_INTERNAL_HANDOVER_M81_85_QA17_20260831.zip`
- SHA256: `e70ef156bcd3816705f397af7985b2647f419bc828abf2312748214ada7abe19`
- Drive ID: `1lLSG-Ews7kPdcZxMsHSmq55l2DklrtgS`
- Reusable Rules ZIP v1.7 Drive ID: `1Cs_YArXIB0kPgsZT0CETXTBi5atkr5ib`

## Baseline / authority
- Pokémon Anil DE 1.0.23 English / Essentials v21.1.
- Immediate saved baseline before this batch: v0.8.5 INTERNAL.
- Runtime lineage preserves v0.6 battle HUD/Summary fixes, v0.7 CJK wrapping and exact-version MapInfos localization.
- English-edition `translation` is semantic/control-code authority.

## Completed
1. Map 81 (v0.8.6 work): 35/35 EVENT_TEXT reviewed, 31 direct rewrites + 6 exact-English propagated fixes.
2. Map 82–85: 65/65 EVENT_TEXT reviewed, 58 direct rewrites.
3. Fixed Rocket Hideout / Giovanni / Archer / Cubone story dialogue, including `scot-free`, Rocket Grunts, Silph Scope and Super Secret Key terminology.
4. Removed all currently known `(法語)` contamination: 7 rows.
5. Removed all `頁:1` machine-shaped format corruption: 38 rows.
6. Added source-aware contracts: Silph Scope, Rocket Grunt(s), Super Secret Key, Hall of Fame.
7. Added opaque single-letter A-Z protection; this newly exposed 16 historical Script Text corruptions and all were repaired.
8. Repaired three late-map Rocket Grunt labels discovered by the new contract.

## QA
- Manifest rows: 21,438.
- Non-empty zh_tw: 21,437.
- Remaining exact `full_mt_argos_s2twp`: 9,186.
- v1.7 reusable/source-aware lint: HARD=0, WARN=0.
- Manifest -> DAT: 21,437 checked, 0 mismatch.
- Marshal compare vs v0.8.6: changed=127, issues=0.
- Total DAT delta vs v0.8.5: changed=164, issues=0.
- Scripts / MapInfos / Summary resource inherited unchanged.
- ZIP integrity: PASS.

## SEALED / never regress
- Resource paths and Modular UI suffixes are non-translatable.
- Preserve battle HUD, Move menu and Summary UI fixes.
- Preserve CJK formatter wrapping; no global Bitmap draw hook.
- Preserve exact-version localized MapInfos.
- DAT patch is key-based only.
- Exact-English templates only propagate on exact English-edition phrase identity.
- `P0/P1/P2/P3` and opaque one-letter labels remain source-exact unless semantics are proven.
- Official Taiwan Pokémon terminology has priority over MT transliteration.
- `Pokévial` / `PokéRider` remain protected custom brands.
- Every INTERNAL/public checkpoint refreshes HANDOVER + QA + Drive + GitHub authority.

## Known / unverified
- Latest physical device feedback in this development line was collected against public v0.7; merge newer screenshots before a public promotion.
- White-fog-after-name-entry behavior is not formally revalidated on this latest lineage.
- 9,186 rows still carry original Argos MT status and require continued prioritized polish.

## Exact next start
1. Start Map 86 EVENT_TEXT human review.
2. Run exact-English repeat discovery before edits.
3. Prioritize Poké Flute/Snorlax/Water/Misty language, then Cycling Road / Erika follow-up maps.
4. Run v1.7 full-manifest lint and clear HARD/WARN before the next checkpoint.
5. Refresh CURRENT_HANDOVER again before any next artifact is considered complete.
