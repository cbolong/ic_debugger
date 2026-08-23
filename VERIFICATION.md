# VERIFICATION.md — 功能 × 驗證追溯表

每一個功能行為都對應到可重跑的驗證項目。目的有二：
1. **抓回歸**：任何人（含 AI）改壞既有行為，`pytest` 就紅。
2. **保護設計**：表中標註「**設計如此**」的行為是刻意決策，不是 bug ——
   之後不准當成錯誤「修掉」；要改必須先改這份文件與對應測試。

**窮舉原則**：可有限窮舉的軸（位元範圍組合、截斷長度、警告分支、格式變體、
真值表）一律全數列舉；無限的輸入空間則列出等價類並以「與實作不同演算法的
參考實作」暴力對照（隨機種子固定，結果可重現）。

執行方式：`PYTHONPATH=. pytest tests/ -q` —— CI（auto-build.yml）在每次
打包前強制全綠，測試不過就不會產生 Release。

## 1. 位元運算（所有數字呈現的地基）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| `extract(v, msb, lsb)` 取欄位值 | test_exhaustive_bits.py::test_extract_all_ranges_32bit / _64bit_boundaries | 32-bit：**全部 528 種 (msb,lsb) 組合**×6 種 pattern＋單邊界值；64-bit：全部 2080 種組合×5 pattern；參考答案用二進位字串切片（獨立演算法） |
| 欄位完整分割可重組原值（無位移偏差） | ::test_extract_field_partition_reconstructs_value | 32/64-bit 各 100 組隨機分割×5 值（seed 固定） |
| hex 呈現：固定寬度、大寫、>32-bit 每 8 位底線 | ::test_fmt_hex_all_widths_roundtrip / _documented_examples | **寬度 1–64 全部**×5 邊界值，驗可逆、位數、底線位置 |
| bin 呈現：0b 前綴、由 LSB 每 4 位分組 | ::test_fmt_bin_all_widths_roundtrip / _documented_examples | **寬度 1–64 全部**×4 邊界值 |
| 值一律以字串過 JS bridge（**設計如此**：64-bit 過 JS Number 會掉精度） | test_analyzer.py::test_payload_decode_and_differs（0x1_00000000 案例）＋ CLAUDE.md 不變條件 2 | 64-bit 邊界值 |

## 2. Spec MD 解析（spec_loader）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| 數值格式：0x／0b／十進位／底線／空白 | test_exhaustive_spec_loader.py::test_parse_int_exhaustive_table | **26 種輸入寫法全表**（含 -、?、—、N/A、TBD → None；**設計如此**：未知不是錯誤） |
| Bits 寫法：`31:24`、`31-24`、`31~24`、`[31:24]`、單一位元、**寫反自動轉正（設計如此）** | ::test_bits_syntax_exhaustive | 10 種合法寫法＋8 種非法寫法（非法→整列略過＋警告） |
| 表頭別名（中英文，**設計如此**：容錯 AI 產出） | ::test_table_header_aliases_exhaustive | **5 組欄位×全部 26 個別名逐一驗證** |
| 全形冒號／CRLF／BOM／markdown 行內標記／HTML 註解／散文行 | ::test_fullwidth_colon_everywhere、_crlf_…、_bom_via_file、_html_comments_… | 每種容錯各一組，合法輸入必須**零警告** |
| 寬度：檔頭 Width 8/16/32/64、暫存器 Size 覆寫 | ::test_size_64_field_to_63_and_widths、_register_level_size_override | 4 種寬度全跑 |
| Enum 掛到欄位、同名欄位全掛（**設計如此**）、Enum 後接屬性行不誤吞 | ::test_enum_attaches_to_all_…、_enum_then_register_attr_not_swallowed | 邊界案例逐一 |
| 暫存器依 Offset 排序、欄位依 msb 排序（非文件順序，**設計如此**） | ::test_registers_sorted_…、_fields_sorted_… | 亂序輸入 |
| **全部 22 條警告分支**：訊息內容＋降級行為（略過該列/該暫存器，不毀整份 spec） | ::test_every_warning_branch（parametrize 22 案例）＋ _file_read_error_… | **警告分支逐條窮舉**，含行號驗證（_warning_carries_line_number） |
| 合法輸入零多餘警告（防警告通膨） | ::test_clean_specs_have_zero_warnings、test_spec_loader.py::test_builtin_specs_parse_clean | 內建 spec 全檔 |
| **內建 spec 必須解析零警告**（CI 品質關卡） | test_spec_loader.py::test_builtin_specs_parse_clean | specs/ 遞迴全部檔案 |
| 四顆內建 CPU 都在、且每份都有 Status／Source／足夠的暫存器數 | ::test_all_four_builtin_cpus_present_and_clean | cortex_r5／cortex_a55／n25／n45 逐份 |
| 廠商＝子資料夾名（UI 分組依據） | ::test_builtin_specs_have_vendor_from_subfolder | 四份逐一 |
| README.md 與底線開頭檔案不當成 spec（**設計如此**：讓維護者能在 spec 旁放說明與草稿） | ::test_is_spec_file_skips_readme_and_underscore、_readme_in_specs_dir_is_not_loaded | 副檔名／檔名各變體 |
| `# Status:` 檔頭解析且不產生警告 | ::test_status_header_parsed_without_warning | — |

## 3. bin 解析與對應（bin_parser）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| little-endian、Offset=檔內位移（**與使用者確認的契約**） | test_exhaustive_analyzer.py::test_word_at_exhaustive_small_buffer、test_analyzer.py::test_word_at_little_endian | 12-byte buffer 內**全部 offset（含負值與越界）× 4 種寬度**，與 int.from_bytes 對照 |
| 空檔／超大檔擋下、訊息可讀 | test_analyzer.py::test_load_bin_errors | 各錯誤路徑 |

## 4. 解碼引擎（analyzer）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| covered／partial（截斷）判定 | test_exhaustive_analyzer.py::test_truncation_sweep_every_length | 16-byte spec（32/64 混合）**bin 長度 0–18 每個長度全驗**，含統計一致性與 hexdump note 三態 |
| differs 判定（值/Reset 已知未知的所有組合；**設計如此**：全未知＝「無基準」None 而非 False；欄位 Reset 明寫優先於推導） | ::test_differs_truth_table、_differs_none_when_bin_absent_or_uncovered | **8 格真值表逐格**＋無 bin/未涵蓋 |
| 欄位 Reset 從暫存器 Reset 自動推導（**設計如此**：表格可少抄） | 同上（真值表 3、4 列） | — |
| 未定義位元自動補列 | ::test_uncovered_ranges_vs_bruteforce_random_layouts | 32/64-bit 各 150 組隨機佈局，與 set 補集暴力對照＋不相鄰驗證 |
| rows 完整分割不變條件（bit ruler／欄位表的前提） | ::test_rows_always_partition_register_exactly | 32/64-bit 各 60 組隨機佈局：覆蓋全部 bit、無重疊、msb 降冪 |
| 未定義位元非 0 提示 | ::test_nonzero_undef_flag | 0／非 0 兩態 |
| enum：目前值標記與缺項行為（值不在表 → 無 label、無 current） | ::test_enum_current_marking_full_domain | 2-bit 欄位**值域 0–3 全窮舉**（含刻意缺 0b11） |
| hexdump：逐 word 對應（32/64/空洞）、LE 組值、檔尾不足一 word | ::test_hexdump_annotation_with_gap_and_64bit、_hexdump_value_matches_le_word、test_analyzer.py::test_hexdump_annotation | 混合佈局逐 word 斷言 |
| 範例 bin × 範例 spec 端到端 | test_analyzer.py::test_sample_bin_against_r5_spec | SCTLR/DFSR 等關鍵解碼逐項 |

## 5. Spec 全文檢視（稽核＋連續對照）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| 原始 MD 一字不差回傳（**設計如此**：稽核要能對 TRM 原文） | test_exhaustive_analyzer.py::test_spec_detail_builtin_raw_matches_file | 內建 R5 全文比對 |
| 檔案消失／無路徑時降級（解析內容仍可看） | ::test_spec_detail_missing_file_degrades、_no_path | 兩種失效路徑 |
| 未載入 bin（或看非目前 spec）＝純 spec、無值 | ::test_spec_detail_builtin_raw_matches_file | 全暫存器斷言 |
| 已載入 bin 時同頁疊上目前值，且值/differs 與暫存器頁**完全一致**（**設計如此**：兩頁共用 build_payload 單一解碼來源，不允許各算各的） | ::test_spec_detail_with_bin_overlays_values | 範例 bin 全暫存器逐一比對 |
| **只有「目前使用中的 spec」疊值**（**設計如此**：bin 的 offset 對應跟著 spec 走，套到別份 spec 上值無意義） | test_app_state.py::test_detail_binf_only_for_current_spec | 目前／非目前／無 bin 三態 |
| 「目前值」與「Reset」在欄位表相鄰並排（**設計如此**：一眼比對不用左右掃） | tools/preview.py 截圖（第 10 節人工清單第 4/6 項） | — |

## 6. 快速反查（offset／名稱＋值 → 單筆解碼）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| 解析路徑：名稱（大小寫不拘/含空白）、offset（0x/十進位/0b）、落在暫存器範圍中間（32-bit 中段、64-bit 高半段）→ 整顆解碼＋note | test_lookup.py::test_resolution_paths_exhaustive | **12 種解析路徑全表** |
| 失敗路徑：未知名稱（帶「名稱相近」建議）、超出 spec 範圍（講明涵蓋區間）、空輸入、空 spec —— 一律中文錯誤，絕不丟例外 | ::test_resolution_failures_exhaustive、_empty_spec | 6 種失敗路徑全表 |
| **名稱優先於 offset 解讀**（**設計如此**：名稱長得像數字時以名稱為準） | ::test_name_priority_over_offset_parse | — |
| 值驗證：0／1／最大值合法；最大值+1、負數、亂字串 → 錯誤（**設計如此**：絕不默默截斷） | ::test_value_bounds_every_width | **寬度 8/16/32/64 全部 × 邊界值** |
| 值格式等價：0x／0X／十進位／0b／底線／空白 → 同一結果 | ::test_value_formats_equivalent_and_invalid | 6 種寫法＋6 種非法輸入 |
| **與 bin 模式完全同源**（**設計如此**：共用 _register_dict，deep equality 一個 key 都不准差） | ::test_lookup_identical_to_bin_path、_lookup_r5_sample_case | 32/64-bit 逐顆深度比對＋R5 端到端 |
| 同名暫存器取 offset 最小者 | ::test_duplicate_register_names_pick_first_by_offset | — |
| 查詢歷史限本次執行、換 spec 即作廢（UI 行為） | tools/preview.py 截圖＋第 10 節人工清單 | — |

## 7. App 狀態（spec 集合管理）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| 內建載入、last_spec 記憶、預設選第一個 | test_app_state.py::test_load_builtin_…、_last_spec_restored | — |
| 外部 spec 加入/移除/重載、內建不可移除、同名衝突加 `~2` 後綴（**設計如此**） | ::test_add_and_remove_external、_external_id_collision_…、_reload_keeps_external | 各狀態轉移 |

## 8. UI（HTML/CSS/JS 靜態保證）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| 佔位符全部替換、主題屬性正確 | test_ui.py::test_no_leftover_placeholders、_light_theme_attr_empty | 4 個佔位符 |
| 深色 tokens ⊆ 淺色 tokens（單一色票來源） | ::test_theme_tokens_complete | 全 token 集合比對 |
| **用到的每個 var(--c-\*) 都有定義**（打錯 token 名顏色會靜默消失） | ::test_every_used_css_token_is_defined_in_light_root | HTML/CSS/JS 全文掃描 |
| **每個 inline handler 都有對應函式**（改名/刪函式把按鈕改壞在此被抓） | ::test_every_inline_handler_has_declared_function | 全部 onclick/oninput/onchange |
| JS 引用的靜態元素 id 都存在 | ::test_every_getelementbyid_target_exists | 全部 getElementById |
| spec 下拉選單與 Spec 管理依廠商分組（**設計如此**：共用 groupSpecsByVendor，不准各分各的） | tools/preview.py 截圖＋第 10 節人工清單 | ARM／Andes／外部載入三組 |
| 六個視圖都有導覽入口與 render 分支 | ::test_all_views_have_render_branch_and_nav_entry | overview/regs/lookup/hex/specdoc/specs |
| **JS 呼叫的每個 api 方法都存在於 Python Api**（橋接兩端同步） | ::test_api_methods_called_from_js_exist_in_python | 全部 api() 呼叫 × AST 解析 Api 類 |
| Python 實際輸出的內嵌 JS 語法正確 | ::test_js_syntax_with_node（node --check） | head＋body 兩段 script |
| 保留位降噪：與 Reset 相同的保留／未定義列預設隱藏；**值≠Reset 或未定義非 0 的保留位強制顯示**（**設計如此**：安全網，不准藏掉異常）；隱藏數提示列可點擊展開；bit ruler 永遠顯示全部位元；**Spec 全文不套用隱藏**（稽核要完整，**設計如此**） | tools/preview.py 截圖＋第 10 節人工清單 | 展開 SCTLR 目視（14 個安靜保留位收起、藍色異常位保留） |
| 渲染共用（防改 A 壞 B）：暫存器展開與快速反查共用 registerBlock()；狀態 chip 共用 statusChipHtml()（**設計如此**：同一資訊只准一份渲染程式，見 CLAUDE.md 不變條件 12） | 程式結構＋test_every_inline_handler_…（改名即紅） | — |
| 真實瀏覽器渲染（五視圖×深淺色、console error 即失敗） | `PYTHONPATH=. python tools/preview.py`（改 UI 後必跑；產 10 張截圖） | overview/regs(展開)/lookup/hex/specs/specdoc(解析後+原文)×兩主題 |

## 9. 報告匯出

| 行為 | 驗證 |
|---|---|
| 標題/統計/enum 意義進報告、only_differs 過濾 | test_analyzer.py::test_report_markdown |
| 表格 cell 的「\|」跳脫（enum 意義可含直線） | ::test_report_escapes_pipe_in_enum_label |
| 無 bin 措辭、零差異時 only_differs 為空表 | ::test_report_no_bin_and_no_diff_wording |

## 10. 無法自動化的部分 —— Windows 實機檢查清單

pywebview／WebView2／檔案對話框／onefile 打包只能在 Windows 實機驗。
**每次 Release 後抽最新 exe 跑一遍：**

1. 從 Releases 下載 `IC_Debugger.exe` 雙擊（SmartScreen →「仍要執行」）→ 視窗開啟、無白畫面。
2. 右上角下拉：spec 依「ARM／Andes」分組，四顆 CPU 都在；切換後暫存器清單跟著換。
3. 「匯入 bin」選 `examples/sample_r5.bin` → 總覽顯示 12/12、2 個 ≠Reset（SCTLR、CPACR）。
4. 展開 SCTLR → 「目前值／Reset」成對顯示在最上方；bit ruler 顯示 M/C/Z/I/BR 藍色高亮；DFSR 的 FS 顯示「對齊（alignment）fault」。
5. 🌓 切深色 → 關掉重開 exe → 仍是深色（設定記憶）。
6. 「Spec 全文」→ 兩個分頁都有內容；載入 bin 後每個暫存器標頭出現「目前值」（SCTLR/CPACR 為藍色 ≠Reset）；「原始 Markdown」與 repo 檔案一致。
7. 「快速反查」輸入 SCTLR＋0x00C7187D → 解碼結果與第 3 步展開的 SCTLR 完全相同；輸入 0xFF（超範圍 offset）→ 出現涵蓋範圍錯誤訊息。
8. 「Spec 管理 → 載入外部 Spec」選任一 .md → 出現在清單；「移除」正常。
9. 「匯出報告 (.md)」→ 檔案打得開、內容與畫面一致。
10. 展開 SCTLR →「與 Reset 相同的保留位」預設收起（有「已隱藏 N 個…」提示列，點擊或按工具列「顯示保留位」展開）；點 bit ruler 上被隱藏的保留位 → 自動展開並跳到該列。
11. **系統列**：按「縮小」→ 視窗從工作列消失、右下角系統列出現晶片圖示（首次附提示气泡）；**雙擊圖示**或右鍵「開啟 IC Debugger」→ 視窗回來；右鍵「結束」→ 程式關閉。按「X」→ 程式真正關閉，且系統列圖示消失、工作管理員無殘留程序。
12. `%APPDATA%\IC_Debugger\ic_debugger.log` 無 ERROR。

## 11. 新增功能的規則

新功能（或行為變更）**必須**：
1. 在本檔加追溯列（含窮舉範圍說明）；
2. 加對應測試（能窮舉就窮舉）；
3. 刻意的取捨標「設計如此」並寫理由 —— 這是防止之後被誤修的鎖。
