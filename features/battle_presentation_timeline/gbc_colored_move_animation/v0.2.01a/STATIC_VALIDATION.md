# v0.2.01a Static Validation

Result: **45 PASS / 0 FAIL**.

Key gates:

- Lua parser PASS: `main.lua`, `gbc_anim_data.lua`.
- Candidate/data/manifest versions agree on v0.2.01a / GBC-A2.
- A1 fire/lightning/explosion assets retained byte-exact from v0.2.00b.
- Sealed function bodies retained byte-exact from v0.2.00b:
  - `Volatile.fireHitFrameAuthority` `1d546b19fbaa86d1d8e515a8d718772b7747be22bd92bb14af4401e6b6085151`
  - `Volatile.actionBindingHit` `f8b9b7b5146e8de2e7ede6bda12ce643f9d99b7cc7f780314611c7adbb36514c`
  - `Volatile.completeActionBindingCue` `b6fd3b025042502f0e23f49203c26e0655b2043ca20b5004904cb3a32911d826`
  - A1 Ember draw `b81ed47173b61158451474cfd38797e8d4be2d59f8152d70da5ebeeeefad6217`
  - A1 Thundershock draw `a069228ba11286501b780e94352dd8672e964c154f97bfa8709d973eb09cc5e2`
  - A1 Thunder Wave draw `f72f864e73a27fd2bb07a22fa3b9fc144ea90e97ed3a5b7b7d4f2fe2c3dc2fe6`
- Quick Attack colored impact is authoritative-HIT gated.
- Fury Swipes alternation uses actual hit-row index.
- Psybeam consumes existing handoff/anchors.
- Surf width is battle-layout aware (160 / 304).
- Pending-HIT retention is bounded and presentation-only.
- Late authoritative HIT re-anchors visual cleanup to `hitFrame`, preventing an old PMD COMPLETE from discarding the first HIT draw.
- TEST fixture uses a battle-local deep copy, exact four benchmark moves, deterministic battle-local RNG, Rattata seen restoration and one-shot B guard.
- No `mod.save` writes in the candidate.
- PATCH_FILES contain no DRAMATIC_SHAPE or THOR modifications.
- Installer, collector and both rollback lanes use exact SHA gates.

Static PASS is not Runtime/Visual PASS. Formal promotion additionally requires complete removal of `GBC_A2_FIXTURE` and the B hook.
