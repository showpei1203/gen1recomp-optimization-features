# RMXP / Pokémon Essentials 繁體中文化可重用規則 v1.6

## 核心原則
繁中化必須先分類字串，再翻譯玩家可見內容。任何機器路徑、內部 key、控制碼、品牌識別或 UI opaque label 都先保護。靜態 QA 只是一道門，實機畫面仍是最高優先級的驗證輸入。

## 既有封版規則
1. `Graphics/`、`Audio/`、`Data/`、`Plugins/` 資源路徑永不翻譯。
2. Modular UI suffix/key，例如 `memo/info/moves/skills/ribbons/forms/area/data/egg/allstats` 永不翻譯。
3. `\v[]`、`\PN`、`\c[]`、`%s`、`{1}`、`{1:03d}`、`#{...}`、HTML tags 必須先保護，翻譯後序列一致。
4. Pokémon、人物、地名、招式、特性、道具名先套台灣官方用語，不允許 MT 自由音譯。
5. CJK 換行在 formatter 層處理，不逐句手塞換行，也不使用全域 `Bitmap#draw_text` hook。
6. Map 標題需檢查 exact-version `MapInfos.rxdata`。
7. DAT patch 必須以 section/map/key 精確定位；禁止拿舊中文值做全域 replace。
8. English edition `translation` 欄是主要語意與控制碼 authority；source 只補上下文。

## v1.6：source-aware terminology contract
只靠「壞中文黑名單」抓不到所有錯誤。當英文 authority 已明確包含某個 Pokémon 專用概念時，繁中必須滿足對應契約。

目前自動檢查：
- English 含 `critical hit` → zh-TW 必須使用「要害」語彙。
- English 含 `Pokévial` / `Poké Vial` → 繁中保留自訂品牌 `Pokévial`。
- English 含 `Coin Case` → 使用「代幣盒」。
- English 含 `Abilities Expert` → 使用「特性專家」。
- `<b>TRAINER TIP:</b>` → `<b>訓練家提示：</b>`。
- English 正好為 `P0/P1/P2/P3` → target 必須完全相同，不得把 opaque UI label 機翻。

`Mega Stone` → `超級石` 與 `寶可夢號` 類 suffix 污染也由 source-aware lint 掃描。v0.8.5 已清至 0。

## opaque label / custom brand
短字串不代表可自由翻譯。像 `P0/P1/P2/P3` 可能是 UI/樓層/狀態識別；未確認語意前必須保持 target-edition 原值。

自訂功能名稱也不能被 MT 音譯：
- `Pokévial` 保留 `Pokévial`
- `PokéRider` 保留 `PokéRider`
若未來決定正式中文命名，必須透過受控 glossary 一次改，不可讓 MT 自行產生「波克維亞／波克瑞德」。

## source-aware 批次清理
若 lint 能由 English source 精準判斷詞義，應採 source-aware 修正。例如 source 含 `Mega Stone` 時才把錯誤「巨石」修為「超級石」，不能全域替換所有「巨石」，否則會傷到真正的巨石、地形或物種分類。

## 人工 Map review
- 一個 batch 必須把指定 Map 的所有 EVENT_TEXT 都看過，不只挑 MT status。
- 已人工確認但文字不需改，也要在 handover 記錄 review coverage。
- 完成 Map review 後立刻跑全庫 lint，跨 section 清同類污染。

## HANDOVER 強制規則
每一次有實質修改的公開版或 INTERNAL checkpoint 都必須：
1. 產生/刷新 `handoff/CURRENT_HANDOVER.md`。
2. ZIP 內包含 handover、policy、必要 QA evidence。
3. artifact 同步 Drive，handover/規則同步 GitHub。
4. handover 明確寫出 baseline、完成內容、SEALED、不確定事項、下一個精確 Map/工作起點。
5. 新工作階段先讀 CURRENT_HANDOVER 再改檔。

## 每 checkpoint 封版條件
- known-bad HARD = 0
- source-aware HARD = 0
- placeholder / Ruby interpolation / HTML / control token mismatch = 0
- resource path translated = 0
- protected suffix/key translated = 0
- manifest → DAT = 0 mismatch
- Marshal section/type/key structure = unchanged
- ZIP integrity PASS
- 公開候選版另需 AYN THOR + JoiPlay 實機 regression
