# SOULGOLD M6X1R3 — Native SoulGold Stat Fidelity

Status: BUILD/STATIC PASS; AYN THOR runtime stat-fidelity gate pending.
Canonical CI: Run #13 / 33867021188.

R2 runtime proved the stat bridge itself was active (`stat_native_composite_frames=87`), but the old historical strip/tint approximation was still visually wrong. R3 permanently rejects that approximation.

R3 generates 16 native stat-change textures at build time from pinned SoulGold `graphics/battle_anims/stat_change`: indexed `tiles.png` (128x32, 64 tiles), native increase/decrease 32x32 tilemaps, and the eight native stat palettes. The generated 256x256 patterns are embedded in the APK.

Runtime rendering uses the ROM-provided stat state. BitmapShader reproduces the SoulGold BG pattern, ROM statScroll drives BG Y, decrease keeps native BG X=64, statBlend maps to blend/16, and the current Showdown frame alpha is applied with DST_IN as the silhouette mask.

Forbidden forever: stripe/clipRect stat approximation, hardcoded RGB stat tint, native 64x64 provider-owned stat silhouette, Android uptime provider clock, BOUNCE_MON coupling, transient bridge blank frames, and host raw healthbox ABI writes.

Binary authority:
- ROM SHA-256: 9030606040c40e81dff820489dcd9cd57ea4619e7c1a3b5bfeb7e702c9018c0e
- SGXP SHA-256: 0915766512c3c704c640b95242a5fe184219a12808981e86d6729e99309724bc
- APK SHA-256: 3452c642ba2dbeb138b5ac1b5f55876e55fe25985642c8f17988fe27799a77c1
- bridge: 0x02002ad4

Next device gate remains Sprigatito player BACK only. Trigger stat decrease 2–3 times. Expected: native SoulGold stat pattern scroll/blend continuously inside Showdown silhouette, with no stripe/block segmentation and no native 64x64 silhouette. FRONT and broad roster expansion remain blocked.
