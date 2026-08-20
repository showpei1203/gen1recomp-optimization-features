# PMD v0.2.01c — GBC-A2.1 Native Presentation Reconstruction TEST

Status: **TEST-only / Static PASS / Thor Runtime + Visual pending**.

This candidate supersedes v0.2.01b for GBC-A2 visual validation. v0.2.01b proved the runtime event chain but failed native-presentation fidelity, especially Surf.

## Development rule

GBC move import must reconstruct the original presentation grammar from `pret/pokecrystal`: animation script, BG effect, object/frameset/OAM composition, loops/waits, and palette behavior. Raw tiles alone are not sufficient.

## Reconstructed benchmarks

- **Surf**: continuous blue background water curtain + scanline wave deformation + foreground OAM22-inspired 22-tile crest; native-like rise/hold/recede lifecycle. Existing authoritative HIT timing is unchanged.
- **Quick Attack**: six SPEED-derived lines in the first 12f after HANDOFF, with compact impact only at authoritative HIT.
- **Fury Swipes**: three CUT slash objects per authoritative hit row, alternating direction by hit index.
- **Psybeam**: 10 wave pulses at 4f intervals, subtle palette/background cycle, and final target burst owned by authoritative HIT.

Authority remains `Presentation Timeline → HIT_FRAME → PMD Action Binding → GBC VFX consumer`.

## Static validation

**82 PASS / 0 FAIL**. Both Lua files parse under Lua 5.4. Sealed pre-GBC Timeline/HIT_FRAME/Action Binding and A1 Ember/Thundershock/Thunder Wave behavior remain byte-exact. No DRAMATIC_SHAPE or THOR source modifications; no new independent clock.

## Hashes

- main.lua `3d72cb1eef2605d0e2cd99fae7be54c408e6f7a94f22f4452a1151eea1e623a5`
- manifest.json `5ef16bb80fea18faa385931732a33b7de61640fbecd4d3e400877600853bad77`
- gbc_anim_data.lua `5fe5c10344afe71c163821b91a3c9a11737f63e814ec7b66a9c999d24108d7fd`
- bubble_blue.png `275c03ef71e6c1cfa1ef75a1c6725e39cad47a7c2ea5deff06d201cc4b8de4d3`
- speed_gold.png `8e55f373406c1a4d0bbc47ba0eef585d42e3b5b23b1eb7a8dd8bcd69204c12a8`
- complete TEST ZIP `3c4ee428eb454b608015a7e17d849fad498b40d62d0ebfd584dcc335bd0371c1`

## Drive

- Test Folder `1rNP_bkRkhlb5oKTPX3sJrVvRZjNsFmqL`
- Complete ZIP `10ZSpwwllZv7gUTRoX-TaBgHsrbFc8Vn8`
- Native Presentation Spec `1xw_7aXZFDXmDxefA6mE87yv4OFY0qVMH`
- Static Validation `1dJEb_Gnza8jLhY2hggiH5WAFjgAtPf9F`
- Source Provenance `1gexzQTZTjwmeBqvMD_-l6_fk9r2K74jw`
- b→c Diff `1vXjFyxMT7EpyMtWe0M0bpNyZQM5Iyl8x`
- Package Manifest `1zHSYG64L0frzzt2un-41rHhBwSe9nddj`

## Formal promotion hard gate

The complete TEST-only `GBC_A2_FIXTURE` block, free-overworld B hook, fixture state, and fixture logging must be deleted before formal release. Thor Runtime/Visual PASS does not waive this requirement.
