# PMD Action Binding I-B v0.1.99b Sustained Commitment

Status: **TEST-only behavioral correction**

Source: v0.1.99a Action Binding trace baseline.
Formal baseline remains `pmd_idle_battle_sprites v0.1.98b` HIT_FRAME Authority I.

## Problem proven by Thor

Two THUNDERSHOCK rows proved that PMD source motion can end before the native animation reaches DONE and before audio-tail ownership can start:

- run A: PMD COMPLETE 1318, ANIM_RELEASE/HIT 1361, early by 43f
- run B: PMD COMPLETE 385, ANIM_RELEASE/HIT 456, early by 71f

## Minimal correction

Only families marked by `Volatile.actionBindSustainedFamilies` are changed.

When the PMD source motion has exhausted after native handoff, but `battle.animPlaying` is still true, keep the same semantic source hitFrame instead of clearing the cue. Once AnimPlayer reaches DONE, the already-sealed `nativeAudioTailHold` continues ownership unchanged. After ANIM_RELEASE, the cue may complete normally.

No new timer is introduced.

Unchanged: move selection, handoff timing, HIT_FRAME authority, damage/status resolution, SFX playback, audio-tail duration, projectile free-running, contact recovery, multi-hit barrier safety, status-self policy, DRAMATIC_SHAPE, THOR Battle UI, Depth/Occlusion, Large Pokémon bounds, and species scale.

Static validation: **30/30 PASS**. Lua 5.4 parser load PASS. `main.lua` diff from v0.1.99a: 30 additions, 0 deletions.

Drive Test Folder: `1OaRiEUFa4YWd3pcwr7UFidJ1foArqNMU`
Drive ZIP: `1BGr-gme_9DPG2z_aWAJ7plzn-HTCSyMR`

Candidate hashes:
- PMD main: `b2f8f143f7298d5b0744c30bc885df5cca1eb109a073c515bbcc6eeedb4eed64`
- manifest: `c9351afd39ce30ca25428dcd359b8687bd7f6f92d2f44bf5ca3b92fa74d45aa4`
- test ZIP: `8c32d53f3dff270a309fca6b66c994240b4de92ff6ddfb428577e67f4c7a1233`

Primary Thor gate: THUNDERSHOCK must emit `ACTION_BIND SUSTAIN_HOLD`, and each sustainedCandidate audio-tail row must finish with `COMPLETE >= ANIM_RELEASE`, while all sealed HIT_FRAME gates remain healthy.
