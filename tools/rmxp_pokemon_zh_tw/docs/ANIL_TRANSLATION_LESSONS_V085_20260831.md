# Pokémon Anil zh-TW 實戰心得 — v0.8.5 / Map 72–80

## 本 checkpoint 做了什麼
- Map 72–80：212 條 EVENT_TEXT 全數人工 review。
- Map batch 直接改寫 169 條。
- exact-English / regression cleanup 另外修改 89 條跨地圖重複字串。
- v1.6 source-aware HARD lint 初次抓出 40 條漏網，全部人工/定向修正。
- source-aware WARN 又抓出 105 條 `Mega Stone` 詞義錯置與 33 條 `寶可夢號` suffix 污染，同 checkpoint 全部清零。
- 相較 v0.8.4 runtime DAT，最終共有 436 個 value 改變。
- `full_mt_argos_s2twp` 降至 9,285。

## 重要新案例
1. `otherworldly` 被翻成「異性戀」：單看中文黑名單可以抓，但更重要的是高曝光 NPC 必須整 Map review。
2. `Channeler` → 「海峽客」：Trainer class / 世界觀名詞不能當一般字典詞。
3. `critical hit` 出現「臨界命中／重大打擊／臨界點」等多種錯法。只列壞中文永遠列不完，因此改成 English source-aware contract：只要 English 含 critical hit，繁中就必須含「要害」。
4. `Pokévial` 被翻成「波克維亞」、`PokéRider` →「波克瑞德」。自訂功能品牌應視為 protected brand，除非 glossary 有正式決議。
5. `P1/P2/P3` 被翻成「臨 1／臨2」。短字串可能是 opaque UI key，不得因為「看起來像文字」就翻。
6. `Mega Stone` 曾大量變成普通「巨石」。全域把「巨石」改成「超級石」會傷到真正的巨石，因此必須用 source-aware 條件修。
7. `寶可夢號` 是 MT 對 Pokémon 的 suffix 污染，可由全庫 scanner 抓出並定向清理。
8. `爾時世尊...` 這種完全無關的幻譯證明：即使 CJK、placeholder、結構全部 PASS，也仍可能有嚴重語義錯誤。

## Map 72–80 主要內容
- 金黃市關卡警衛罷工/阿杏茶事件
- 玉虹市、莉佳、卡拉卡拉與遊戲城線索
- 占卜師 / Nuzlocke 預言
- 玉虹百貨公司、娜姿攝影事件、交換與招式學習器
- 咖哩/拉麵/代幣盒/加密寶可夢 NPC
- 開發者房間、洛托姆家電、特性專家

## v1.6 QA 結果
- manifest: 21,438
- non-empty zh_tw: 21,437
- reusable/source-aware lint: HARD 0 / WARN 0
- manifest → DAT: 21,437 checked / 0 mismatch
- Marshal structure: 0 issue
- 下一個人工 review 起點：Map 81
