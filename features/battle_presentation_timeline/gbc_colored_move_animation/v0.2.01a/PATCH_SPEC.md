# v0.2.01a GBC-A2 Patch Spec

## Base

Accepted source gates:

1. exact v0.2.00b GBC-A1 test base
   - main `0310e5d564b3dc94bf229a6ab2d7f04e93a8e89b3317aad75023b225dd149008`
   - manifest `5808fb4d9703a4a671a2a7d9df0cff2f1df464c36d27d69ad77734e0f6849039`
2. exact formal v0.1.99b
   - main `b2f8f143f7298d5b0744c30bc885df5cca1eb109a073c515bbcc6eeedb4eed64`
   - manifest `c9351afd39ce30ca25428dcd359b8687bd7f6f92d2f44bf5ca3b92fa74d45aa4`

Sealed DS/THOR hashes are hard-gated and unchanged.

## A2 presentation families

- **Quick Attack**: draws a gold Crystal-derived HIT object only after `rec.hitFrame` exists. No pre-HIT colored impact is legal.
- **Fury Swipes**: each actual Action Binding row owns one Crystal CUT-family slash; hit-row parity alternates slash direction.
- **Psybeam**: Crystal PSYCHIC wave objects travel from existing PMD attacker presentation anchor to target anchor; authoritative HIT opens a short target burst.
- **Surf**: Crystal WAVE-family objects span the classic 160px or wide 304px battle field.

Native move animations remain visible in this test lane.

## Late-HIT visual retention

Prior Quick Attack evidence showed PMD `COMPLETE` can precede authoritative engine HIT by about 26 battle frames. v0.2.01a therefore keeps a completed damaging VFX record alive for a bounded `pendingHitGrace` while HIT is absent. If HIT arrives after PMD COMPLETE, cleanup is re-anchored to `hitFrame` for the short impact/burst tail. This is presentation-record retention only. It does not delay native animation, sound, damage, queue progression, HIT_FRAME, or PMD body completion.

## One-shot B fixture

TEST-only behavior:

- Hook: `OverworldState.handleInput`.
- Gate: free-overworld input path, player not moving, B edge.
- First valid B: consumes fixture for this process and starts one wild benchmark battle through the normal overworld battle transition.
- Player: deep-copied first healthy party mon, battle-local only, moves replaced with `QUICK_ATTACK/FURY_SWIPES/PSYBEAM/SURF`, status cleared, full fixture HP, high speed.
- Enemy: RATTATA, 9999 HP, high defenses, low speed/attack, `GROWL` only.
- Battle RNG: local deterministic minimum result to stabilize hit/multi-hit evidence.
- Pokédex RATTATA `seen`: snapshotted/restored immediately after constructor and again at fixture end.
- Second valid B after return: logs `ONCE_GUARD`; no second fixture starts.

No persistent fixture writes are allowed.

## Promotion rule

Formal release must delete the entire fixture implementation and its B hook/logging. Runtime PASS of this TEST candidate does not waive that deletion gate.
