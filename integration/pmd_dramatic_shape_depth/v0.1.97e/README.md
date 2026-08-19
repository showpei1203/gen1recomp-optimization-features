# PMD v0.1.97e × DRAMATIC_SHAPE 1.8.2 × THOR Battle UI 0.3.41 — Depth Integration IV

Status: **TEST-ONLY / STATIC PASS / ROOT-CAUSE FIX+VERIFY / WAITING THOR VISUAL + RUNTIME ACCEPTANCE**

## Root causes confirmed by Thor evidence

Diagnostic evidence: `GEN1RECOMP_PMD_DEPTH_ROOT_DIAG_20260819_214955.zip`.

### 1. Missing player PMD body

The diagnostic call stack repeatedly resolves to:

- `DRAMATIC_SHAPE/lib/OverworldBattle.lua:1119` (`originalSideTexture`)
- called by `thor_battle_ui/main.lua:772`
- then back into `DRAMATIC_SHAPE/lib/OverworldBattle.lua:1338`

Exact `thor_battle_ui 0.3.41` source contains:

```lua
O.sideTexture = function(battle, side)
  local tex = originalSideTexture(battle, side)
```

This wrapper drops the third `opts` argument. Integration III requests the player shadow with `{ pmdOnly=true, shadowOnly=true }`; after the THOR wrapper that becomes a normal visible `sideTexture(battle, "player")` call. Evidence then shows `playerCanDraw=true`, `depthPlayer=true`, `overlayWillDraw=false`, proving the PMD asset is healthy but the legacy visible overlay is suppressed by incorrect visible-3D ownership.

**Fix:** THOR wrapper now accepts and forwards `opts` unchanged.

### 2. Enemy feet clipped by terrain

Route 2 diagnostic proves:

- `playerGround=0`
- `enemyGround=0`
- `chosenGroundY=0`
- `enemyMinusPlayer=0`

So terrain-height mismatch is eliminated.

PMD reports enemy `actualAnchor=(80,106)`, but Integration I–III declared `local bridgeAnchor=nil` inside the `pcall(function() ... end)` closure. The return path that assigns `tex.ax/tex.ay` is outside that closure, so it never sees the local variable and falls back to stock `TEX_AY=96`.

Result: 10 texture pixels are grounded below the world floor. With `BattleBillboard.FULL_W/FULL_PIC = 16/56`, that is about `2.8571` world units below ground, which the working terrain depth buffer correctly clips.

**Fix:** `bridgeAnchor` is now declared in `sideTexture` outer scope and assigned inside the closure, allowing the real PMD baseline to propagate to BattleScene.

## Candidate scope

Only three runtime files are changed:

- `pmd_idle_battle_sprites/main.lua`: retains the v0.1.97d proof logs for one acceptance run and updates the candidate marker/version.
- `DRAMATIC_SHAPE/lib/OverworldBattle.lua`: fixes `bridgeAnchor` lexical scope and logs the applied anchor once per side.
- `thor_battle_ui/main.lua`: forwards `sideTexture(..., opts)`.

Unchanged:

- DRAMATIC_SHAPE `BattleScene.lua`
- DRAMATIC_SHAPE `BattleBillboard.lua`
- `Voxel3D.lua`
- Presentation Timeline IIc
- audio-tail
- HIT timing
- damage / accuracy
- THOR Battle UI manifest `0.3.41`

## Source gates

- PMD v0.1.97d main: `fb62d1b24300791811b62dc9469b78f4a7ae30bc833adc69881845da73945627`
- DRAMATIC_SHAPE v0.1.97d OverworldBattle: `b539d343b89615179101e32b57be582f20b4b78822b2e9f32d85a6efd12dff40`
- DRAMATIC_SHAPE BattleScene: `62daab3a679551ecd8871e464df6fddaf207070892d8f06dd528f98f5b2d91fb`
- THOR Battle UI 0.3.41 main: `50ca1356f5110d676ecda4179b899a4abd2267b0226203ece1540a81b9c99a43`
- THOR Battle UI manifest: `22d4ccf00b77f5b389473b9b1c66dac2182816fd1d1af643cd3f32c8de8229a6`

## Candidate hashes

- Package ZIP: `09e74da970f41f48429d6bcba9013b41d86650d54904dfdec28c1cb0ef13f99e`
- PMD main: `44d005f262b58aadaf898aa5cba198c570aaf684ef5a6d621134417081743e5f`
- PMD manifest: `a6c150da7ea094c11ca7304780d219dab993d0320fa700d8a13e5fc3512cc975`
- DRAMATIC_SHAPE OverworldBattle: `43dc0b6da793e1ce43d80efddfdf8afa72d2a51f35a3fda06bc36c13edda7104`
- THOR Battle UI main: `8a1d1fb26b56c736fed42ef7c27f95cdc3e3a349ae989417f4e9ee2579686835`
- BattleScene unchanged: `62daab3a679551ecd8871e464df6fddaf207070892d8f06dd528f98f5b2d91fb`

## Drive authority

- Root-cause Evidence folder: `1AJYFZ7Je7Kn3ZfV4Bx9nj3zGS0UHkiTh`
- Evidence ZIP: `1WXlwWsrTwn82rCZ5PC5NdDTRO6m9b5O2`
- Root Cause report: `1lBMVdGhlTV1E9QLbc9dqQS4XwW0pTamd`
- Exact THOR Battle UI source folder: `1NdD03leouMCBH-uJDat2YbIU-Lf88J6b`
- Candidate folder: `1Qp5bEA7WbV1yfCU66OLAk8p63BERZyR2`
- Candidate ZIP: `1hRHEle3iZroZJ3zR3z-aH1H6ItZGOR8d`
- Static Validation: `1SCvhoZ07RWl33mGefdscL89iHk3uinUM`

No promotion to baseline is allowed before Thor visual/runtime acceptance.
