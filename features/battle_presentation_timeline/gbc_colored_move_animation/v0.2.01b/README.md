# PMD v0.2.01b — GBC-A2 Visual Composition Fix TEST

Status: **Runtime PASS / Native Presentation Fidelity Visual FAIL / superseded by v0.2.01c**.

v0.2.01b corrected the obvious raw-tile fragmentation from v0.2.01a and proved the A2 runtime event/lifecycle integration. Thor evidence is healthy: fixture START/END/ONCE_GUARD all correct, all four move families covered, GBC errors=0, HIT_DRAW present for Psybeam/Surf, and sealed Action Binding/HIT_FRAME gates remain zero/healthy.

However, user visual review correctly identified that Surf still did not reproduce Pokémon Crystal's native presentation grammar. It rose, but read primarily as crest/ring objects instead of a crest riding above a continuous blue water body/curtain. Re-reading `pret/pokecrystal` confirms Surf is a two-layer animation: `BATTLE_BG_EFFECT_SURF` plus `BATTLE_ANIM_OBJ_SURF`.

Therefore this build is not eligible for visual acceptance or formal promotion.

## Candidate hashes
- main.lua `4cf22a673dc0752e89127f7799155a9fb9701903e162a12e72def8dd6e4d9e96`
- manifest.json `3f6b05aefd3d0a5749400719c2cfe88e8ade5725829ce0afde341146db0577b3`
- gbc_anim_data.lua `d93deb9fe02ee8dce796f5990844d4ddb422c8ecca34913ed0f98ec2a732ea51`
- TEST ZIP `834cdaa099eec3d040706e9e2e149a4e44e163844da6fedafa8d29de6f0ff141`

Static validation: **47 PASS / 0 FAIL**.

Drive Test Folder: `1pw5xndVdWx5_SHRJB_vO5Y9TJIcYhYgG`
Thor result: `THOR_RESULT_20260821_063127.md`
Evidence Folder: `1NSlnhbACszL-i6x7auol4egEfod4PNUr`
Evidence ZIP: `1coqzjkA3NMlGqEsr_uFNv5Nc3onVGUGm`
Diagnosis: `1iAjDv6yc6GDk2Y84xITAUFoaAxpLGoux`

## Formal promotion hard gate
The complete TEST-only `GBC_A2_FIXTURE` implementation, free-overworld B hook, fixture state, and fixture logging must be deleted before any formal release.
