# GBC-A1 Source Manifest

Primary technical reference: `pret/pokecrystal`.

Required source areas:
- `gfx/battle_anims/`
- `gfx/battle_anims/battle_anims.pal`
- `data/moves/animations.asm`
- battle animation command definitions/documentation

Confirmed available graphics include objects such as `fire.png`, `beam.png`, `bubble.png`, `hit.png`, `explosion.png`, `aeroblast.png` and related animation sheets.

`data/moves/animations.asm` contains move animation entries covering the Gen1 and Gen2 catalog, including Ember, Thundershock, Thunder Wave, Quick Attack, Fury Swipes, Ice Beam, Psybeam, Surf and Earthquake.

Implementation policy:
1. Do not simply play captured GIF/video.
2. Translate Crystal animation behavior into an internal runtime representation: objects, coordinates, waits, palette effects, background effects and presentation events.
3. GBC VFX consumes existing battle-presentation events and never owns damage/HIT timing.
4. Prefer source manifests/import tooling and derived runtime representations over publishing a standalone archive of copyrighted Pokémon artwork.
