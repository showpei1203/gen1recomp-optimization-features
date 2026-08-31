# Pokémon Anil zh-TW 實戰心得 v0.8.4

## 本輪新增發現
1. Map 71 全 39 條 EVENT_TEXT 重新人工 review，35 條實際改寫。
2. 最後一條 v1.4 hard-fail `波克矇` 已修正，21,438 條 master 的 known-bad HARD lint 回到 0。
3. `Professor Samson -> 加百列教授` 並非單點錯誤，而是 8 個重複英文任務模板跨 222 rows 的系統性污染。
4. 攝影師 Seymour 事件在多張 Map 複製，錯誤 `西摩語Name`、`\GWould...`、`\GSplendid...`、`這是在房子`、`大聲喊一聲` 也會跟著複製。應以 exact-English phrase template 一次人工封正。
5. `Poké球`、`月球石` 顯示「已經是中文」不代表符合台灣 Pokémon 官方用語。專有詞 QA 不能只檢查英文字母比例。

## 新流程規則
- 可重複事件要建立「English exact phrase -> vetted zh-TW」模板庫。
- 不能用「錯誤中文 -> 正確中文」當全域 key。
- 每個有實質修改的 checkpoint 必須產出 CURRENT_HANDOVER.md，並同步 GitHub/Drive。

## v0.8.4 本輪數字
- Map 71 EVENT_TEXT reviewed: 39/39
- Map 71 changed: 35
- exact English templates: 29
- exact template matched rows: 410
- exact template changed rows: 393
- remaining `full_mt_argos_s2twp`: 9,507
- known-bad HARD issues: 0
- manifest -> DAT mismatches: 0
- Marshal structure issues: 0
