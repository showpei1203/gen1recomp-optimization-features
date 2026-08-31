# Pokémon Anil zh-TW 實戰心得與回歸案例 2026-08-31

## 已證明的根因
- UI 背景消失：MT 翻到 Graphics resource path。
- Trainer Memo 背景消失：內部 suffix `memo` 被翻成 `備忘`，實際路徑變成 `bg_備忘`。
- 繁中長對話切掉：Essentials formatter 依英文空格斷行，CJK 沒有可用 break point。
- `Pallet Town` 漏翻：畫面來源為 exact v1.0.23 `MapInfos.rxdata`，不是單純 message DAT。
- `Smell ya / Smell you later`：英語慣用語不可逐字機翻，需 phrase regression lexicon。
- Berry/Poffin 說明 `為佛德童子`：MT 對固定遊戲描述模板產生系統性幻譯，應以官方 zh-Hant corpus/固定模板覆蓋。

## 已固定的 regression phrases
- Smell ya! → 先走啦！/回頭見！依情境
- Smell you later, {player}! → 回頭見，{player}！
- Giovanni → 坂木
- Team Rocket → 火箭隊
- Poké Ball → 精靈球
- Berry status recovery → 優先採官方「讓寶可夢攜帶後，可以治癒…」模板

## 流程教訓
- 「有翻譯」和「可遊玩繁中化」是兩件事。
- 玩家可見文字、UI label、machine key、resource path 必須在翻譯前分流。
- 任何實機新 bug 都應加入 reusable lint，而不是只修 Anil 單一 entry。

## v0.7.5 / Map 41–54 新增教訓
1. **同一個錯誤 MT 值不代表同一個原句。** 小剛道館兩句不同台詞曾被機翻成完全相同的中文。若用 value-based replace，會把其中一句錯修成另一句。DAT 必須以 section/map/key 精確定位。
2. **source 與 English edition translation 可能不同。** 玩家實際使用的 English edition `translation` 欄是主要語意與控制碼 authority；西文 source 只用來補充上下文。不可把兩個版本的 HTML tag 混在一起。
3. **專名音譯漏網要資料化。** Cubone/Graveler/Sudowoodo/Clefairy/Spearow/Farfetch'd/Pidgeot 等錯音譯已加入 known-bad pattern table。
4. **固定遊戲功能詞不可逐字機翻。** Technical Machine、Move Reminder、Trainer、Rock-type 應先套詞庫，再處理句子。
5. **寄放屋、交換、道館提示適合建立固定句型模板。** 這些流程跨地圖重複，人工校訂後應復用一致中文。

## v0.7.5 執行結果
- Map 41–54：186 條 EVENT_TEXT 全部重新檢閱。
- 152 條 EVENT_TEXT 實際改寫。
- 額外跨 section 官方詞彙/音譯修復 20 條。
- `full_mt_argos_s2twp` 狀態降至 9,900 條。
- data-driven quality lint HARD issue = 0。
- Marshal structure issue = 0。
