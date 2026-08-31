# RMXP / Pokémon Essentials 繁體中文化可重用規則 v1.1

## 核心原則
繁中化不是把所有 String 交給翻譯器。先分類、保護機器字串與控制碼，再翻玩家可見內容，最後以靜態 QA + 實機截圖驗證。

## 既有必守規則
1. 玩家可見劇情/NPC/說明可翻；UI 短詞只走受控詞庫。
2. `Graphics/`、`Audio/`、`Data/`、`Plugins/` 路徑、UI suffix/key 永不翻譯。
3. `\v[]`、`\PN`、`\c[]`、`%s`、`{1}`、`{1:03d}`、`#{...}`、HTML tags 先保護再翻。
4. Pokémon、人物、地名、招式、特性、道具名先套官方台灣詞庫，禁止 MT 自由音譯。
5. CJK 換行在文字 formatter 處理，不逐句人工塞換行，也不以全域 Bitmap hook 破壞 UI。
6. Map 名稱需查 exact-version `MapInfos.rxdata`；不能假設所有文字都在 messages DAT。
7. 長工作先 checkpoint，再 QA；QA fail 不得把完整成果一起丟掉。
8. 每個實機新錯誤都必須轉成：根因 → 規則 → lint/test → handoff。

## v1.1 新增：雙語 authority 規則
Anil 的 runtime key 是西班牙文，但 English edition 的 `translation` 欄可能做過改寫，甚至刪減/變更 HTML tag。

- **玩家實際要玩的 English edition 語意，以 `translation` 欄為主要語意 authority。**
- `source` 欄只用於補充上下文、人物語氣與歧義判讀。
- **控制碼與 HTML tag 序列必須跟 target-edition 的 `translation` 保持一致。**
- 不可因為 source 裡多了一個 `<b>` 就把它擅自加回繁中，否則會破壞既有 formatter/QA 契約。

實例：Brock 的 TM 台詞，西文 source 有 `<b>Team Rocket</b>`，英文 edition 改成「help back in the museum」。繁中應跟英文 edition 的內容和 tag 結構，而不是把兩個版本混在一起。

## v1.1 新增：DAT patch 必須 key-based
不可用「舊翻譯值 → 新翻譯值」做全域 replace。

原因：不同 source key 可能被 MT 翻成完全相同的錯誤中文，但人工修正後需要兩個不同句子。全域 value replace 會把其中一個錯修成另一個。

正式規則：
- EVENT_TEXTS：以 `(section_id=0, map_id, source/key)` 精確定位。
- 其他 Hash section：以 `(section_id, key)` 精確定位。
- Patch 後必跑 Marshal class/length/hash-key structure compare。

## v1.1 新增：proper-noun transliteration regression
實機與 Map 41–54 人工潤稿又抓到一批「英文專名被 MT 音譯」的錯誤，例如：
- Brock → 布洛克 → 小剛
- Cubone → 庫邦 → 卡拉卡拉
- Graveler → 格雷夫勒 → 隆隆石
- Sudowoodo → 蘇杜多 → 樹才怪
- Clefairy → 克蕾費 → 皮皮
- Spearow → 斯皮洛 → 烈雀
- Farfetch'd → 法菲奇 → 大蔥鴨
- Pidgeot → 皮奇奧 → 大比鳥
- Rock-type → 搖滾屬性 → 岩石屬性
- Trainer → 培訓員 → 訓練家
- Technical Machine → 技術機器 → 招式學習器

上述錯誤輸出已加入 data-driven `known_bad_patterns.tsv`。後續新專案可以只更新 TSV，不必每次改 lint 程式。

## 每版硬 QA
- placeholder/control token sequence = 0 mismatch
- Ruby interpolation/format spec = 0 mismatch
- HTML tag sequence = 0 mismatch
- resource path translated = 0
- protected suffix/key translated = 0
- known bad pattern HARD = 0
- Marshal section/type/key structure = unchanged
- Scripts count/targeted diff
- ZIP integrity
- JoiPlay/AYN THOR：Battle HUD、Move menu、Summary、地名、長對話換行實機 regression
