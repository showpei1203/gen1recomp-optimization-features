# GBC Colored Move Animation Layer I — GBC-A1

Status: DEVELOPMENT STARTED
Planned candidate line: v0.2.00a
Date: 2026-08-20

## Formal base
- pmd_idle_battle_sprites v0.1.99b — PMD Action Binding Authority I / Formal PASS
- HIT_FRAME Authority I — engine applyHitFx is sole authoritative HIT owner
- Presentation Timeline Authority
- DRAMATIC_SHAPE 1.8.2 × thor_battle_ui 0.3.41 sealed compatibility baseline
- Depth/Occlusion and Large Pokémon Presentation Bounds remain sealed

## Persistence rule
All development-relevant information must be persisted outside chat.
- Google Drive: specs, complete candidate/test ZIPs, tools, evidence/logs, PASS/FAIL records, Authority/Handoff updates.
- GitHub: source/config/tools/patch metadata/versioned technical docs.
- Failed candidates/evidence remain archived.
- No Linear.

## Goal
Build a colored Gen2/GBC move-VFX layer that consumes existing Presentation Timeline → HIT_FRAME → PMD Action Binding events. The GBC layer is a presentation consumer and must not become a new timing or damage authority.

## Hard boundaries
Do not change HIT ownership, Action Binding family/action selection, native damage/status, SFX/audio-tail ownership, DRAMATIC_SHAPE, THOR UI, Depth/Occlusion, Large Pokémon bounds, or species scale. The deferred Nidoran♂ vs Vulpix size-normalization issue is out of scope.

## GBC-A1 minimum benchmark
- Ember — projectile
- Thundershock — sustained/electric
- Thunder Wave — non-damage status

## GBC-A2 expansion
- Quick Attack or Tackle — contact
- Fury Swipes — multi-hit
- Ice Beam or Psybeam — beam
- Surf or Earthquake — area/full-screen observer

## Initial binding policy
- Projectile: spawn/travel from HANDOFF; visual impact resolves at authoritative HIT.
- Contact: PMD body remains primary; GBC layer adds impact at HIT.
- Multi-hit: each authoritative hit row may emit one impact; no continuation barrier re-arm.
- Sustained: VFX may live through native animation/audio-tail presentation but must not move damage/HIT timing.
- Status: may consume HANDOFF/ANIM_RELEASE but must never synthesize damage HIT.
- Area/full-screen: observer-only during first benchmark.

## First implementation deliverable
Source manifest/import path, minimal command representation, colored palette support, overlay renderer, Ember/Thundershock/Thunder Wave definitions, installer+rollback, collector+trace summary, complete test ZIP, static validation report, exact hashes.
