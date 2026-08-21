# PMD v0.2.01f — GBC-A2.4 Psybeam Non-Contact Binding TEST

Status: **TEST-only / Static PASS / Thor visual confirmation pending**.

## Root cause
v0.2.01e fixed the split Psybeam beam, but Thor visual review found a one-frame Pikachu/attacker silhouette at the damage instant. Evidence shows Psybeam is routed as `family=strike action=attack`, then authoritative HIT starts `contact_recovery` and re-delivers `HIT_AUTH POSE sourceHitFrame=3`. Because the fixture attacker is Pikachu, that forced attacker pose is the visible one-frame silhouette.

## Correction
Add a narrow Psybeam semantic override in `moveActionForQueue()` before generic special routing:
- if native Shot exists: `shot / beam_release`
- otherwise keep the existing source-aware strike/attack body action but family=`beam_release`

This preserves the current seamless GBC WAVE stream while making Psybeam non-contact. `beam_release` is `contact=false`, `projectile=true`, `sustained=true`; `applyHitFx` must not start attacker contact recovery and HIT authority must be `behavioral=false`.

## Frozen scope
- Psybeam GBC WAVE rendering / 4f continuation: unchanged
- Quick Attack / Fury Swipes / Surf: unchanged
- GBC data + all 12 PNG assets: byte-exact from v0.2.01e
- fireHitFrameAuthority / actionBindingHit / actionBindingRecovery / completeActionBindingCue: unchanged
- damage/status/SFX/audio-tail/barrier/Depth/DS/THOR: unchanged

## Static validation
**56 PASS / 0 FAIL**. Lua 5.4 parser PASS for main and GBC data.

Candidate hashes:
- main.lua `cb91b7712ad40ec7a44c1bc4a3fa7d943f638c3af330ee352385284c59d88479`
- manifest.json `ae0871a629831adf8f35788525e509d2631bbe73d17f84f08fc331ca7187a8e6`
- gbc_anim_data.lua `b8619c28485ae5293f470ab9f00ed8a914a84fc42616e21d578ab6b904a255f0`
- TEST ZIP `c0b1d021a13d21aafbe41bf4dd6cb7556bbf764a6c4fdbb9c825d20d49a88a67`

Drive Test Folder: `12VB2mkloYXlw0nEO7IPhGLCpA6RpHgcL`
Complete ZIP: `1HxwJOQR1eNgqxYeGmULqPc6JmDHzxV0f`
Static: `1avjr3Fw4NEjfBQLpsPFDLgBWXZq1wH3m`
Spec: `1jL0MbShmbd89xcbsAITDwiTw1-j-sFBr`
Provenance: `1UTT_s2GPCQqnn6YcrEWvWzHs_yAuaOG8`
Diff: `16iK0vlfKbrCax7BGBtzT6QXiNuUbfi-h`
Manifest: `14PL1hGjiepyWtBDPon82sQFGdlkCeQM2`

## Thor gate
Use Psybeam only. Beam must remain seamless. Trace must show `family=beam_release contact=false projectile=true`, zero Psybeam `RECOVERY_START`, HIT_AUTH `behavioral=false`, and no one-frame attacker/Pikachu flash at damage.

Formal promotion still requires complete removal of the TEST-only B fixture.
