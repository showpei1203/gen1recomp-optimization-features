# PMD v0.2.01b — GBC-A2 Visual Composition Fix TEST

Status: **TEST-only / Static PASS / Thor Runtime + Visual pending**.

Builds directly on v0.2.01a after the Thor visual failure. It does not reopen Presentation Timeline, HIT_FRAME Authority I, PMD Action Binding Authority I, Depth/Occlusion, Large Pokémon bounds, DRAMATIC_SHAPE, or THOR UI.

## Visual corrections

- QUICK ATTACK: retains compact authoritative-HIT impact.
- FURY SWIPES: CUT-family tiles are composed into coherent diagonal slash objects instead of isolated quadrilateral fragments.
- PSYBEAM: PSYCHIC-family tiles are composed into a wave/crescent head with trailing tiles; `pendingHitGrace=192` keeps the record alive through observed late-HIT gaps and authoritative HIT creates a target burst.
- SURF: replaces the static lower row with a long battlefield waterline/wave rise, approximately y=126/122 to y=48/46 over 128 frames. Crest spirals are clipped so they read as wave crests rather than full circles. Runtime logs `GBC_VFX SURF_RISE`.
- Post-HIT visual proof uses `GBC_VFX HIT_DRAW`.

The analyzer now treats Fury Swipes continuation rows correctly: a continuation hit does not require a second HANDOFF, while native barrier re-arm remains forbidden.

## Candidate hashes

- main.lua `4cf22a673dc0752e89127f7799155a9fb9701903e162a12e72def8dd6e4d9e96`
- manifest.json `3f6b05aefd3d0a5749400719c2cfe88e8ade5725829ce0afde341146db0577b3`
- gbc_anim_data.lua `d93deb9fe02ee8dce796f5990844d4ddb422c8ecca34913ed0f98ec2a732ea51`
- TEST ZIP `834cdaa099eec3d040706e9e2e149a4e44e163844da6fedafa8d29de6f0ff141`

Static validation: **47 PASS / 0 FAIL**.

Drive Test Folder: `1pw5xndVdWx5_SHRJB_vO5Y9TJIcYhYgG`
Complete ZIP: `1Cy40_noocRaT98f7cHTT0QQQYiIWCIDD`
Static: `1-SE5w69Be8KqQewJl_mX7B3sX42eTiOx`
Diff: `1BKQFjhiOVGCnKyVD4trU4uoy21oJ2RXi`
Provenance: `1s-rkMsttzi23SO8UOLs9QLoI9-z7s4XH`
Package manifest: `1KYfKScNs8pulbNfpuyjXo6sffsV8z3HM`

## Formal promotion hard gate

The complete TEST-only `GBC_A2_FIXTURE` implementation, free-overworld B hook, fixture state, and fixture logging must be deleted before formal release. Runtime/visual PASS of this candidate does not waive that deletion requirement.
