# SBFX Probe II — Direct Screen Primitives

Date: 2026-08-22
Status: TEST-only / diagnostic

Probe I disabled only `StadiumScreenFx.present(game, viewport)` and the user visually confirmed the square/translucent battle mask still remained. Therefore the render.hud post-compose replay path is cleared as the root cause.

Next diagnostic target is the direct screen-space primitive path used while StadiumFxPlayer custom rendering is active. Probe II restores the known Probe-I `present()` bypass marker if installed, then injects TEST-only early returns into `StadiumScreenFx.region`, `StadiumScreenFx.tile`, and `StadiumScreenFx.drawMove`. Anchored/custom move rendering remains enabled; Surf full-screen fidelity is intentionally not a gate for this probe.

Interpretation:
- mask gone + anchored Stadium VFX still present => root cause is inside SBFX direct screen-space primitives; narrow to region/fill vs tile/program.
- mask still present => clear StadiumScreenFx screen-wide primitive composition; next isolate StadiumFxPlayer adapter / wide-compat animation surface.

Do not modify PMD HIT_FRAME, Action Binding, damage/status ownership, Dramatic Shape, THOR UI, or Formal Authority.

Probe package SHA-256: `b8da1d9d61c3e6598fa9c1f7481667786df3e72dcf866d9d28a85ae125bff74c`.
