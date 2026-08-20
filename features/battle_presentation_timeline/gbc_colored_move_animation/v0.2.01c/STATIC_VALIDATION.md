# v0.2.01c Static Validation

Result: **82 PASS / 0 FAIL**.

Key gates:
- Lua 5.4 parser PASS for main.lua and gbc_anim_data.lua.
- manifest version/entry and TEST-only fixture warning valid.
- pre-GBC sealed prefix byte-exact to v0.2.01b.
- A1 Ember / Thundershock / Thunder Wave block byte-exact.
- GBC START/HANDOFF/HIT/COMPLETE lifecycle byte-exact.
- PMD-only patch; no DRAMATIC_SHAPE or THOR patch files.
- no new `love.timer`, `os.clock`, applyHitFx, or barrier timing changes.
- Surf: OAM-set marker, 22 tuples, base tile9, startY104, topY8, rise96f, hold128f, fall2px/f, endY112, BG wave amplitude2, solid curtain + crest/rise diagnostics.
- Quick Attack: six speed objects, native wait12, impact requires HIT.
- Fury Swipes: exact triple offsets left/right and row alternation.
- Psybeam: 10 pulses, interval4, 48f tail model, palette cycle, pending-HIT192, final burst HIT-owned.
- one-shot B fixture preserved as TEST-only with formal-removal warning.
- installer, collector, analyzer, rollback and provenance gates all PASS.

Candidate hashes:
- main.lua `3d72cb1eef2605d0e2cd99fae7be54c408e6f7a94f22f4452a1151eea1e623a5`
- manifest.json `5ef16bb80fea18faa385931732a33b7de61640fbecd4d3e400877600853bad77`
- gbc_anim_data.lua `5fe5c10344afe71c163821b91a3c9a11737f63e814ec7b66a9c999d24108d7fd`
- bubble_blue.png `275c03ef71e6c1cfa1ef75a1c6725e39cad47a7c2ea5deff06d201cc4b8de4d3`
- speed_gold.png `8e55f373406c1a4d0bbc47ba0eef585d42e3b5b23b1eb7a8dd8bcd69204c12a8`
- TEST ZIP `3c4ee428eb454b608015a7e17d849fad498b40d62d0ebfd584dcc335bd0371c1`
