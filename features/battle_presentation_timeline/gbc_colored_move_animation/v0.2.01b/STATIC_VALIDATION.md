# v0.2.01b Static Validation

Result: **47 PASS / 0 FAIL**.

Key gates:

- Lua 5.4 parser PASS for `main.lua` and `gbc_anim_data.lua`.
- Version/package/hash consistency PASS.
- Sealed `Volatile.fireHitFrameAuthority`, Action Binding HIT/COMPLETE, and A1 Ember/Thundershock/Thunder Wave draw bodies remain byte-exact against v0.2.01a.
- CUT composite object implementation present.
- PSYCHIC composite object implementation present.
- Psybeam pending-HIT retention increased to 192 frames; authoritative HIT_DRAW proof required.
- Surf rise lasts 128 frames, moves from lower to upper battlefield, and logs SURF_RISE.
- Surf crest clips the 24x24 spiral source instead of rendering complete static circles.
- Fury Swipes analyzer accepts continuation rows without a repeated HANDOFF while retaining continuation barrier re-arm=0 as a hard gate.
- Late authoritative HIT re-anchors only visual cleanup.
- TEST-only B fixture remains isolated/battle-local and is still a formal-release deletion gate.
- No DRAMATIC_SHAPE or THOR source is patched.
- Installer and rollback lanes use exact SHA gates.

Candidate hashes:
- main `4cf22a673dc0752e89127f7799155a9fb9701903e162a12e72def8dd6e4d9e96`
- manifest `3f6b05aefd3d0a5749400719c2cfe88e8ade5725829ce0afde341146db0577b3`
- data `d93deb9fe02ee8dce796f5990844d4ddb422c8ecca34913ed0f98ec2a732ea51`
- ZIP `834cdaa099eec3d040706e9e2e149a4e44e163844da6fedafa8d29de6f0ff141`

Static PASS is not Runtime/Visual PASS.
