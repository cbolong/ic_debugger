# SPEC_REVIEW_LOG — 三方交叉審查決議紀錄

本檔是 `specs/` 四份 CPU spec 與外部審查（ChatGPT／OpenAI）交叉檢查的**決議與待辦總帳**。
目的：讓每一輪審查的結論不散失，並明確區分「已套用」「待原文親驗」「已駁回」。

- 審查輪次：R1＝2026-08-24 自我稽核；R2＝ChatGPT 第二輪審查；R2R＝Claude 複驗回覆；R3＝OpenAI 第三輪審查；R3R＝2026-08-29 套用；R4＝OpenAI 第四輪獨立複驗（直接抽查 repo／CI／TRM）；R4R＝2026-08-29 第四輪套用；R5＝OpenAI Codex 第五輪複驗（帶 TRM 原文逐欄轉錄）；R5R＝2026-08-30 第五輪套用；R6＝OpenAI Codex 第六輪複驗；R6R＝2026-08-30 第六輪套用；R7＝OpenAI Codex 第七輪複驗；R7R＝2026-08-30 第七輪套用；R8＝OpenAI Codex 第八輪複驗；R8R＝2026-08-30 第八輪套用；R9＝OpenAI Codex 第九輪複驗；R9R＝2026-08-30 第九輪套用；R10＝OpenAI Codex 第十輪複驗（原報告未送達，內容由其重複回覆確認函重述）；R10R＝2026-08-30 第十輪套用；R11＝OpenAI Codex 第十一輪複驗；R11R＝2026-08-30 第十一輪套用；R12＝OpenAI Codex 第十二輪複驗；R12R＝2026-08-31 第十二輪套用；R13＝OpenAI Codex 第十三輪複驗（**首輪帶官方 0460D 直接親驗**）；R13R＝2026-08-31 第十三輪套用；Final＝OpenAI Codex 結案前最終驗收（維護者已裁示收束，僅一次性收尾）；FinalR＝2026-08-31 一次性收尾套用（單一 cleanup commit，**迴圈就此結案**）。**被後續決議推翻的舊列以「SUPERSEDED by #n」開頭標記；僅部分修訂的以「AMENDED by #n」標記——單獨引用舊列前先看標記**
- 證據分層定義（Verified 欄位的授予標準）：
  1. **親驗一手**：Claude 直接開啟一手來源逐欄核對（唯一可寫 `- Verified:` 的層級）
  2. **審查轉錄**：審查方轉錄自 TRM，Claude 無法在工作環境開啟原文——內容可寫入表格，但**不給 Verified**，
     Description 必須標「審查轉錄…待親驗」
  3. **佐證**：第三方程式碼（Xilinx BSP、Linux kernel、TF-A）——只用於支持方向，不決定完整佈局
- 工作環境限制（2026-08-29 查核）：documentation-service.arm.com／andestech.com 於 Claude 工作環境不可達；
  GitHub raw／git 可達。此為環境紀錄，非 spec 永久屬性（依 R3 修正 7 移出 spec 本體，記於此）。

## 一、已套用的決議（#1–26＝R3R；#27–33＝R4R；#34–40＝R5R；#41–47＝R6R；#48–50＝R7R；#51–53＝R8R；#54–56＝R9R；#57–59＝R10R；#60–61＝R11R；#62–63＝R12R；#64–68＝R13R；#69–71＝FinalR）

| # | 檔案 | 決議 | 證據層級 |
|---|---|---|---|
| 1 | cortex_r5 | ATCMRR/BTCMRR 編碼互換修正：ATCM=c9,c1,1、BTCM=c9,c1,0 | 親驗（Xilinx xreg_cortexr5.h）＋審查（DDI 0460D Table 4-43/4-44） |
| 2 | cortex_r5 | ATCMRR/BTCMRR 補 Size[6:2]、[11:7] UNP/SBZ | 審查轉錄＋Xilinx 佐證 |
| 3 | cortex_r5 | DFSR/IFSR 欄位 Access RO→RW（官方屬性「32-bit RW register」） | 親驗（DDI 0406C.d §B6.1） |
| 4 | cortex_r5 | FPEXC 產品化：31 RAZ／30 EN／29 DEX／28:0 RAZ | 審查轉錄（Table 11-6）＋Linux FPEXC_DEX 佐證 |
| 5 | cortex_r5 | FPSCR trap enable（15,12:8）→RO/0（VFPv3 RAZ/WI）；QC/AHP→RO＋產品註 | 親驗（0406C VFPv3 規則）＋審查轉錄 |
| 6 | cortex_r5 | RGNR [7:0]→[3:0]（R5 為 12/16 區） | 親驗（0406C 欄寬規則）＋審查 |
| 7 | cortex_r5 | ACTLR 填入完整 29 欄產品表 | 審查轉錄（Table 4-25），無 Verified |
| 8 | cortex_r5 | ADFSR/AIFSR 填入產品欄位表（CacheWay/Side/Index…） | 審查轉錄（Table 4-31/4-32），無 Verified |
| 9 | cortex_r5 | **SUPERSEDED by #34/#41**——SCTLR FI/RR/Z 產品固定行為以註記呈現（Access 未改，待原文） | 審查轉錄 |
| 10 | cortex_r5 | CPACR ASEDIS/D32DIS 改 R5F 產品語意（VFPv3-D16→兩位恆 1） | 審查轉錄 |
| 11 | cortex_r5 | CSSELR 產品註（僅 L1；產品層 Level 唯讀） | 審查轉錄 |
| 12 | cortex_r5 | 新增 MVFR0/MVFR1（62 顆） | 親驗（0406C §B6.1） |
| 13 | cortex_a55 | SCTLR_EL1[29:28]→RES1（無 FEAT_LSMAOC） | 親驗（Linux SCTLR_EL1_RES1＋架構規則）＋審查（Figure 3-162） |
| 14 | cortex_a55 | CCSIDR 補 WT/WB/RA/WA[31:28] | 親驗（0406C 同佈局）＋審查（§3.2.23／Figure 3-99，R3 更正圖號） |
| 15 | cortex_a55 | **SUPERSEDED by #38/#44**——AFSR0/1_EL1→RES0（消除表格與說明矛盾；後續改為上半 Reserved／下半 RES0 分層） | 親驗（自檔矛盾）＋審查 |
| 16 | cortex_a55 | CSSELR_EL1.TnD→RES0（A55 無 MTE） | 同上 |
| 17 | cortex_a55 | REVIDR_EL1 移除 ARMv7 alias-to-MIDR 語意（AArch64 無此行為） | 親驗（語意錯置源頭＝0406C v7 原文） |
| 18 | cortex_a55 | ID 暫存器逐欄標「本核心（v8.2）讀 0」（位置不變；~60 欄） | 共識（R2R/R3 分類：產品存在性，非位置錯誤） |
| 19 | cortex_a55 | CPUECTLR/CPUPWRCTLR 填入完整產品表；CPUACTLR 加「Arm internal use，不得修改」警語 | 審查轉錄（§3.2.30/3.2.35/3.2.28）＋TF-A 具名位親驗 |
| 20 | cortex_a55 | CNTKCTL EL0PTEN/EL0VTEN 加「v8.0 基線」註（R2 的 A55-09 為誤報，三方確認撤回） | 親驗（0406C B8 PL0PTEN/PL0VTEN） |
| 21 | n25/n45 | 刪除過期「尚未收錄 Andes CSR」TODO 塊（與後文矛盾） | 自檔矛盾 |
| 22 | n45 | mcounterovf 寫 1 清除→**寫 0 清除（W0C）**；n25 明標 W1C | 親驗（pinned QEMU write_mcounterovf） |
| 23 | n25/n45 | 全部 QEMU 出處釘 commit 3290262（ast-v5_4_2-release） | 親驗（pinned 標頭與遮罩逐項比對一致） |
| 24 | n25/n45 | udcause 存在條件修正（predicate=any，與 N 擴充無關） | 親驗（pinned csr_andes.c） |
| 25 | n25/n45 | Status 改為「QEMU 模型 profile」定位＋priv 1.12／mvendorid 0x31E 期望值註 | 親驗（pinned cpu.c） |
| 26 | n45 | Status 記錄官網世代衝突（RV32GCB／M-U-S／PMP32／PMA16 vs QEMU 模型） | R3 確認之來源衝突 |
| 27 | cortex_a55 | **SUPERSEDED by #36**——AIDR_EL1 版面修正：[63:32] RES0＋[31:0] RES0（上半部後經 #36 更正為 RESERVED）——結案 R2 A55-04／R4-01 | 審查轉錄（§3.2.14／Figure 3-91） |
| 28 | cortex_a55 | ID_AA64MMFR0 TGran4/TGran64 改雙層描述（架構 0＝支援＋產品圖 Figure 3-127 併標 RES0）；R3R 反問 1 結案 | 親驗（sail／0406C 架構側）＋審查轉錄（Figure 3-127） |
| 29 | cortex_a55 | CPUACTLR_EL1 內部保留位 Access RO→RW；Access 欄明定為硬體屬性（R4-04） | 審查轉錄（§3.2.28 accessibility）＋TF-A MSR 寫入佐證 |
| 30 | cortex_r5 | 檔頭清理：Source「僅 TCMTR」、MVFR 待補註解、「全部可讀 CP15」範圍語（R4-05） | 自檔矛盾 |
| 31 | tools | sample_r5.bin FPSID 0x41023154→0x41023153（對齊 Table 11-7 轉錄值；舊值無出處，QEMU r5f 亦未定義 FPSID）（R4-06） | 審查轉錄 |
| 32 | ci | auto-build 安裝 playwright＋chromium：3 條 bridge 測試 CI 不再 skip，CI 與本機跑同一套全量測試（R4-03） | 環境 |
| 33 | 本檔＋SPEC_FORMAT | ID_ISAR2 自待回填清單改列 TRM 內部衝突（R4-02，見第二節）；SPEC_FORMAT 明定 Access＝硬體存取屬性 | 親驗（0406C MemHint 編碼＋QEMU cpu32.c）＋審查轉錄（Table 4-17） |
| 34 | cortex_r5 | **AMENDED by #43**（reset 證據規則後續增列 Figure B6-1 reset 圖明文一類）——SCTLR 套用 Table 4-24 產品 overlay（R5-01）：AFE/TRE 具名、保留段依產品分組（[23:22]/[9:7]/[6:3]…）、FI/Z 改 RO（SBO）、RR 補明文 reset 0、IE/NMFI 明文 RO；**刪除無出處的「依 CFGBR 接腳」**；SBO/SBZ 玻璃屋定義（硬體忽略寫入＋軟體寫錯須預期 UNPREDICTABLE）0406C.d 親驗；Reset 只在架構 RAO/RAZ 親驗或 Table 4-24 明文時填 | 審查轉錄（§4.3.16／Table 4-24）＋親驗（0406C 玻璃屋與架構層讀值） |
| 35 | cortex_r5 | DFSR/IFSR 改產品欄名（R5-02）：ExT→SD、WnR→RW、FS[4]→S、FS[3:0]→Status，拆出 [9:8] 與 Domain[7:4]；DFSR[9:8] 明文 RAZ/WI 填 reset 0、IFSR[9:8] 無明文不填；SD 為 external abort 子分類、不併入 S:Status 主編碼 | 審查轉錄（§4.3.20／Figure 4-31/4-32／Table 4-28/4-29/4-30） |
| 36 | cortex_a55 | AIDR_EL1 上半部 RES0→**RESERVED**（Figure 3-91 原文；更正決議 #27 的過度轉譯——Reserved 與 RES0 不可無佐證互換）；Reset 補 0x0（Table 3-49 Type=RO/Reset=0 轉錄）（R5-03） | 審查轉錄 |
| 37 | cortex_a55 | REVIDR_EL1 上半部 RES0→RESERVED（Figure 3-160）；Reset 補 0x0（Table 3-49 轉錄）（R5-03） | 審查轉錄 |
| 38 | cortex_a55 | AFSR0/1_EL1 上半部 RES0→RESERVED（Figure 3-85/3-88）；Description 分層明寫「暫存器介面 RW（Table 3-54）、產品內容無可寫資訊」（R5-04） | 審查轉錄 |
| 39 | 本檔 | QEMU 佐證釘 commit `d2e570cc0f97b936902a5b1b86b73c0f5998b475`（qemu-project/qemu target/arm/tcg/cpu32.c 親驗），並標示該模型 MIDR=0x411fc153＝**r1p3**——僅作 r1p2 推導的交叉佐證，不取代 DDI 0460D（R5-05） | 親驗（pinned 原始碼） |
| 40 | tests | 新增 R5R 鎖定測試 5 條＋改寫 AIDR 鎖與 A55 reset 例外清單（見 tests/test_specs_official.py） | — |
| 41 | cortex_r5 | SCTLR enum 產品化（R6-01）：刪 FI/Z 的通用 ARMv7 開關 enum（產品上此二位不控制功能）、RR enum 改「兩值皆 random replacement」 | 審查轉錄（Table 4-24） |
| 42 | cortex_r5 | DFSR/IFSR Status enum 對齊 Table 4-28（R6-02）：刪 R5 上為 Reserved 的 Lockdown（10100）與 coprocessor abort（11010）；IFSR 補非同步外部中止（10110）與非同步同位/ECC（11000）；同位錯誤改稱同位/ECC；未列組合皆保留 | 審查轉錄（Table 4-28 共用編碼表） |
| 43 | cortex_r5 | SCTLR reset 補 FI=0、BR=0、[6:3]=0b1111；Z 維持 `-`（R6-03）——依 0406C.d Figure B6-1（PMSAv7 reset 圖）逐位親驗＋CP15BEN 條文（實作→reset 1／未實作→RAO/WI）；證據規則補「reset 圖明文」一類 | 親驗（Figure B6-1＋§B6.1 條文） |
| 44 | cortex_a55 | AFSR0/1 上半 RESERVED 的 reset 0→`-`（R6-04）：Reserved 無讀值保證，與 #36 的原則一致套用；下半 RES0 維持 0 | 自我一致性（R6 指正） |
| 45 | cortex_r5 | DFAR/IFAR 的「見 DFSR.FS／IFSR.FS」失效引用改為 S:Status＋SD 分層說明（R6-05） | 自檔矛盾 |
| 46 | cortex_r5＋本檔 | CFGBR 自 live spec 完全移除（R6-06 表態採納）：歷史只留本檔（#34 與本列）；A55/R5 檔頭補記 R5R/R6R 修正範圍、舊決議 #9/#15/#27 標 SUPERSEDED（R6-07） | 慣例決策 |
| 47 | cortex_a55＋tools | REVIDR_EL1[31:0] 欄名改 IMPDEF（照 Figure 3-160 原圖標籤，R6-09）；sample 產生器的 SCTLR.Z 說明改歸因 ACTLR.BP（R6-08） | 審查轉錄＋慣例 |
| 48 | cortex_r5 | DFSR/IFSR Status enum 的 FAR 狀態對齊 Table 4-28（R7-01；來源敘述經 R8-02 精修）：Debug Event→FAR 保持原值（Unchanged）、非同步外部中止與非同步同位/ECC→UNPREDICTABLE、同步同位/ECC→有效。舊 UNKNOWN 的架構層**直接**來源只涵蓋：DFSR 的 debug／非同步外部中止／非同步 parity（Table B5-8 明文 UNKNOWN）與 IFSR 的 debug event（Table B5-7 明文 UNKNOWN）——**IFSR 的 10110/11000 不在 Table B5-7**（該表未列即 Reserved；2026-08-30 親驗 B5-7/B5-8 原文確認），舊版對其套 UNKNOWN 屬未標示的推論。本輪起產品層一律以 Table 4-28 為準 | 審查轉錄（Table 4-28 FAR 欄）＋親驗（B5-7/B5-8 涵蓋範圍） |
| 49 | cortex_r5 | SCTLR.Z 的 Figure B6-1 footnote 記號修正：裸 †→**(†)**，並改寫為完整句（R7-03）。字元級 PDF 抽取對複合上標符號不可靠（本輪座標驗證：Z 格數字 0＝(†) 的 otherwise-reset、CP15BEN 格 (‡)＋數字 1 對照吻合），以完整圖例句為準 | 親驗（座標級複核） |
| 50 | tests＋本檔 | **AMENDED by #51**（「逐項鎖八個 full S:Status＋FAR 狀態」屬過度主張——R8-01 證實 R7 版實際僅鎖整列 substring，S 分支歸屬鎖由 #51 補正；本列其餘兩項不受影響）——R7-02/04/05：fault enum 測試改名 test_r5_fault_status_and_far_semantics_match_table_4_28 並逐項鎖八個 full S:Status＋FAR 狀態＋Status label 禁 UNKNOWN；superseded 測試加 #34 AMENDED 斷言；REVIDR 測試 docstring 改 IMPDEF | — |
| 51 | tests | **AMENDED by #54/#57**（「再驗 fault/FAR」與「另一側必為保留」相對當時實作屬過度主張——FAR 名稱與三態互斥由 #54 補正（R9-01）、reserved 側當時僅驗子字串、exact 鎖由 #57 補正（R10-01）；S 分支歸屬鎖本身不受影響）——fault 測試改 **S 分支歸屬鎖**（R8-01）：檢查器逐 full encoding 先切出 S=n 分支再驗 fault/FAR、同步項禁「非同步」子字串誤中、單編碼列的另一側必為保留；另加負向測試——把真實 enum 的 S=0/S=1 整組對調後檢查器必須失敗 | — |
| 52 | 本檔 | #48 來源敘述精修（R8-02）：分開 DFSR（B5-8 明文）／IFSR debug（B5-7 明文）／IFSR 10110/11000（B5-7 未列＝Reserved，舊 UNKNOWN 屬推論）三種來源——B5-7/B5-8 涵蓋範圍本輪親驗 | 親驗 |
| 53 | 本檔＋cortex_r5 | 檔頭輪次補 R7/R7R/R8/R8R（R8-03）；DFSR/IFSR 的 Verified 邊界明文——Verified 僅涵蓋架構層位置與 B5-7/B5-8 基線，現行 Table 4-28 產品 enum 不在其內（R8-04） | 慣例 |
| 54 | tests | fault 檢查器補 FAR 完整語意鎖（R9-01）：三種 FAR 狀態都必須帶正確 FAR 名（DFAR/IFAR，錯名禁入）且三態互斥（有效／保持原值／UNPREDICTABLE 不得同分支並存）、每列結構鎖恰為 S=0/S=1 兩分支；加兩條永久負向測試——DFAR↔IFAR 錯名必敗（雙向）、矛盾狀態並存必敗（雙向） | — |
| 55 | 本檔＋tests | #50 標 AMENDED by #51（R9-02）：「逐項鎖八個 full S:Status」經 R8-01 證明過度主張，僅 fault 測試部分被 #51 修訂（#34 斷言、REVIDR docstring 兩項仍成立）；review-log 標記測試加 #50 斷言 | 自我一致性 |
| 56 | 本檔 | 頁碼引用規範（R9-03）：PDF 頁碼引用一律標「viewer 1-based 頁＋印刷頁碼」，程式 zero-based 索引需明標。R8R 回覆的 B5-7/B5-8「p1762–1763」實為 PyMuPDF zero-based 索引——正確為 viewer 頁 1763–1764／印刷頁 B5-1763（Table B5-7）與 B5-1764（Table B5-8；正文明文「Table B5-8 on page B5-1764」），本輪親驗更正 | 親驗 |
| 57 | tests | reserved 分支改 **exact 鎖**（R10-01）：單編碼列的另一側必須恰等於「S=n＝保留」——舊版僅驗「保留」子字串，「S=1＝保留，但同時聲稱背景故障（FAR 為 UNPREDICTABLE）」也放行（DFSR/IFSR 都重現）；加永久負向測試 reserved 側摻語意必敗 | — |
| 58 | 本檔＋tests | #51 標 AMENDED by #54/#57（R10-02）：其「驗 fault/FAR」「另一側必為保留」相對當時實作屬過度主張，分別由 #54（R9-01）/#57（R10-01）補正；review-log 標記測試加 #51→#54/#57 斷言 | 自我一致性 |
| 59 | 本檔 | **AMENDED by #61**（master 僅作發現 URL——不可變重現來源改 commit/blob pin，見 #61）——我方 0406C.d 的 provenance 記錄（R10-03）：來源＝GitHub 鏡像 lisider/my_book（master）`Architecture/arm/armv7-cortex-ar/DDI0406C_d_armv7ar_arm.pdf`（2026-08-28 sparse checkout 取得；2026-08-30 重抓同 URL 雜湊相符）；18,620,001 bytes、SHA-256 `b6c60d1b04ce…e952a094`、PDF 1.7、2720 頁、封面 DDI 0406C.d／ID040418、creationDate 2018-04-04T19:05:24Z、modDate 2018-05-28+08:00、producer Acrobat Distiller 8.3.1。**信任分層**：鏡像位元組未經 arm.com 背書＝容器層低於官方下載；內容層主張迄今均經 Codex 官方建置（SHA-256 294668ae…）獨立覆核相符，僅憑我方副本成立的主張如有應個別標註待官方複驗 | 親驗（metadata＋重抓）＋鏡像 |
| 60 | tests | **AMENDED by #62**（「fault 類別互斥」當時僅涵蓋中文 canonical token——英文官方術語（Alignment fault／Reserved encoding）可繞過；中英雙語 alias＋NFKC/casefold 正規化由 #62 補正）——active 分支補 **fault 類別互斥鎖**（R11-01）：以 allowlist token 依序剝離（非同步先於同步、殘文再驗防同類別重複）——每個 active 分支恰好解析出一個且等於預期的 fault 類別、禁「保留」；舊版只驗預期名存在，「背景＋對齊」「active 兼保留」四型變異都放行（DFSR/IFSR 都重現）。加永久負向測試（兩型×兩顆）；16 個真實 active 分支 dry-run 零誤傷 | — |
| 61 | 本檔＋tests | 0406C.d 鏡像 provenance 釘 commit（R11-02）：commit `b7eccdd03f6442d9d4597a89e70fa8f8fb7167cb`、blob `81171e821320cfbbe8c1ac0a6f544e3068a8ca96`（blob 以 git 演算法自本地檔重算相符）；commit-pinned raw URL 2026-08-30 實抓 SHA-256 仍為 `b6c60d1b…`（與 master URL、本地檔三方一致）。master 僅作發現 URL，不得作唯一可重現來源；加 provenance 鎖定測試。**R12-02 補全（本列自包含、一鍵可重現）**：完整 pinned URL＝`https://raw.githubusercontent.com/lisider/my_book/b7eccdd03f6442d9d4597a89e70fa8f8fb7167cb/Architecture/arm/armv7-cortex-ar/DDI0406C_d_armv7ar_arm.pdf`、完整 SHA-256＝`b6c60d1b04ce04769f7a22abd71614251c783fcc410c7f1e9aa0cf19e952a094` | 親驗（blob 重算＋pinned 重抓） |
| 62 | tests | **AMENDED by #64**（「英文名取 DDI 0406C.d／0460D 表格用語」當時漏掉五個正式名——0460D Table 4-28 Sources 的 Alignment/Background/Permission 單字短名與 0406C.d 的 Memory access (a)synchronous parity error，10 個變異放行；#64 補全並改詞界線 regex）——active 排他鎖擴為**中英雙語 canonical alias**（R12-01）：8 類別×中英 alias 經 NFKC＋casefold 正規化、依長→短剝離至定點（計入全部出現次數）、命中一律映回中文 canonical；active 分支禁正規化後的「保留」與「reserved」。英文官方術語 mutation（Alignment fault／Reserved encoding，含大小寫變體）修正前放行（DFSR/IFSR 都重現）、修正後必敗（bilingual 負向測試永久化）；16 個真實分支 dry-run 零誤傷。**保證範圍明文＝canonical 中英術語排他，非任意同義詞的語意理解** | — |
| 63 | 本檔＋tests | provenance 決議自包含化（R12-02）：#61 直接補入完整 commit-pinned raw URL 與完整 SHA-256；鎖定測試改名 test_arm_mirror_provenance_row61_is_self_contained_and_commit_pinned 並**定位 #61 列**逐項斷言（commit／blob／URL／SHA-256），不再全檔搜尋；#59→#61 AMENDED 斷言保留 | 慣例 |
| 64 | tests | alias 補齊官方詞彙＋詞界線（R13-01）：0460D Table 4-28 Sources 單字短名（Alignment/Background/Permission）與 0406C.d 的 Memory access (a)synchronous parity error 入 alias（後者 2026-08-31 自本地 0406C.d B5-7/B5-8 頁面親驗）；比對改詞界線 regex（前後不得緊鄰 [a-z0-9]——backgrounded/realignments 不誤中、中文緊鄰英文仍抓到）；官方詞彙全量負向測試（19 詞×DFSR/IFSR＝38 變異，修正前其中 10 個放行）＋詞界線良性反證 | 親驗（0406C 詞彙）＋審查轉錄（0460D 詞彙） |
| 65 | 本檔 | 官方文件通道狀態更新（R13-02）：Codex 2026-08-31 實測 developer.arm.com／documentation-service.arm.com 已可下載——DDI 0460D（download `https://documentation-service.arm.com/static/5f04288cdbdee951c1cd8969`、檔名 DDI0460D_cortex_r5_r1p2_trm.pdf、3,268,393 bytes、468 頁、SHA-256 `da00857f6e3d429354e8606bc1de2012782389dc3da0be829a19f0f680c2188b`）與 100442_0200_02_en（download `https://documentation-service.arm.com/static/649ac6d4df6cd61d528c2bf1`、4,680,444 bytes）——以上數值為 Codex 回報之審查轉錄。我方沙箱同日重試：代理對 documentation-service.arm.com／infocenter.arm.com CONNECT 回 403 host_not_allowed（出口 allowlist 政策，非 ARM 端問題）。**解鎖路徑：使用者將官方 PDF 放入 repo（或開放網域）即可親驗升級** | 審查轉錄＋親驗（我方 403 實測） |
| 66 | cortex_r5 | ACTLR 依 Table 4-25 修正（R13-03，審查轉錄）：FRCDIS＝停用 fetch-rate control（舊「Fault 路徑組合邏輯」誤譯）、DNCH＝停用 AXI master 對 non-cacheable 的 data forwarding、FDSnS＝MPU 關閉時強制 D-side Normal Non-cacheable 為 Non-shared（舊 write-through 語意錯置）、sMOV＝divide 不亂序完成；[27:25] 收斂為 ECC 檢查致能（reset 依 PARECCENRAMm）；[18] 自 RES0/0 回退 RESERVED/`-`（僅 SBZ）；明文 reset 回填（[31:28]/[24:19]/[17]/[14:6] 各 0、BP=0b00、CEC=0b100）、[2:0] reset 依 ERRENRAMm | 審查轉錄（Table 4-25） |
| 67 | cortex_r5 | ADFSR/AIFSR 依 Table 4-31/4-32 修正（R13-04，審查轉錄）：三段保留位（[31:28]/[19:14]/[4:0]）自 RES0/0 回退 RESERVED/`-`（僅 SBZ）；CacheWay/Index 補「僅 data cache store 同位/ECC 錯誤時有效」註腳、AIFSR.Index＝SBZ（舊版無條件解讀屬實質診斷錯誤）；兩顆補整體有效性（僅 DFSR/IFSR 回報同位/ECC 時內容有效）；Side/SideExt 補八組 SideExt:Side 組合表（0:00 Cache/AXIM…1:10 AHB 周邊埠） | 審查轉錄（Table 4-31/4-32） |
| 68 | cortex_r5 | ATCMRR/BTCMRR 依 Table 4-43/4-44 修正（R13-05，審查轉錄）：[11:7]＝讀取不可預期＋寫入 SBZ（不得稱 RES0——與「讀為 0」語意衝突）；bit1 自 RES0/0 回退 RESERVED/`-`；Size 完整 enum（0＝無 TCM、3–14 級距含 **14=8MB**，未列值 1、2、15–31 保留）；Base reset 依 LOCZRAMAm（ATCM：=1 為 0／=0 實作定義；BTCM 相反）、En reset 依 INITRAMAm/Bm、未實作該 TCM 時 En 為 RAZ | 審查轉錄（Table 4-43/4-44） |
| 69 | cortex_r5 | AIFSR 語意收尾（FINAL-01）：CacheWay 欄把 Table 4-31 註腳的推論寫完——僅 data cache store 同位/ECC 錯誤時有效，AIFSR（指令側）不存在此情境，**讀值為 Unpredictable、不得解讀**；暫存器摘要同步移除「cache way」作為可用定位資訊（改列 CacheWay=Unpredictable、Index=SBZ）。測試補鎖（欄位 Unpredictable＋摘要正反兩向）並先對舊文字驗證必敗 | 審查轉錄（Table 4-31 註腳）＋邏輯推論（AIFSR 為指令側） |
| 70 | cortex_r5 | ACTLR pin-dependent reset 逐欄對應（FINAL-02）：六列自匯流排式 `[2:0]` 改 exact mapping——B1TCMPCEN[27]←PARECCENRAMm[2]、B0TCMPCEN[26]←PARECCENRAMm[1]、ATCMPCEN[25]←PARECCENRAMm[0]、B1TCMECEN[2]←ERRENRAMm[2]、B0TCMECEN[1]←ERRENRAMm[1]、ATCMECEN[0]←ERRENRAMm[0]。資料驅動測試逐欄鎖 exact pin＋禁 `[2:0]` 籠統寫法，先對舊文字驗證必敗 | 審查轉錄（Table 4-25；映射內部自洽——兩組皆 B1/B0/ATCM ↔ [2]/[1]/[0]） |
| 71 | 本檔＋終結函 | 結案條款定稿（FINAL-03～06）：終結函四處措辭修正——(a) Andes 證據層級＝「RISC-V Privileged v1.11＋Andes 官方 QEMU pinned model；AndeStar V5 SPA／datasheet 尚未取得」，N45 為指定 QEMU model profile、不等同現行矽產品定版；(b)「R8–R12 零內容錯誤」改「當時未新發現內容錯誤」（R13 修正的錯誤當時已存在，只是未被發現）；(c) 總保證降為可證明範圍——「本審查已覆蓋範圍內無剩餘已知錯誤；未親驗、未細切、產品世代衝突與未收錄範圍明列 pending」，不宣稱全域／永久正確；(d) 內容審查重啟條件放寬為「可重現一手證據」（官方 URL＋版次＋SHA-256／使用者附件／審查環境可讀副本），官方 PDF **不強制** commit 入 repo——repo 只需記來源、版次、雜湊、頁碼與驗證結論；惟 Verified 升級仍以審查環境實際可讀為前提，僅有 URL＋雜湊而環境不可達時維持轉錄層 | 慣例決策（結案程序） |

## 二、待原文親驗後回填（官方 PDF 公網已可取得——見 #65）

文件狀態（2026-08-31）：**DDI 0460D** 與 **100442_0200_02_en** 的官方下載端點已恢復可達
（Codex 實測，URL/雜湊見 #65）；我方沙箱出口政策仍擋 arm.com 系網域（403 host_not_allowed，
同日重試實測）——**使用者將兩份官方 PDF 放入 repo 即可解鎖親驗**，屆時逐顆、逐表核對後把
「審查轉錄」升級為 Verified 並回填下列值（不得批次升級）。**N25/N45 datasheet 或 AndeStar
V5 SPA** 仍待取得。

### R5（審查轉錄的 Table 4-2 讀值——**未寫入 spec**，回填前逐項親驗）
CTR=0x8003C003、TCMTR=0x00010001、ID_PFR0=0x00000131、ID_PFR1=0x00000001、ID_DFR0=0x00010400、
ID_AFR0=0、ID_MMFR0=0x00210030、MMFR1=0、MMFR2=0x01200000、MMFR3=0x00000211、
ID_ISAR1=0x13112111、ISAR3=0x01112131、ISAR4=0x00010142、ISAR5=0、
AIDR=0、CPACR=0、PMCR=0x41151800、FPSID=0x41023153、MVFR0=0x10110221、MVFR1=0x00000011

**已知衝突（R3／R4 確認，不得直接回填）**：
- ID_ISAR0 — Table 4-2 印 0x01101111（Divide=僅 Thumb），但 Table 4-15 明定 r1p0 起 ARM+Thumb
  皆有 SDIV/UDIV（Divide=0x2）→ r1p2 應推導 0x02101111。R4 檢索：公開 SDEN（ARM-EPM-012129 v3.0）
  查無 Table 4-2 勘誤（審查轉錄）；QEMU cortex-r5 **r1p3** 模型用推導值（qemu-project/qemu
  pin `d2e570cc0f97b936902a5b1b86b73c0f5998b475` target/arm/tcg/cpu32.c 親驗——r1p3 非 r1p2，
  僅作交叉佐證）。需硬體實測或新版 TRM 定案。
- ID_ISAR2 — Table 4-2 印 0x21232131（MemHint[7:4]=0x3＝僅 PLD/PLI，即 r0p0 值），但 Table 4-17
  明定 r1p0 起支援 PLDW→MemHint=0x4（0406C.d MemHint_instrs 編碼 0b0100＝加 PLDW，親驗）→ r1p2
  應推導 0x21232141。QEMU cortex-r5 r1p3 模型（同上 pin `d2e570c`，親驗）與 sample_r5.bin
  皆用推導值。R4 新發現，與 ID_ISAR0 同型（Table 4-2 疑沿用 r0p0 讀值未隨版更新）。

### R5 其他待辦
- ~~SCTLR 產品化~~ R5R 已依 Table 4-24 轉錄套用（決議 #34）——待原文親驗後升級 Verified
- ~~DFSR/IFSR 產品欄名~~ R5R 已依 §4.3.20 轉錄套用（決議 #35）——待原文親驗後升級 Verified
- TRM 專屬未收顆：Secondary ACTLR、TCM Selection（c9,c2,0，Xilinx 佐證存在）、Slave Port Control、
  Correctable Fault Location、Build Options、Pin Options、周邊介面區域暫存器——親驗後補收
- R5 vs R5F 的 schema 級 requires:FPU 機制（見第四節）

### A55（審查轉錄的 Table 3-49 讀值——未寫入 spec）
CTR_EL0=0x84448004、ID_AA64DFR0=0x…10305408、ID_AA64ISAR1=0x…00100001、ID_AA64MMFR0=0x…00101122、
ID_AA64MMFR1=0x…10212122、ID_AA64MMFR2=0x…00001011、ID_AA64PFR1=0x…00000010、CSSELR=0
（REVIDR=0、AIDR=0 已於 R5R 以轉錄層寫入 spec Reset——決議 #36/#37，親驗後升級）
- MMFR0[63:24] 疑點已於 R4 釐清：A55 TRM Figure 3-127 確實把 [63:24] 整段併標 RES0（產品畫法，
  審查轉錄），同時 TGran4/TGran64 的架構編碼 0＝支援仍成立——spec 以雙層描述並存（決議 #28），結案。
- EL2/EL3 暫存器群、PMU 直接視圖群、DSU 叢集暫存器（TF-A dsu_def.h 可為編碼憑據）：依需求擴充

### Andes
- N45 定版：現行官網世代（RV32GCB/M-U-S/PMP32/PMA16）vs QEMU 模型（本檔現況）——取得 datasheet 後
  決定是否分立 `n45_qemu` / `n45_gen2` 兩份 spec
- 12 顆僅編號＋遮罩的 CSR（mxstatus/mcache_ctl 中段/milmb 高位/mecc_code/mpft_ctl/msave*/mclk_ctl/
  mppib・mfiob 大小編碼/udcause 值表/mdcause 值表）：SPA 手冊親驗後補切分
- PMA 群（pmacfg/pmaaddr）與 pmpcfg4-7/pmpaddr16-31：datasheet 定版後以組態條件補收

## 三、已駁回／已撤回的審查主張（含出處）

| 輪次 | 主張 | 處置 |
|---|---|---|
| R2 A55-09 | CNTKCTL EL0PTEN[9]/EL0VTEN[8] 是 FEAT_ECV、A55 應 RES0 | **撤回**（R2R 反駁、R3 確認）：ARMv7 CNTKCTL.PL0PTEN/PL0VTEN 即存在（DDI 0406C.d B8-1952 親驗）；ECV 僅新增 EVNTIS[17] |
| R2 R5-14 部分 | ID_ISAR0=0x01101111 為 r1p2 正確值 | **改列 TRM 內部衝突**（R2R 質疑、R3 承認）：見第二節 |
| R2 A55-05/06 定性 | 「產品佈局／位置錯誤」 | **改定性**為「產品 overlay／存在性呈現」——位置層級的 sail 對照未被推翻 |
| R2 A55-02 引用 | CCSIDR 圖號 Figure 3-101 | **更正為 Figure 3-99**（R3；3-101 是 CPACR_EL1）。教訓：圖號類引用以「章節＋暫存器名」為錨 |
| R2 A55-03 歸因 | REVIDR 語意錯置歸因 VPIDR_EL2 | 更正：源頭是 ARMv7 REVIDR 選配別名語意（R2R 提出、R3 採納） |
| R2 測試備註 | 「170 passed 3 skipped」暗示 repo 測試異常 | 環境差異：該環境缺 Python playwright 套件（3 條 bridge 測試 skip）。Claude 環境 node＋playwright 皆備，skip=0（R3R 時 176 條、R4R 加 6 條鎖定測試後 182 條）。R4 補充：CI 過去同樣缺 playwright（skip 3）——R4R 起 workflow 安裝 playwright＋chromium，CI 與本機跑同一套全量測試 |

## 四、雙方同意、尚未實作的機制改進

1. **requires/predicate 欄位**：spec 格式增加 `- Requires:`（如 `FPU`、`mmsc_cfg.HSP=1`、`RVS`），
   解析器與 UI 呈現存在條件——目前條件寫在 Description，機器可讀化排入下一輪（與產品 overlay 一併做）
2. **Verified 分層標籤**的機器可讀化（目前以 Verified 文字＋Description 慣例表達，分層定義見本檔開頭）
3. n25/n45 測試由「全等」改為「base＋overlay 差異表」：已知差異（mcounterovf 清除語意、marchid）已鎖測試
