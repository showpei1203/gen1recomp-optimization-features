# GBC-A1 v0.2.00b — Asset Loader Fix TEST

Status: **TEST-only / Static PASS / Thor runtime pending**

Formal base remains `pmd_idle_battle_sprites v0.1.99b` Action Binding Authority I. The installer accepts either exact v0.2.00a or exact formal v0.1.99b as source, while DRAMATIC_SHAPE/THOR remain sealed.

## Why b exists

v0.2.00a Thor evidence proved the three GBC event chains were alive but no colored pixels appeared. All three PNGs were present byte-exact on Thor yet failed through `mod.assets.image(spec.file)`.

v0.2.00b changes only GBC asset loading and render-proof instrumentation:
1. normal `mod.assets.image` first;
2. binary `mod:read("assets/<file>")` fallback;
3. `love.filesystem.newFileData` + `love.graphics.newImage(FileData)`;
4. direct `mod.path/assets/...` final fallback;
5. `GBC_VFX IMAGE_LOADED` diagnostic with route and dimensions;
6. `GBC_VFX DRAW` only after at least one tile actually renders.

No Presentation Timeline, HIT_FRAME, Action Binding, damage/status, audio-tail, queue barrier, Depth/Occlusion, Large Pokémon bounds, species scale, DRAMATIC_SHAPE or THOR behavior is changed.

## Static validation

`54/54 PASS`, including Lua 5.4 parser load for `main.lua` and `gbc_anim_data.lua` and byte-exact comparisons of all sealed timing/action functions against v0.2.00a.

## Candidate hashes

- main.lua `0310e5d564b3dc94bf229a6ab2d7f04e93a8e89b3317aad75023b225dd149008`
- manifest.json `5808fb4d9703a4a671a2a7d9df0cff2f1df464c36d27d69ad77734e0f6849039`
- gbc_anim_data.lua `bed3ab707188ae817035d725ca01a61be84c54d88fb519e63501d27f5d1b82ef`
- fire_red.png `7b279edf5a907c278d18bccfe1f6661f3ead56b7264fde4bcfe57a0999798a93`
- lightning_yellow.png `78949d8afed6f5962be7425a593246e07ea7525ce043e35e758a4dcf9bb89d2f`
- explosion_gray.png `73bea1826f82eb9bcbe66cd2675195e55e6a922808b16b66cc3b115242a5a718`
- complete TEST ZIP `0d803b7f123fec5e320ecbedd5b1ca82a81f4a8613d136e07a3d3e29462117ed`

## Drive

- Test folder `1Jl4A8aO6KH3aHHOlVL4ZKUbYV6VCuz4z`
- Complete ZIP `18DIRo3pVdJXrHt4TNYlKfFMFi2GuGTln`
- Static validation `19OYbnfqDkhKdxw8CAot1bI9sX6kEMXtr`
- Package manifest `1sAchiiP33bXocpkeae5A54yceWP02e1x`
- a→b diff `1Xx5FIwoCou8-OxCbTjd3EDf7i_p8h8nl`

## Thor gate

Run Ember, Thundershock and Thunder Wave once each. Required proof:
- `GBC_VFX_ERRORS=0`
- fire/lightning/explosion `IMAGE_LOADED=True`
- real `GBC_VFX DRAW` for supported rows
- Thunder Wave no false damage HIT
- all sealed Action Binding/HIT gates remain healthy
- user confirms colored pixels are visibly present and positioned sensibly.
