# Pokémon Essentials 繁中化工作流程

Essentials 本身支援抽取翻譯文字。新版本常見 `messages_core.dat` + `messages_game.dat`，舊版常見 `messages.dat` / `intl.txt`。

本工具鏈以 **Essentials-first** 為正式策略：

`Extract Text -> TSV -> 翻譯/術語 -> QA -> 重建 Text -> Essentials Compile Text`

只有遇到非標準或高度魔改作品，才進入 Ruby / PBS / 自訂資料掃描與 adapter 路徑，避免不必要地直接修改 RMXP binary。

## 版本策略
- Essentials v21+：優先支援 split messages / `Text_*` 形式。
- Essentials v17-v20：支援 `intl.txt` / legacy translation flow。
- 更舊或魔改版：先偵測結構，再決定是否需要 adapter。

## 字型
字型是否包含繁中文字形是獨立問題。若顯示方框，先查遊戲字型設定。未確認授權前，不把第三方字型檔提交到 GitHub。

## 最低 QA
- `PLACEHOLDER_MISMATCH = 0`
- `UNTRANSLATED` 持續下降
- 實測戰鬥文字、選單、事件對話、圖鑑、道具/招式/特性名
- 長句不超框
- 存檔後語言設定可保持
