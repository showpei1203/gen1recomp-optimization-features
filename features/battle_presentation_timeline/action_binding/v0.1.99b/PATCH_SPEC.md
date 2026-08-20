# v0.1.99b Patch Spec

The runtime delta is intentionally one narrow guard inside `combatMotionPose`.

When all are true:

- source `motionElapsed >= total`
- `cue.nativeSync`
- `cue.nativeHandoffReached`
- `Volatile.actionBindSustainedFamilies[cue.family] == true`
- `battle.animPlaying == true`

then the cue must not be cleared. Instead it renders the source hitFrame and logs one `ACTION_BIND SUSTAIN_HOLD` event. Existing `nativeAudioTailHold` takes over after AnimPlayer DONE. No timing source is added.

The analyzer is also corrected so `SUSTAINED_AUDIO_TAIL_ROWS` only counts rows whose START has `sustainedCandidate=true`; v0.1.99a had incorrectly counted every positive audio tail as sustained. Under the corrected interpretation, v0.1.99a has two sustained rows and both fail.

Acceptance:

- sustainedCandidate coverage present
- `SUSTAINED_COMPLETE_BEFORE_ANIM_RELEASE=0`
- `ACTION_BIND_HIT_DUPLICATES=0`
- contact recovery remains at HIT
- projectile contact-recovery leakage remains 0
- status unexpected HIT remains 0
- HIT_AUTH duplicate/re-arm/release-delta/status-false-hit all remain 0
- DS/THOR sealed hashes unchanged
