# RMXP Pokémon 繁體中文工具鏈 v0.1.0

目標：把 Pokémon Essentials / RPG Maker XP 同人作品的繁中化工作，從人工逐事件點擊改成可重複、可驗證、可更新的管線。

## 正式策略：Essentials-first
主要目標鎖定 **Pokémon Essentials v17-v21+**。一般作品優先使用 Essentials 原生 Extract Text / Compile Text；只有非標準或高度魔改作品才啟用 Ruby/PBS 掃描或新增 adapter。

## v0.1.0
- 偵測 Essentials 常見結構與新舊訊息格式線索。
- 支援 `intl.txt` 與 `Text_*/*.txt`。
- 匯出 UTF-8 TSV，適合 Excel / Google Sheets / AI 批次翻譯。
- 僅回寫 translation line，不改 source/key/section。
- 保護並 QA `\v[]`、`\c[]`、`%s`、`{1}` 等 placeholder。
- 可套用繁中術語表。
- 可掃描 `.rb/.txt/.pbs/.ini/.csv` 漏網英文。
- 附 `Scripts.rxdata` Ruby 解包工具。
- Windows `.bat` 一鍵入口，Python 標準函式庫即可。

標準 Essentials 專案走原生翻譯管線；直接修改 RMXP binary 只當 fallback。

## 大型遊戲 ZIP：Localization Source Pack

Drive 連接器的單次 raw download 有約 256 MB 上限。完整遊戲 ZIP 太大時，使用：

`07_PREP_LOCALIZATION_SOURCE.bat`

把原始遊戲 ZIP 拖到 BAT 上。它會直接從 ZIP 抽出繁中化需要的 `Data/`、`PBS/`、`Plugins/`、`Fonts/`、`Text_*`、`Game.ini` 等內容，產生：

`<原檔名>_LOCALIZATION_SOURCE.zip`

原始 ZIP 不會被修改。

## v0.1.2: Essentials v21 direct-DAT bridge

Anil DE 1.0.23 proved that waiting for an in-game Extract Text pass is unnecessary for many v21 projects. The toolchain can now read compiled `messages_game.dat` plus an existing translated DAT directly with Ruby Marshal.

- `08_EXPORT_V21_DAT.bat`: default + existing translation DAT -> TSV.
- `09_BUILD_V21_DAT.bat`: TSV `zh_tw` column -> `messages_zh_tw_game.dat`, gated by placeholder QA.
- `10_PATCH_LANGUAGE_SUPPORT.bat`: adds a `zh_tw` language entry and conditional system CJK-font fallback to `Scripts.rxdata`.
- `toolchain/essentials_v21_dat_bridge.rb`: exports the **union** of default and translated keys. Anil contains live translation-only keys, so default-only extraction would silently miss text.

No third-party font file is bundled. CJK font selection only tries fonts already installed on the target OS.
