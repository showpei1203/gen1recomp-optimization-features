# RMXP / Pokémon Essentials 繁體中文化可重用規則 v1

## 目的
這份規則把 Pokémon Anil DE 1.0.23 實機繁中化遇到的失敗模式固定成後續專案的預設安全規則。未來不是「記得小心」，而是先分類、先保護、再翻譯、最後用 QA 阻擋回歸。

## A. 文字必須先分類，不能看到字串就翻
1. **玩家可見內容**：劇情、NPC、道具/招式/特性說明，可翻譯。
2. **受控 UI 詞彙**：Fight/Bag/Summary/Run 等只走短詞詞庫，不交給自由機翻。
3. **機器內部字串**：檔名、Graphics/Data/Audio/Plugins 路徑、UI suffix、symbol/key、script id，永遠不得翻譯。
4. **格式與控制碼**：`\v[]`、`\PN`、`\c[]`、`%s`、`{1}`、`{1:03d}`、`#{pokemon.name}`、HTML tags 等先 token 化保護，翻完再還原。

## B. 官方詞彙優先
寶可夢、招式、特性、道具、地名、角色名先套官方台灣用語，再處理一般句子。不得讓 MT 自由翻：Pokémon、Poké Ball、Giovanni、Team Rocket、Pidgey 等。

## C. 不信任「100% 已翻譯」這個數字
`zh_tw` 非空只代表有字，不代表可用。已出現過：
- `Smell ya!` → `聞聞你!`
- `Smell you later` → `晚點聞聞...`
- Berry/Poffin 說明 → `為佛德童子`
- Giovanni → `喬瓦尼`
- Team Rocket → `小組火箭`
- Poké Ball → `撲克舞會`
- `Sp. Atk`/性格資料 → `(韓語)`、`軟體`
因此每版都要跑 known-bad-pattern lint。

## D. UI 與資源完整性
翻譯層不得改變任何圖片/音效/資料檔路徑。Anil 曾把 `Graphics/Translations/English/databox_normal` 翻成中文，直接造成 HP HUD、Move 選單、Summary 背景消失。所有 resource path 必須逐筆比對且檔案存在性檢查。

## E. 內部 suffix/key 必須原樣保留
Anil Modular UI 的 `memo` 被翻成 `備忘`，程式因此去找 `bg_備忘` 而不是 `bg_memo`。未來 `memo/info/moves/skills/ribbons/forms/area/data/egg/allstats` 這類 suffix/key 一律列入 protected terms。

## F. CJK 換行要在引擎 formatter 解決
英文靠空格找換行點，繁中沒有空格。不可人工替每句插換行，也不可用全域 `Bitmap#draw_text` hook。應在原 formatter 加入 CJK 字元邊界換行，並做長句、HTML tag、控制碼 regression test。

## G. Map 名稱要查真正資料來源
畫面上的 Pallet Town 即使 message DAT 已翻譯，仍可能來自 `Data/MapInfos.rxdata`。必須針對 exact game version 檢查 MapInfos、Scripts、PluginScripts、PBS/Data，不可假設所有文字都在 messages DAT。

## H. Exact-version baseline
修 UI/Script/MapInfos 時，優先取同一遊戲同一版本的原始檔做 authority。不同版本素材只能當診斷參考，不可直接視為正式修復基底。

## I. 機翻只當底稿
Marian/NLLB/M2M100 實測都會破壞 Pokémon 專名、截句或產生不自然中文。策略固定為：
`全量 MT 底稿 → 官方詞庫 → 系統錯譯規則 → 高曝光戰鬥/UI 人工校訂 → 劇情依地圖人工潤稿`。

## J. Checkpoint before QA
超過 10 分鐘的生成/翻譯工作必須先保存 artifact/checkpoint，再跑 QA。QA fail 不得讓完整翻譯成果一起消失。

## K. 每版必跑的硬 QA
- Placeholder/control token 逐序列一致
- Ruby interpolation / format spec 一致
- HTML tags 一致
- resource path 不得翻譯
- internal suffix/key 不得翻譯
- known bad patterns = 0
- Marshal section/type/key structure 不變
- Scripts count/targeted-diff 檢查
- ZIP integrity
- AYN THOR + JoiPlay 實機 regression：UI、Battle HUD、Move menu、Summary、長對話換行

## L. 實機截圖是正式 QA 輸入
玩家看到的錯誤優先級高於「靜態 QA 0 issues」。每一個實機錯誤都要轉成：
1. 根因；2. 可重用規則；3. 自動 lint/test；4. handoff 紀錄。
