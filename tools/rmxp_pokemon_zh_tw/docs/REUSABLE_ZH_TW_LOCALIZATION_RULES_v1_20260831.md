# RMXP / Pokémon Essentials 繁體中文化可重用規則 v1.7

## 核心原則
繁中化必須先分類字串，再翻譯玩家可見內容。任何機器路徑、內部 key、控制碼、品牌識別、opaque label、格式短碼先保護。英文版 `translation` 是語意與控制碼 authority，實機截圖仍是最終驗證來源。

## 已封版規則
1. `Graphics/`、`Audio/`、`Data/`、`Plugins/` 路徑永不翻譯。
2. Modular UI suffix/key，例如 `memo/info/moves/skills/ribbons/forms/area/data/egg/allstats` 永不翻譯。
3. `\v[]`、`\PN`、`\c[]`、`%s`、`{1}`、`{1:03d}`、`#{...}`、HTML tags 必須保護，翻譯後 token 序列一致。
4. Pokémon、角色、地名、招式、特性、道具名先套台灣官方用語，不允許 MT 自由音譯。
5. CJK 換行在 formatter 層處理，不逐句硬塞換行，不使用全域 `Bitmap#draw_text` hook。
6. Map 標題需檢查 exact-version `MapInfos.rxdata`。
7. DAT patch 只允許 section/map/key 精確定位，不允許舊中文 value-based global replace。
8. English edition `translation` 欄為主要語意與控制碼 authority；source 僅補上下文。
9. 每一個公開版或 INTERNAL checkpoint 都必須刷新 HANDOVER、QA evidence、Drive artifact 與 GitHub authority。

## v1.7 新增：短字串 / machine-shaped output 必須預設不可信
Argos 在 Script Texts 把大量單一字母與格式短碼翻成 `頁:1`、`C級`、`一般事務人員`、`英`、`無` 等完全錯誤值。

新規則：
- English edition 若正好是單一 ASCII 大寫字母 `A-Z`，且尚未確認為玩家可翻譯字義，target 必須保持原值。
- `P0/P1/P2/P3` 維持原值。
- `頁:1` 類 machine-shaped fragment 一律 HARD FAIL，不可視為「已經是中文」。
- `x{1}`、時間單位、計數器、戰鬥模擬 UI 等短字串需人工確認格式，再決定是否局部中文化。

這一輪僅靠新增 single-letter contract 又抓出 16 條舊污染，證明短字串不應交給自由 MT。

## v1.7 新增：Script Texts 與 EVENT_TEXTS 必須同等 QA
`頁:1` 38 個命中中，絕大多數藏在 `SCRIPT_TEXTS`，包括：
- 時間/分鐘/秒格式
- `x{1}` 數量顯示
- 隊伍生成/對戰模擬進度
- Opponent/You/Ally 統計
- 砍樹提示
- Monotype Challenge 說明
- 單字母 UI label

因此「劇情地圖人工潤稿完成」不代表系統 UI 已安全。每個 checkpoint 都必須全 21,438 條跨 section lint。

## v1.7 新增：source-aware Pokémon terminology contracts
- `Silph Scope` → `西爾佛檢視鏡`
- `Rocket Grunt(s)` → `火箭隊手下`；允許 `火箭隊精英手下` 等修飾語，lint 不得錯誤要求完全連續字串。
- `Super Secret Key` → 專案受控名稱 `超級秘密鑰匙`
- `Hall of Fame` → `名人堂`
- 既有 `critical hit` → 要害、`Coin Case` → 代幣盒、`Abilities Expert` → 特性專家、`Mega Stone` → 超級石等契約繼續保留。

## v1.7 新增：語言標籤污染
任何與 English authority 無關的 `(法語)`、`(韓語)`、`(簡體中文)` 類標籤都是 HARD FAIL。這類字樣曾出現在阿波羅台詞、名人堂 UI 與純格式字串中。

## v1.7 新增：exact-English template 的使用方式
只有 English edition 原句完全一致時才能跨 Map 傳播人工模板。
- 同句可安全傳播，例如電梯樓層詢問、Super Secret Key 提示。
- 角色修飾詞不同時需 source-aware 合約而不是死字串，例如 `Rocket Grunt` 與 `Elite Rocket Grunt`。
- 任何模板寫入後仍要跑 token sequence、source-aware contract、Marshal structure compare。

## 每 checkpoint 封版條件
- known-bad HARD = 0
- source-aware HARD = 0
- source-aware WARN = 0，或每筆具人工 justification
- placeholder / Ruby interpolation / HTML / control token mismatch = 0
- resource path translated = 0
- protected suffix/key translated = 0
- opaque single-letter changed = 0
- manifest → DAT = 0 mismatch
- Marshal section/type/key structure = unchanged
- ZIP integrity PASS
- 公開候選版另需 AYN THOR + JoiPlay 實機 regression
