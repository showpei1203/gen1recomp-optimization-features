# SoulGold M6X1R3 Native Stat Fidelity Authority

M6X1R3 supersedes the historical M2/M6X1R2 strip/tint stat-effect approximation. The R2 AYN THOR runtime proved external stat presentation was active, so R3 changes visual fidelity only; registry/audio and R2 presentation lifecycle remain sealed.

Canonical build: GitHub Actions Run #13 / 33867021188. Native stat asset generation, R3 validator, SoulGold ROM, exact 32 MiB gate, SGXP, patched mGBA ARM64, Android contract audit, APK and artifact uploads all PASS. The final compact persistence housekeeping failure occurred after artifact upload and does not invalidate the binaries.

R3 source authority is pinned SoulGold `graphics/battle_anims/stat_change`. Build output embeds 16 256x256 patterns derived from native tiles, increase/decrease tilemaps and eight native palettes. Runtime uses BitmapShader + ROM statScroll/statBlend and masks the native stat pattern with current Showdown alpha via DST_IN.

Permanent negative rules: no stripe/clipRect approximation, no hardcoded tint stat fake, no provider-owned native 64x64 stat pixels, no Android wall-clock provider timing, no BOUNCE_MON coupling, no raw healthbox ABI writes.

Binary authority:
- ROM: 9030606040c40e81dff820489dcd9cd57ea4619e7c1a3b5bfeb7e702c9018c0e
- SGXP: 0915766512c3c704c640b95242a5fe184219a12808981e86d6729e99309724bc
- APK: 3452c642ba2dbeb138b5ac1b5f55876e55fe25985642c8f17988fe27799a77c1
- bridge: 0x02002ad4

Runtime acceptance remains pending on AYN THOR, Sprigatito player BACK only. FRONT and 901-species expansion remain blocked.
