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
