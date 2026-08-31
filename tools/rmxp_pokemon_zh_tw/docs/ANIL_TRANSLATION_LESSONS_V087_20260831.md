# Pokémon Anil zh-TW 實戰心得 — v0.8.7 / Map 81–85 + QA v1.7

## 本 checkpoint 完成
- 承接 v0.8.6 Map 81：35/35 EVENT_TEXT 人工 review，31 條實際改寫，另有 6 條 exact-English propagation。
- Map 82–85：65/65 EVENT_TEXT 人工 review，58 條實際改寫。
- 格式/語言/專名全庫 cleanup：49 條實際修改。
- v1.7 source-aware lint 首次又抓出 4 條 Rocket Grunt / Hall of Fame 漏網，全部修正。
- 新增 opaque single-letter contract 後再抓出 16 條舊 Script Text 污染，全部修正。
- 相較 v0.8.6 DAT：127 values changed。
- 相較 v0.8.5 DAT：164 values changed。
- 原始 Argos MT status 降至 9,186。

## 重要新案例
1. `scot-free` → `走開的Scot`：英語慣用語被拆字，必須人工依語意翻成「全身而退」。
2. `Rocket Grunts` → `火箭榴彈`：專名與一般名詞混合後 MT 會產生完全錯誤詞義。官方語彙使用「火箭隊手下」。
3. `Control.` → `控制層`：極短高語意台詞不能靠機翻字面判斷，坂木情境應為「掌控一切」。
4. `(法語)` 污染分散在 EVENT_TEXTS 與 SCRIPT_TEXTS，證明語言標籤污染需全庫 HARD lint。
5. `頁:1` 是系統性 machine-shaped corruption。38 個命中裡大量是時間、數量、UI 計數器、單字母 label，不能當正常中文。
6. 新增「單一 ASCII 大寫字母保持原值」後，又抓出 C/D/E/F/G/K/L/M/N/O/Q/R/T/U/V/W 共 16 條錯譯。
7. source-aware contract 不能只比固定連續中文。`Elite Rocket Grunt` 合法翻作「火箭隊精英手下」，lint 應檢查概念成分而非只接受「火箭隊手下」完全連續字串。
8. `Silph Scope` 使用台灣官方「西爾佛檢視鏡」。
9. `Super Secret Key` 是 Anil 自訂功能名稱，本專案統一為「超級秘密鑰匙」，並由 source-aware contract 管控。

## Map 82–85 主要內容
- 火箭隊地下基地各樓層與電梯
- 超級秘密鑰匙 / 西爾佛檢視鏡提示
- 坂木第一次正式長篇對話
- 卡拉卡拉母親 / 寶可夢塔事件銜接
- 阿波羅帳目與火箭隊資本劇情

## QA 結果
- manifest: 21,438
- non-empty zh_tw: 21,437
- v1.7 lint: HARD 0 / WARN 0
- manifest → DAT: 21,437 checked / 0 mismatch
- Marshal structure vs v0.8.6: changed 127 / issues 0
- total DAT delta vs v0.8.5: 164
- next exact human-review start: Map 86
