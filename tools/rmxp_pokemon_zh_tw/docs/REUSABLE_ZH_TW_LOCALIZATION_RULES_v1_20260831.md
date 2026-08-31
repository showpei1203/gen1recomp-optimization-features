# RMXP / Pokémon Essentials 繁體中文化可重用規則 v1.2

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

## 雙語 authority 規則
Anil 的 runtime key 是西班牙文，但 English edition 的 `translation` 欄可能做過改寫，甚至刪減/變更 HTML tag。
- 玩家實際要玩的 English edition 語意，以 `translation` 欄為主要語意 authority。
- `source` 欄只用於補充上下文、人物語氣與歧義判讀。
- 控制碼與 HTML tag 序列必須跟 target-edition 的 `translation` 保持一致。
- 不可因為 source 裡多了一個 `<b>` 就把它擅自加回繁中。

## DAT patch 必須 key-based
不可用「舊翻譯值 → 新翻譯值」做全域 replace。不同 source key 可能被 MT 翻成相同中文，但人工修正後需要不同句子。
- EVENT_TEXTS：以 `(section_id=0, map_id, source/key)` 精確定位。
- 其他 Hash section：以 `(section_id, key)` 精確定位。
- Patch 後必跑 Marshal class/length/hash-key structure compare。

## proper-noun transliteration regression
任何 Pokémon 專名音譯污染都列為 HARD FAIL。已收錄案例包括：
- Brock → 布洛克 → 小剛
- Ariana → 阿里安納 → 雅典娜
- Archer → 阿徹 → 阿波羅
- Cubone → 庫邦 → 卡拉卡拉
- Graveler → 格雷夫勒 → 隆隆石
- Sudowoodo → 蘇杜多 → 樹才怪
- Clefairy → 克蕾費 → 皮皮
- Spearow → 斯皮洛 → 烈雀
- Farfetch'd → 法菲奇 → 大蔥鴨
- Pidgeot → 皮奇奧 → 大比鳥
- Ninetales → 尼尼塔萊斯 → 九尾
- Charmander → 查曼德 → 小火龍
- Totodile → 託多迪爾 → 小鋸鱷
- Starmie → 斯塔米 → 寶石海星
- Bellossom → 貝爾洛瑟姆 → 美麗花
- Rapidash → 拉皮塔什 → 烈焰馬
- Cyndaquil → 辛達基爾 → 火球鼠
- Bulbasaur → 布巴索爾 → 妙蛙種子
- Lugia → 盧吉亞 → 洛奇亞

## phrase-level idiom regression
英語笑點、慣用語不能逐字 MT。已證明的 HARD 案例：
- `Smell ya!` / `Smell you later` → 不可「聞聞你／晚點聞聞」，依語境翻「先走啦／回頭見」。
- `party pooper` → 不可「黨拉屎」，依語境翻「掃興鬼」。
- `smarty-pants` → 不可「聰明的褲子」，依角色口吻翻「聰明人／自作聰明的傢伙」。
- `Drats` → 不可音譯成「德拉特斯」。
- `cakewalk` → 不可按 cake 逐字理解，應譯為「輕鬆／容易」。

## 全庫回歸規則
實機或人工審稿抓到一個新錯譯時，不只修單一 entry：
1. 加入 `known_bad_patterns.tsv`。
2. 立即重跑全 manifest。
3. 同類錯誤即使出現在後期 Map、Pokédex、Item Description、Trainer Name，也要在同一 checkpoint 清乾淨。
4. HARD issue 必須回到 0 才能封 checkpoint。

## 固定功能詞模板
寄放屋、交換、道館提示、Berry 狀態恢復、招式學習器等跨地圖重複流程應建立固定句型，不交給自由 MT。例如交換句型：`\PN用九尾交換到了小火龍！`。

## 每批人工潤稿的封版條件
- 該批 Map 的 EVENT_TEXTS 全部人工 review，不能只挑 `full_mt_argos_s2twp`。
- placeholder/control token sequence = 0 mismatch。
- Ruby interpolation/format spec = 0 mismatch。
- HTML tag sequence = 0 mismatch。
- resource path translated = 0。
- protected suffix/key translated = 0。
- known bad pattern HARD = 0。
- Marshal section/type/key structure = unchanged。
- Scripts count/targeted diff。
- ZIP integrity PASS。
- JoiPlay/AYN THOR：Battle HUD、Move menu、Summary、地名、長對話換行實機 regression。
