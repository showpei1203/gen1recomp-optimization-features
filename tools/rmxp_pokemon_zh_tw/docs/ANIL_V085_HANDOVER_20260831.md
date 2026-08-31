# CURRENT HANDOVER — Pokémon Anil zh-TW

## Identity
- Project: Pokémon Anil DE 1.0.23 Traditional Chinese localization
- Checkpoint: v0.8.5 INTERNAL — Map72–80 + source-aware QA v1.6
- Date: 2026-08-31
- Status: INTERNAL CHECKPOINT. User continues physical testing on public v0.7; do not claim this INTERNAL build is device-validated.

## Authority / baseline
- Game authority: Pokémon Anil DE 1.0.23 English / Essentials v21.1.
- Runtime lineage preserves v0.6 battle UI/Summary fixes, v0.7 CJK wrapping and localized MapInfos.
- Immediate checkpoint baseline: v0.8.4 INTERNAL.
- English-edition `translation` remains semantic/control-code authority.

## Completed this checkpoint
1. Map 72–80 EVENT_TEXT: 212/212 manually reviewed.
2. 169 direct Map text rewrites.
3. 89 exact-English/repeated regression fixes, including rest/heal dialogue, Saffron gate guards, Pokévial, opaque P0–P3 labels and Abilities Expert.
4. Source-aware lint v1.6 introduced. Initial run exposed 40 HARD issues beyond the old blacklist; all fixed.
5. 105 Mega Stone terminology warnings fixed only where English source contains `Mega Stone`, avoiding false replacement of legitimate 巨石.
6. 33 `寶可夢號` suffix corruptions cleaned.
7. Severe semantic residues fixed: `異性戀` for otherworldly, `海峽客` for Channeler, `命運之邦`, `爾時世尊`, Girafarig transliteration, critical-hit terminology, Coin Case and Pokévial runtime strings.
8. Final DAT delta vs v0.8.4: 436 values.
9. Remaining original Argos-MT status: 9,285 rows.

## QA
- Manifest entries: 21,438.
- Non-empty zh_tw: 21,437.
- reusable/source-aware lint v1.6: HARD=0, WARN=0.
- Manifest → DAT verification: 21,437 checked, 0 mismatch.
- Marshal structure compare vs v0.8.4 DAT: changed=436, issues=0.
- Scripts/MapInfos/Summary bg are inherited unchanged from v0.8.4 lineage.
- ZIP integrity: PASS.

## SEALED / do not regress
- Never translate resource paths or Modular UI suffixes.
- Preserve battle HUD, move menu and Summary UI repairs.
- Preserve CJK formatter wrapping; no global Bitmap draw hook.
- Preserve localized exact-version MapInfos.
- DAT patch key-based only.
- Exact-English templates may be reused globally only when the English-edition phrase matches exactly.
- Official Taiwan terminology wins over MT transliteration.
- `Pokévial` / `PokéRider` are protected custom brands until a controlled glossary explicitly renames them.
- `P0/P1/P2/P3` are opaque labels and stay unchanged unless exact UI semantics are confirmed.

## Artifact
- `ANIL_DE_1.0.23_ZH_TW_v0.8.5_INTERNAL_HANDOVER_M72_80_QA16_20260831.zip`
- SHA256: `81d590b02496a350112ada835b08b8a642ee0f55b5f89f92d3191522b307ea06`
- Drive ID: `1BGbIIJrHkPKcYFkY_YAhk31MyctiD6AL`

## Known issues / unverified
- User is still testing public v0.7. Any new device feedback must be merged before the next public candidate.
- White-fog-after-name-entry path remains unverified on this latest lineage. Do not claim formal fix without device confirmation.
- 9,285 rows still retain original Argos MT status and require continued prioritised human polish.

## Next exact starting point
1. Start EVENT_TEXT human review at Map 81.
2. Before per-map edits, run exact-English repeated-phrase discovery against remaining MT rows.
3. Prioritize Map 81 onward and source-aware WARN/HARD discoveries.
4. Merge any new v0.7 device feedback.
5. Every subsequent development checkpoint MUST refresh CURRENT_HANDOVER and ship it inside the artifact.
