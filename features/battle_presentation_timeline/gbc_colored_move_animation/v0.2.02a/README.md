# v0.2.02a — GBC Colored Move Animation Layer I Formal Promotion Candidate

Source base: exact v0.2.01f.

This candidate removes the complete TEST-only GBC-A2 B fixture and freezes all validated GBC visual/runtime behavior.

Removed:
- `GBC_A2_FIXTURE` state / helpers / logging
- battle-local benchmark launcher
- `OverworldController.handleInput` B interception
- one-shot fixture state

Frozen from v0.2.01f:
- Ember / Thundershock / Thunder Wave
- Quick Attack
- Fury Swipes exact CUT frameset
- Psybeam seamless WAVE stream + `family=beam_release` semantic
- Surf water curtain / crest
- HIT_FRAME / Action Binding / audio / barrier ownership
- `gbc_anim_data.lua` and all 12 GBC assets
- DRAMATIC_SHAPE / THOR / Depth authority

Static Validation: **42 PASS / 0 FAIL**.

Candidate hashes:
- main `f574c138ca224ba06fb680fef59b5ff8869f6580da3c84398c3796a2c6d5a65e`
- manifest `7e823d33645f82758cda4cf8cc28279a2ffb721031821808233e84e259db3eda`
- data `b8619c28485ae5293f470ab9f00ed8a914a84fc42616e21d578ab6b904a255f0`
- complete ZIP `2b6407ada7c09d4383a114a52d43771d76eb458b1ff6666199c1b995d1acc3e0`

Drive Test Folder: `1DBtVinDxPkc1VHUqY1cFwtx2R1EEBJBy`
Complete ZIP: `1qmqoWhT99_PBzaPoS9oESo7Qt-wlJ_dM`
Static: `1YLOc_AGVtvWYPpY1WqfrqYK1cTQrtAUZ`
Spec: `1PNCGNnhDUfpi_1yAxWLQ98wCALdSE0Ch`
Diff: `1bjEYgStB4gh22ofonhVMD9JVrK8rNjDb`
Manifest: `1sIojXI5CbF061-KI-ScauWyikGxVjapb`

Thor promotion smoke: install from exact v0.2.01f, launch to normal free overworld, press B once, verify the old benchmark battle does NOT start, then run the promotion collector. No inaccessible move needs to be re-exercised because the validated move bodies are statically frozen from v0.2.01f.