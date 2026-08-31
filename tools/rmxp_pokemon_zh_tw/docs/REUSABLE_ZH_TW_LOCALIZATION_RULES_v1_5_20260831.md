# RMXP / Pokémon Essentials 繁體中文化可重用規則 v1.5

## 核心原則
繁中化不是把所有 String 丟給翻譯器。先分類、保護機器字串與控制碼，再翻玩家可見內容，最後以靜態 QA + 實機截圖驗證。

## 已封版的安全規則
1. 劇情/NPC/說明可翻；UI 短詞只走受控詞庫。
2. `Graphics/`、`Audio/`、`Data/`、`Plugins/` 路徑、UI suffix/key 永不翻譯。
3. `\v[]`、`\PN`、`\c[]`、`%s`、`{1}`、`{1:03d}`、`#{...}`、HTML tags 先保護再翻。
4. Pokémon、人物、地名、招式、特性、道具名先套官方台灣詞庫，禁止 MT 自由音譯。
5. CJK 換行在原文字 formatter 處理，不逐句人工塞換行，也不使用全域 Bitmap hook。
6. Map 名稱需查 exact-version `MapInfos.rxdata`，不能假設所有文字都在 messages DAT。
7. target English edition 的 `translation` 是主要語意與控制碼 authority；source 只補上下文。
8. DAT patch 必須以 section/map/key 精確定位，不可用舊中文 value 做全域 replace。
9. 實機錯誤必須轉成 regression rule/lint，而不是只修單一 entry。

## v1.5：Exact-English phrase template 規則
重複功能/事件台詞可批次人工校訂，但只能以「完全相同的 English-edition `translation`」作為 template key。

允許：`exact English phrase -> vetted zh-TW phrase`

禁止：`bad old zh-TW phrase -> new zh-TW phrase` 全域替換。

原因：不同英文原句可能被 MT 壓成相同的爛中文；反過來，完全相同的英文功能台詞跨多張 Map 重複時，正適合以人工模板統一。

Anil v0.8.4 實例：
- Professor Samson 傳說寶可夢任務 8 個英文模板，跨 222 rows 統一。
- 攝影師 Seymour 12 個功能台詞模板，跨 179 rows 統一。
- Poké Ball 功能/道具說明 9 rows 統一台灣用語。

## v1.5：新增 recurring hard-fail
- `加百列教授` -> `成也・大木博士`
- `西摩語Name` -> `西摩`
- `Poké球` -> `精靈球`
- `月球石` -> `月之石`
- `大聲喊一聲`（Give me a shout）-> 自然語句
- `這是在房子`（It's on the house）-> `免費招待`
- `\GWould` / `\GSplendid` -> 保留控制碼但禁止英文殘留

## Mandatory HANDOVER rule
從 2026-08-31 起，每一個有實質修改的開發回合與 INTERNAL checkpoint 都必須準備 handover。每個 ZIP 必含 `handoff/CURRENT_HANDOVER.md`，並在可用時同步 GitHub + Drive。詳見 `PROJECT_HANDOVER_POLICY_v1_20260831.md`。

## 每版硬 QA
- placeholder/control token sequence = 0 mismatch
- Ruby interpolation/format spec = 0 mismatch
- HTML tag sequence = 0 mismatch
- resource path translated = 0
- protected suffix/key translated = 0
- known bad pattern HARD = 0
- manifest -> DAT keyed verify = 0 mismatch
- Marshal section/type/key structure = unchanged
- Scripts count/targeted diff
- ZIP integrity
- JoiPlay/AYN THOR：Battle HUD、Move menu、Summary、地名、長對話換行實機 regression
