# SoulGold M1.4 Formal Pass Authority
Date: 2026-08-30

Status: **FORMAL PASS / SEALED**

Accepted evidence:
`SOULGOLD_M1_4_CORE_CLOCK_SYNC_EVIDENCE_20260830_175304.zip`

Evidence SHA-256:
`b53bd386e5a3b43c520a6dce7ca56cd4dac38fa3cdf8fb275050c39aa57f42e0`

User acceptance:
- gameplay speed normal
- map movement normal
- NPC dialogue/text timing normal
- event timing normal
- battle timing normal
- BGM normal
- SFX synchronization normal

Machine acceptance:
- target FPS 59.727500
- observed FPS 59.702600
- FPS error 0.024900
- source audio 65536 Hz
- audio queue max 137.417 ms
- audio queue final 78.562 ms
- queue drift -0.8008 ms/sec
- battle state lines 31
- move state lines 20
- M1_4_MACHINE_GATE=PASS

Sealed StateBridge:
- gBattleTypeFlags = 0x0200271C
- gBattlersCount = 0x02002720
- gBattleStruct = 0x02002724
- gBattleControllerExecFlags = 0x02002994
- gCurrentMove = 0x02002AB4
- gChosenMove = 0x02002B2E
- gBattleMons base = 0x02002B34

Accepted species observation:
- 1289 = Sprigatito
- 183 = Marill

Permanent architecture:
- mGBA = GBA hardware correctness authority
- Gen1 enhancement layer = SoulGold state / external PMD & Showdown sprites / zh-Hant-TW / host UI
- gbarecomp = optional experimental acceleration only

Next milestone:
M2 — one-species PMD Animated Battle Overlay Proof, first target Sprigatito / species 1289.
