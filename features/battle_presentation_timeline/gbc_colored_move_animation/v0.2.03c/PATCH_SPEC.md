# GBC-A3.2 v0.2.03c Scratch Handoff Hold Fix TEST

## Evidence basis
`GEN1RECOMP_PMD_GBC_A3_1_v0203b_EVIDENCE_20260821_203134.zip`

## v0.2.03b result
Collector `RESULT=FAIL`, but the failure is split into one tooling defect and one unproven Scratch presentation gate:
- `HASH_GATE=FAIL` was a stale analyzer constant. Installed runtime hashes exactly matched the v0.2.03b package manifest (`main=f9771872...`, `manifest=d0597f...`, `data=e49dbf2c...`).
- `SCRATCH_CONTACT_HOLD=0`: the v0.2.03b hold condition required `motionElapsed >= total`, but Thor trace showed HANDOFF at battleFrame 943 and authoritative HIT at 976 while that exhaustion condition never became true.

Healthy v0.2.03b evidence retained:
- Tackle safe body bind: 2; bad lunge body bind: 0.
- Bubble/Bubblebeam projectile wrong: 0.
- Bubblebeam WATER BG proof: 1.
- Action Binding/HIT Authority duplicate/re-arm/release-delta hard gates: all 0.

## v0.2.03c change
Only Scratch body-pose synchronization changes semantically:
1. After native HANDOFF, while Scratch is still awaiting authoritative `applyHitFx`, the PMD body returns the exact source hit frame every real draw.
2. HIT_FRAME remains engine-owned; no synthetic HIT, timer, audio, damage, barrier, queue, or native animation lifetime is added.
3. At true HIT, HIT Authority therefore re-delivers the same pose instead of visibly starting a second attacker beat.
4. Existing contact recovery remains after HIT.

Tooling fix:
- Collector hash gate now checks the actual v0.2.03c runtime SHA values and can no longer fail on the stale pre-repack main hash.

## Runtime hashes
- main.lua `da480a595fba950ad54a0cec0c96b5d2958382962e3c1c93ba3556ee682b7b29`
- manifest.json `7515cce9787d9dd9e9854d494c1200298a22fcb9f0397e5ec5cb29d51dc86e77`
- gbc_anim_data.lua `9ba4a8f12665cad62940202927892a306c1b86f90675da582bfaae4db2a8a206`

Formal Authority remains exact v0.2.02a. TEST-only B fixture must be removed before promotion.
