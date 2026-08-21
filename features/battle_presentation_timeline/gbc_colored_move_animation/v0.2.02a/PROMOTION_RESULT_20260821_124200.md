# v0.2.02a Promotion Result — 2026-08-21 12:42

Status: **FORMAL RUNTIME PASS**

Evidence ZIP SHA-256: `5d1802169fdf34e798c373afd1602bf865c56ccdda59d83827bf267635ea27d9`

## Promotion smoke

- RESULT=PASS
- GBC_LAYER_LOAD=True
- GBC_A2_FIXTURE_LOG_LINES=0
- GBC_VFX_ERRORS=0
- CURRENT_FATAL_LOVE_ANR_ERRORS=0
- HASH_GATE=PASS

Installed PMD, DRAMATIC_SHAPE and THOR hashes match the accepted promotion candidate / sealed dependencies.

Normal runtime in the promotion session also exercised GBC VFX for Thundershock, Thunder Wave and Quick Attack with no GBC errors.

Depth smoke retained:
- enemy presentation=(80,96)
- enemy physical=(80,106)
- overflowPx=10
- player visible body=legacy overlay
- player silhouette=3D shadow only

Historical `lua-error.log` rows are dated 2026-08-10 through 2026-08-15 and are not current promotion-run errors.

## Promotion meaning

v0.2.02a is derived from v0.2.01f and removes only the TEST-only A2 B fixture / benchmark plumbing. GBC move visuals, Psybeam `beam_release` semantics and sealed battle authorities are frozen from the accepted test state.

Formal Runtime Authority is therefore accepted.
