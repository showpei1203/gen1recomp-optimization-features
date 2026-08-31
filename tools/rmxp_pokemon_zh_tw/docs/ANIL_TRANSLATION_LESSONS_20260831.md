# Pokémon Anil zh-TW 實戰心得與回歸案例 2026-08-31

## 已證明的結構根因
- UI 背景消失：MT 翻到 Graphics resource path。
- Trainer Memo 背景消失：內部 suffix `memo` 被翻成 `備忘`，實際路徑變成 `bg_備忘`。
- 繁中長對話切掉：Essentials formatter 依英文空格斷行，CJK 沒有可用 break point。
- `Pallet Town` 漏翻：畫面來源為 exact v1.0.23 `MapInfos.rxdata`，不是單純 message DAT。
- `Smell ya / Smell you later`：英語慣用語不可逐字機翻，需 phrase regression lexicon。
- Berry/Poffin 說明 `佛德童子`：固定遊戲描述模板不可任由 MT 幻譯。

## 既有流程教訓
- 「有翻譯」與「可遊玩繁中化」是兩件事。
- 玩家可見文字、UI label、machine key、resource path 必須在翻譯前分流。
- 每個實機錯誤都要轉成根因、規則、lint/test、handover。
- DAT patch 必須以 section/map/key 精確定位，不可 value-based global replace。
- English edition `translation` 欄是主要語意與控制碼 authority；source 只補充上下文。
- Pokémon 專名、人物、固定功能詞必須走受控詞庫。
- 一批 Map 要 review 全 EVENT_TEXT，不只挑機翻狀態列。
- 抓到新錯譯後要立刻全庫掃描，不只修眼前 Map。

## v0.7.7 / Map 56–61
- 233 條 EVENT_TEXT 全部人工檢閱。
- 220 條直接改寫，另有跨 section regression cleanup。
- 馬志士、小霞、聖安奴號等高曝光劇情證明英語軍事梗、雙關、慣用語不能直接逐字 MT。
- `party pooper`、`smarty-pants`、`Drats`、`cakewalk` 等轉為 phrase-level regression。

## v0.8.5 / Map 72–80
- Map 72–80：212 條 EVENT_TEXT 全數人工 review。
- Map batch 直接改寫 169 條。
- exact-English / regression cleanup 另外修改 89 條跨地圖重複字串。
- v1.6 source-aware HARD lint 初次抓出 40 條舊黑名單沒抓到的錯誤，全部修正。
- source-aware WARN 再抓出 105 條 `Mega Stone` 詞義錯置與 33 條 `寶可夢號` suffix 污染，同 checkpoint 清零。
- 相較 v0.8.4 runtime DAT，最終共有 436 個 value 改變。
- `full_mt_argos_s2twp` 降至 9,285。

### v0.8.5 新案例
1. `otherworldly` → 「異性戀」。高曝光 NPC 必須整 Map review，單靠格式 QA 沒用。
2. `Channeler` → 「海峽客」。Trainer class / 世界觀詞不能當一般字典詞。
3. `critical hit` 有「臨界命中／重大打擊／臨界點」等多種錯法，因此改採 English source-aware contract，只要 source 含 critical hit，繁中必須用「要害」。
4. `Pokévial` →「波克維亞」、`PokéRider` →「波克瑞德」。自訂功能品牌必須 protected。
5. `P1/P2/P3` →「臨 1／臨2」。短字串可能是 opaque UI label，未確認語意不可翻。
6. `Mega Stone` 大量變成普通「巨石」。不能全域改「巨石」，必須 source-aware 條件修正。
7. `寶可夢號` 是可重複掃描的 MT suffix 污染。
8. `爾時世尊...` 這種完全無關的幻譯證明 placeholder、CJK、Marshal 全 PASS 仍不代表語義安全。

## v0.8.5 QA
- manifest: 21,438
- non-empty zh_tw: 21,437
- reusable/source-aware lint v1.6: HARD 0 / WARN 0
- manifest → DAT: 21,437 checked / 0 mismatch
- Marshal structure: 0 issue
- 下一個人工 review 起點：Map 81
