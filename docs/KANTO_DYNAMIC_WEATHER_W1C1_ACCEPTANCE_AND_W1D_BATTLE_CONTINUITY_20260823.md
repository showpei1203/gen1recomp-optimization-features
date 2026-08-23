# Kanto Dynamic Weather Integration — W1c1 Acceptance / W1d Battle Continuity

Date: 2026-08-23

## W1c1 accepted state

W1c1 repaired the Weather / Dramatic Shape split-renderer identity issue by compiling the Weather-aware `Sky`, `Voxel3D`, and `VoxelScene` code into the already-existing Dramatic Shape shared table identities rather than creating duplicate renderer tables.

User visual acceptance reported all targeted regressions normal:
- 3D tree trunks restored
- overworld Weather still visible
- First Person actually enters first-person
- player card hidden in First Person
- direction gauge normal

Returned evidence:
- ZIP SHA-256: `20aeb64550d24660047851caea8d88fe218448a0391b7f34d0fdb4d8628f72ae`
- `RESULT=STRUCTURAL_PASS`
- `W1C_BRIDGE_READY_ROWS=1`
- `SHARED_IDENTITY_TRUE_ROWS=1`
- `WEATHER_MAIN_READY_ROWS=1`
- `ERROR_ROWS=0`
- `EXACT_HASHES=True`
- `BATTLE_SOURCE_CAPTURED=True`

Accepted W1c bridge SHA-256:
`31b9592da88d54d246b0b156f7a0667834556ae4cb8285bd504d8a6f8f9d3920`

## Exact Thor battle source authority captured by W1c evidence

- `BattleScene.lua`: `4c05b8788e3cd64ea64e6905c2ba623e1d69722a44387c8f193b2ad76992f3c0`
- `OverworldBattle.lua`: `1714ac5d5d98f2f785a8a63f2cc741865595e41eafada8d9dd7c4619f23ca501`
- `BattleCam.lua`: `673f1169e2b483ca0db9e84cc1e508c569854815e39fdc9a1abae3615db4c3e5`
- `BattleArena.lua`: `a9a044e882d7f91575a701fbb19aa346b0cc0aaeccce3b22e9c189269f185041`

## W1d candidate goal

Project requirement: an outdoor overworld weather state must visually continue into Dramatic Shape's staged outdoor battle scene.

Weather ownership remains environment-only. W1d must not become a flat HUD overlay and must not steal move presentation ownership from PMD / StadiumBattleFX.

W1d intended battle environment contributions:
- weather-aware outdoor sky and lightning tint
- cinematic fog at reduced battle density
- moving cloud-shadow shader state
- depth-tested clouds / mist / ambient particles
- depth-tested rain

Intentionally excluded from battle:
- puddle/reflection pass
- sprite reflections
- god rays crossing combatants

Existing sealed rules remain unchanged:
- PMD player visible body remains legacy 2D overlay
- PMD enemy visible body remains depth-tested 3D card
- visible Pokemon body fog/local-shadow parity remains unchanged
- StadiumBattleFX remains VFX owner
- `BattleState.applyHitFx` remains HIT_FRAME authority

## W1d implementation architecture

Dramatic Shape files are never written on disk.

The Weather bridge is extended to transform and compile exact Thor `BattleScene.lua` into the existing shared `BattleScene` table identity. Weather-owned `CinematicAtmos.lua` gains a battle-only draw path that reuses the existing world-space atmosphere primitives while skipping puddle/reflection and god-ray passes.

W1d bridge candidate SHA-256:
`f89867e98900736776402d4100f62b1961471d43dfe170874df59f1686743ee3`

W1d test ZIP SHA-256:
`5110cb964bd05fb1f9144ed7b73b99683f3ec820fd5c2ce3c8c1adf49abacdc7`

Status: `STATIC_SCOPE_PASS / THOR_RUNTIME_PENDING`.
