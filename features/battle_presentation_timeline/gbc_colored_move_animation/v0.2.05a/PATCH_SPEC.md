# GBC Catalog Expansion A4 — CUT Family Batch I v0.2.05a

Base: exact v0.2.04a Formal Authority.

New moves: CUT, SLASH, VICEGRIP, GUILLOTINE.

All four reuse the exact frozen `cut_gray.png` derived from pret/pokecrystal `gfx/battle_anims/cut.png`; no new PNG assets. One generic `cut_pattern` renderer consumes data-defined Crystal object patterns. Short cut uses accepted 4B→4C→4D→4E. Long cut adds exact 4B→4C→4D→4F→50→51→52 frameset/OAM.

The accepted Scratch HANDOFF→HIT same-pose hold is generalized only to this CUT-family batch to prevent a Swing HOME→second-hit-body beat. HIT_FRAME remains engine-owned by applyHitFx.

TEST-only fixture: one free-overworld B press, battle-local clone, four moves, deterministic Rattata, no save mutation; second B logs ONCE_GUARD. Formal promotion must remove the entire fixture block.