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
| **`- Verified:` 逐顆出處解析**（有寫＝已對照官方文件；未寫＝空字串，**設計如此**：空字串不是 None，JS 端只做 truthy 判斷） | test_spec_loader.py::test_verified_header_parsed、_verified_defaults_to_empty_string、test_exhaustive_analyzer.py::test_verified_absent_is_empty_string_not_none | 有/無兩態＋型別 |
| 出處**不跨暫存器繼承**（前一顆標了，後一顆不准跟著變成已對照） | ::test_verified_is_per_register_not_inherited | 相鄰兩顆 |
| Enum 區塊後接 `- Verified:` 不被誤吞成 enum 項目 | ::test_verified_inside_enum_block_still_belongs_to_register | 邊界案例 |
| **R5 的 TCMTR 必須在**、位置介於 CTR 與 MPUIR、帶官方出處（2026-08-24 現場漏列事故） | ::test_builtin_r5_tcmtr_present_and_verified | offset／欄位／出處逐項 |
| 只要還有暫存器未對照，`# Status:` 必須掛 `⚠`（**設計如此**：不准讓使用者以為全部驗過） | ::test_builtin_specs_status_declares_verification_state | 四份內建 spec 全掃 |
| **RISC-V 標準 CSR 的位元定義**逐欄鎖定官方 v1.11（mstatus 的 UPIE／UIE、mie／mip 的 U 模式位元、misa 26 個擴充字母、mcause 值表、PMP cfg 佈局） | test_specs_official.py::test_mstatus_layout_matches_official_v1_11、_interrupt_registers_layout_…、_misa_extension_letters_…、_mcause_code_enum_…、_pmpcfg0_entry_layout_and_reset、_pmpaddr_registers_… | n25／n45 各 20 顆逐欄 |
| **重置值只寫官方明訂的**（mstatus 只有 MIE／MPRV＝0，PMP 只有 A／L＝0，其餘 `-`；**設計如此**：猜的 reset 會產生假的「≠ Reset」差異） | ::test_mstatus_reset_only_mie_and_mprv_are_defined、_pmpcfg0_entry_layout_and_reset、_a55_reset_values_are_not_fabricated | 兩份 RISC-V spec 全欄位＋A55 全暫存器 |
| N25 與 N45 的標準 CSR 定義必須完全一致（防「只改了一邊」） | ::test_n25_and_n45_standard_csrs_are_identical | 兩份 spec 深度比對 |
| **A55 欄位位置**鎖定 Arm 機器可讀架構規格（123 個具名欄位） | ::test_a55_field_positions_match_arm_machine_readable_spec、_a55_verified_registers_cite_the_machine_readable_spec | 12 顆暫存器逐欄＋Verified 出處字串 |
| **R5 清單完整性**鎖定官方 DDI 0406C.d Table B5-11（PMSA 全部可讀暫存器 53 顆＋TCM/CPSR/FPU） | ::test_r5_covers_full_official_pmsa_readable_list、_r5_id_registers_verified_against_ddi0406 | 60 顆逐名＋ID 系列出處 |
| **Andes 專屬 CSR 位置**鎖定 Andes 官方 QEMU（mmsc_cfg／micm_cfg／mmisc_ctl／mhsp_ctl 關鍵欄位＋CSR 編號） | ::test_riscv_andes_csr_positions_match_official_qemu | n25/n45 各 4 顆逐欄＋編號 |
| **完整 PMP＋計數器群**存在性（pmpcfg0-3、pmpaddr0-15、mcycle/minstret/mhpm3-6 含 h 半） | ::test_riscv_full_pmp_and_counters_present | n25/n45 各 90 顆計數 |
| **A55 擴充清單**鎖定（ID 全套／計時器／PMU／TF-A 實作定義顆） | ::test_a55_extended_registers_present、_a55_verified_registers_cite_the_machine_readable_spec | 55 顆計數＋23 顆逐名＋出處分類 |

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
| 暫存器層級沒有 Reset 時，判定只用得到有寫 Reset 的欄位 → `reset_partial` 為 True，chip 加註「（部分欄位）」（**設計如此**：不可以出現「Reset —」旁邊掛沒有但書的「= Reset」） | test_exhaustive_analyzer.py::test_reset_partial_flag_truth_table、_reset_partial_false_without_bin、_r5_ctr_shows_partial_after_reset_cleanup、test_ui.py::test_reset_chip_says_when_verdict_is_partial | **4 格真值表**＋無 bin＋R5 實例＋UI 單一渲染來源 |
| 未定義位元自動補列 | ::test_uncovered_ranges_vs_bruteforce_random_layouts | 32/64-bit 各 150 組隨機佈局，與 set 補集暴力對照＋不相鄰驗證 |
| rows 完整分割不變條件（bit ruler／欄位表的前提） | ::test_rows_always_partition_register_exactly | 32/64-bit 各 60 組隨機佈局：覆蓋全部 bit、無重疊、msb 降冪 |
| 未定義位元非 0 提示 | ::test_nonzero_undef_flag | 0／非 0 兩態 |
| enum：目前值標記與缺項行為（值不在表 → 無 label、無 current） | ::test_enum_current_marking_full_domain | 2-bit 欄位**值域 0–3 全窮舉**（含刻意缺 0b11） |
| hexdump：逐 word 對應（32/64/空洞）、LE 組值、檔尾不足一 word | ::test_hexdump_annotation_with_gap_and_64bit、_hexdump_value_matches_le_word、test_analyzer.py::test_hexdump_annotation | 混合佈局逐 word 斷言 |
| 範例 bin × 範例 spec 端到端 | test_analyzer.py::test_sample_bin_against_r5_spec | SCTLR/DFSR 等關鍵解碼逐項 |
| 出處（verified）在**三條解碼路徑**（bin 分析／Spec 全文／快速反查）看到同一個值（**設計如此**：共用 `_register_dict`） | test_exhaustive_analyzer.py::test_verified_flows_through_all_three_paths | R5 全暫存器逐顆 |
| `spec_summary.verified_count` 等於實際標了出處的顆數、且 0 ≤ count ≤ 總數 | ::test_verified_count_matches_registers | 四份內建 spec 全掃 |

## 5. Spec 全文檢視（稽核＋連續對照）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| 原始 MD 一字不差回傳（**設計如此**：稽核要能對 TRM 原文） | test_exhaustive_analyzer.py::test_spec_detail_builtin_raw_matches_file | 內建 R5 全文比對 |
| 檔案消失／無路徑時降級（解析內容仍可看） | ::test_spec_detail_missing_file_degrades、_no_path | 兩種失效路徑 |
| 未載入 bin（或看非目前 spec）＝純 spec、無值 | ::test_spec_detail_builtin_raw_matches_file | 全暫存器斷言 |
| 已載入 bin 時同頁疊上目前值，且值/differs 與暫存器頁**完全一致**（**設計如此**：兩頁共用 build_payload 單一解碼來源，不允許各算各的） | ::test_spec_detail_with_bin_overlays_values | 範例 bin 全暫存器逐一比對 |
| **只有「目前使用中的 spec」疊值**（**設計如此**：bin 的 offset 對應跟著 spec 走，套到別份 spec 上值無意義） | test_app_state.py::test_detail_binf_only_for_current_spec | 目前／非目前／無 bin 三態 |
| 「目前值」與「Reset」在欄位表相鄰並排（**設計如此**：一眼比對不用左右掃） | tools/preview.py 截圖（第 11 節人工清單第 4/6 項） | — |
| **載入失敗不得死在「載入中」**：get_spec_detail 失敗時頁面常駐顯示原因（toast 會消失）＋重試按鈕，重試成功後正常渲染；spec 集合變動時 docError 隨 doc 快取一起作廢 | test_ui_interactions.py::test_specdoc_error_shows_reason_and_retry_recovers（假 bridge 失敗一次→重試恢復，Chromium 實跑） | 失敗→常駐錯誤→重試→成功全鏈 |
| 每顆暫存器標示對照狀態：已對照→綠色 chip＋出處全文；未對照→虛線 chip（**設計如此**：未對照不再重複印長句，避免 17 行雜訊） | test_ui.py::test_unverified_register_says_so_on_audit_page＋tools/preview.py 截圖 8 | 兩態 |
| spec 層級顯示「已對照官方 X/N」比例（Spec 管理卡片與 Spec 全文標頭同一支渲染） | test_ui.py::test_verify_state_rendered_from_single_source＋截圖 4/8 | 全對照／部分／完全未對照三態 |

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
| 查詢歷史限本次執行、換 spec 即作廢（UI 行為） | tools/preview.py 截圖＋第 11 節人工清單 | — |

## 7. App 狀態（spec 集合管理）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| 內建載入、last_spec 記憶、預設選第一個 | test_app_state.py::test_load_builtin_…、_last_spec_restored | — |
| 外部 spec 加入/移除/重載、內建不可移除、同名衝突加 `~2` 後綴（**設計如此**） | ::test_add_and_remove_external、_external_id_collision_…、_reload_keeps_external | 各狀態轉移 |
| **同一路徑重複載入＝就地重新讀取**（**設計如此**：不產生第二張卡——cfg 去重本來就表明同檔只記一次；同時滿足「改了 .md 再載入＝更新」）。修正前重加同檔會出現兩張卡共用一條 cfg 路徑，移除其一另一張成孤兒（2026-09-03 實證的狀態不一致） | ::test_readd_same_external_path_reloads_in_place（重加＝同 id、內容更新、移除後零孤兒） | 加→改檔→重加→移除→重載全鏈 |

## 8. UI（HTML/CSS/JS 靜態保證）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| 佔位符全部替換、主題屬性正確 | test_ui.py::test_no_leftover_placeholders、_light_theme_attr_empty | 4 個佔位符 |
| 深色 tokens ⊆ 淺色 tokens（單一色票來源） | ::test_theme_tokens_complete | 全 token 集合比對 |
| **用到的每個 var(--c-\*) 都有定義**（打錯 token 名顏色會靜默消失） | ::test_every_used_css_token_is_defined_in_light_root | HTML/CSS/JS 全文掃描 |
| **每個 inline handler 都有對應函式**（改名/刪函式把按鈕改壞在此被抓） | ::test_every_inline_handler_has_declared_function | 全部 onclick/oninput/onchange |
| JS 引用的靜態元素 id 都存在 | ::test_every_getelementbyid_target_exists | 全部 getElementById |
| spec 下拉選單與 Spec 管理依廠商分組（**設計如此**：共用 groupSpecsByVendor，不准各分各的） | tools/preview.py 截圖＋第 11 節人工清單 | ARM／Andes／外部載入三組 |
| 六個視圖都有導覽入口與 render 分支 | ::test_all_views_have_render_branch_and_nav_entry | overview/regs/lookup/hex/specdoc/specs |
| **JS 呼叫的每個 api 方法都存在於 Python Api**（橋接兩端同步） | ::test_api_methods_called_from_js_exist_in_python | 全部 api() 呼叫 × AST 解析 Api 類 |
| Python 實際輸出的內嵌 JS 語法正確 | ::test_js_syntax_with_node（node --check） | head＋body 兩段 script |
| 保留位降噪：與 Reset 相同的保留／未定義列預設隱藏；**值≠Reset 或未定義非 0 的保留位強制顯示**（**設計如此**：安全網，不准藏掉異常）；隱藏數提示列可點擊展開；bit ruler 永遠顯示全部位元；**Spec 全文不套用隱藏**（稽核要完整，**設計如此**） | tools/preview.py 截圖＋第 11 節人工清單 | 展開 SCTLR 目視（14 個安靜保留位收起、藍色異常位保留） |
| 渲染共用（防改 A 壞 B）：暫存器展開與快速反查共用 registerBlock()；狀態 chip 共用 statusChipHtml()（**設計如此**：同一資訊只准一份渲染程式，見 CLAUDE.md 不變條件 12） | 程式結構＋test_every_inline_handler_…（改名即紅） | — |
| **bit ruler 點擊在兩條路徑都要動**：暫存器頁（ri=數字）與快速反查頁（ri='lk' 字串）點欄位都必須捲動＋閃爍對應列——產生的 onclick 參數必加引號（字串 ri 少引號＝ReferenceError，點擊整組沉默失效；2026-09-02 review 實測抓到） | test_ui_interactions.py::test_bit_ruler_click_focuses_field_on_both_pages（Chromium 實點＋pageerror 必須為零） | 數字／字串 ri 兩路徑實點 |
| 搜尋輸入：S.q 逐鍵即時更新（不丟字），整頁重繪合併到停止輸入後 120ms（**設計如此**：大 spec＋全部展開時逐鍵重繪會卡輸入） | test_ui_interactions.py::test_search_filters_after_debounce（實際打字→過濾端到端） | 打字＋等待＞120ms→結果過濾且目標可見 |
| 長文降噪（**設計如此**：資訊不刪除、預設收斂）：收合列的暫存器說明夾 2 行（展開該列即還原全文）；總覽 Source、Spec 卡查核狀態、Spec 全文查核狀態／來源夾 3 行、點擊展開收合。Spec 全文的**欄位表**不受任何夾行影響（稽核完整性） | test_ui.py::test_long_prose_is_clamped_with_expand_toggle（4 個 clamp 位置計數）＋test_ui_interactions.py::test_clamped_prose_expands_on_click（實點展開/收合）＋tools/preview.py 截圖 | 4 個 clamp 位置＋點擊兩態 |
| tools/preview.py 的 `--out` 接受相對路徑（先 resolve 再 as_uri，否則截圖階段炸 ValueError） | test_ui.py::test_preview_tool_accepts_relative_out_dir | 相對路徑輸出落點＋訊息為絕對路徑 |
| 真實瀏覽器渲染（五視圖×深淺色、console error 即失敗） | `PYTHONPATH=. python tools/preview.py`（改 UI 後必跑；產 11 張截圖） | overview/regs(展開)/lookup/hex/specs/specdoc(解析後+原文)×兩主題 |

## 9. 打包與啟動診斷（單元測試看不到的死角）

單元測試讀的是 repo 目錄，使用者跑的是 exe —— 這一節專門補這段落差。
（2026-08-23 現場回報「找不到任何 spec」而測試全綠，就是這個死角。）

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| spec 搜尋路徑：打包內 specs/ ＋ exe 旁 specs/，開發模式去重（**設計如此**：exe 旁的目錄同時是「免重 build 加 spec」與資源解壓失敗的救援路徑） | test_packaging.py::test_spec_dirs_dev_mode_is_deduped | 開發／打包兩種模式 |
| 每個搜尋目錄都留下掃描紀錄（dir／exists／loaded／names） | ::test_scan_records_every_searched_dir | 全目錄逐一 |
| 目錄不存在照實回報 exists=False，不丟例外 | ::test_scan_reports_missing_dir_without_raising | 缺目錄路徑 |
| **打包後的 exe 自我驗證**：`--selftest` 載得到 ≥4 份 spec、零警告 → exit 0；載不到 → exit 1（CI 據此擋下 Release） | ::test_selftest_exits_zero_and_reports_four_specs、_fails_when_no_specs＋CI「Self-test the packaged EXE」步驟 | 正常／空目錄兩態；CI 每次 build 用真實 exe 跑 |
| **每個 bridge 方法都掛 @_guard**（**設計如此**：例外必須進 log 並回可讀訊息，不准變成空畫面） | ::test_every_public_api_method_is_guarded（AST 掃描，新增方法忘了掛就紅） | Api 全部公開方法 |
| get_init 一定帶 diag（scan／log_path／frozen／spec_count） | ::test_get_init_returns_diagnostics | 必要欄位逐一 |
| 「找不到 spec」畫面顯示完整診斷表 | tools/preview.py 的 11_nospec_diag.png | 目錄不存在的情境 |
| **不載入任何外部資源**（封閉網路啟動不卡） | test_ui.py::test_no_external_resources | HTML 全文掃描 |

### 9.1 bridge 初始化競態（2026-08-24 現場事故）

pywebview 先注入 `window.pywebview = {api: {}}`，之後才把方法掛上去。
前端若只檢查 `pywebview.api` 存在就初始化，會落在空窗期取到 undefined 的
`get_init`，promise 被拒後 `S.inited` 已 latch，之後的 `pywebviewready`
也不會重試 —— 結果就是畫面永遠停在「找不到任何 CPU spec」、沒有 toast、
連診斷表都不出現。

| 行為 | 驗證 | 窮舉範圍 |
|---|---|---|
| `bridgeReady()` 必須確認 `pywebview.api.get_init` **真的是 function**（**設計如此**：只檢查 api 物件＝重現事故） | test_bridge_init.py::test_bridge_ready_checks_actual_method | 靜態掃描，CI 一定跑 |
| `init()` 在 bridge 未就緒時不得先 latch `S.inited` | ::test_init_does_not_latch_before_bridge_ready | 程式結構斷言 |
| 輪詢有逾時，逾時把原因寫進畫面而非無限空白 | ::test_poll_has_timeout_and_reports_failure | — |
| `handle()` 在 `ok:false` 時仍保留 diag（**設計如此**：出事時診斷不能一起消失） | ::test_handle_keeps_diag_on_failure | 程式結構斷言 |
| **真的重演兩段式注入**：空窗期 0／400／1200 ms，UI 最後都必須拿到 spec | ::test_ui_loads_despite_two_phase_bridge_injection（Chromium 實跑；已驗證還原修正就會紅） | 3 種空窗期 |
| 失敗原因常駐顯示在空狀態（toast 會消失） | ::test_handle_keeps_diag_on_failure ＋ noSpecHtml 的 lastError 區塊 | — |

## 10. 報告匯出

| 行為 | 驗證 |
|---|---|
| 標題/統計/enum 意義進報告、only_differs 過濾 | test_analyzer.py::test_report_markdown |
| 表格 cell 的「\|」跳脫（enum 意義可含直線） | ::test_report_escapes_pipe_in_enum_label |
| 無 bin 措辭、零差異時 only_differs 為空表 | ::test_report_no_bin_and_no_diff_wording |

## 11. 無法自動化的部分 —— Windows 實機檢查清單

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

## 12. 新增功能的規則

新功能（或行為變更）**必須**：
1. 在本檔加追溯列（含窮舉範圍說明）；
2. 加對應測試（能窮舉就窮舉）；
3. 刻意的取捨標「設計如此」並寫理由 —— 這是防止之後被誤修的鎖。
