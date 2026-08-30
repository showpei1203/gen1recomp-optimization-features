# RMXP Pokémon 繁體中文工具鏈 v0.1.0

目標：把 Pokémon Essentials / RPG Maker XP 同人作品的繁中化工作，從人工逐事件點擊改成可重複、可驗證、可更新的管線。

## 正式策略：Essentials-first
目前主要目標鎖定 **Pokémon Essentials v17-v21+**。一般作品優先使用 Essentials 原生的 Extract Text / Compile Text 機制。只有遇到非標準或高度魔改作品，才啟用 Ruby/PBS 掃描或新增 adapter。這比一開始就直接改 `MapXXX.rxdata` 穩定得多，也比較不像拿鏈鋸修手錶。

## v0.1.0
- 偵測 Essentials 常見結構與新舊訊息格式線索。
- 支援 Essentials Extract Text 產出的 `intl.txt` 與 `Text_*/*.txt`。
- 將翻譯條目匯出為 UTF-8 TSV，適合 Excel / Google Sheets / AI 批次翻譯。
- 僅回寫 translation line，不改 source/key/section。
- 保護並 QA 常見控制碼、`\v[]`、`\c[]`、`%s`、`{1}` 等 placeholder。
- 可套用繁中術語表。
- 可掃描 `.rb/.txt/.pbs/.ini/.csv` 中可能漏掉的英文。
- 附 `Scripts.rxdata` Ruby 解包工具。
- Windows `.bat` 一鍵入口，不需要第三方 Python 套件。

## 推薦流程
1. 在遊戲內用 Essentials Debug 的 Extract Text 產生 `intl.txt` 或 `Text_default_game` / `Text_default_core`。
2. `02_EXPORT_TRANSLATION.bat`
3. 編輯 `work/translation_manifest.tsv` 的 `translation` 欄。
4. `03_APPLY_GLOSSARY.bat`
5. `05_QA.bat`
6. `04_BUILD_TRANSLATION.bat`
7. 回 Essentials Debug 用 Compile Translated Text / Compile Text 生成語言 `.dat`。
8. 實機驗收字型、對話框、戰鬥 UI、選單與存檔。

v0.1.0 不直接改 `MapXXX.rxdata`。標準 Essentials 專案走原生翻譯管線；binary surgery 只當 fallback。
