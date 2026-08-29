# SPEC_REVIEW_LOG — 三方交叉審查決議紀錄

本檔是 `specs/` 四份 CPU spec 與外部審查（ChatGPT／OpenAI）交叉檢查的**決議與待辦總帳**。
目的：讓每一輪審查的結論不散失，並明確區分「已套用」「待原文親驗」「已駁回」。

- 審查輪次：R1＝2026-08-24 自我稽核；R2＝ChatGPT 第二輪審查；R2R＝Claude 複驗回覆；R3＝OpenAI 第三輪審查；R3R＝本輪（2026-08-29）套用
- 證據分層定義（Verified 欄位的授予標準）：
  1. **親驗一手**：Claude 直接開啟一手來源逐欄核對（唯一可寫 `- Verified:` 的層級）
  2. **審查轉錄**：審查方轉錄自 TRM，Claude 無法在工作環境開啟原文——內容可寫入表格，但**不給 Verified**，
     Description 必須標「審查轉錄…待親驗」
  3. **佐證**：第三方程式碼（Xilinx BSP、Linux kernel、TF-A）——只用於支持方向，不決定完整佈局
- 工作環境限制（2026-08-29 查核）：documentation-service.arm.com／andestech.com 於 Claude 工作環境不可達；
  GitHub raw／git 可達。此為環境紀錄，非 spec 永久屬性（依 R3 修正 7 移出 spec 本體，記於此）。

## 一、已套用的決議（R3R，本輪 commit）

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
| 9 | cortex_r5 | SCTLR FI/RR/Z 產品固定行為以註記呈現（Access 未改，待原文） | 審查轉錄 |
| 10 | cortex_r5 | CPACR ASEDIS/D32DIS 改 R5F 產品語意（VFPv3-D16→兩位恆 1） | 審查轉錄 |
| 11 | cortex_r5 | CSSELR 產品註（僅 L1；產品層 Level 唯讀） | 審查轉錄 |
| 12 | cortex_r5 | 新增 MVFR0/MVFR1（62 顆） | 親驗（0406C §B6.1） |
| 13 | cortex_a55 | SCTLR_EL1[29:28]→RES1（無 FEAT_LSMAOC） | 親驗（Linux SCTLR_EL1_RES1＋架構規則）＋審查（Figure 3-162） |
| 14 | cortex_a55 | CCSIDR 補 WT/WB/RA/WA[31:28] | 親驗（0406C 同佈局）＋審查（§3.2.23／Figure 3-99，R3 更正圖號） |
| 15 | cortex_a55 | AFSR0/1_EL1→RES0（消除表格與說明矛盾） | 親驗（自檔矛盾）＋審查 |
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

## 二、待原文親驗後回填（需使用者提供 PDF 或關鍵頁）

需要的文件：**DDI 0460D**（Cortex-R5 r1p2 TRM）、**100442_0200_02_en**（Cortex-A55 r2p0 TRM）、
定版的 **N25/N45 datasheet 或 AndeStar V5 SPA**。取得後逐項親驗、把「審查轉錄」升級為 Verified 並回填下列值。

### R5（審查轉錄的 Table 4-2 讀值——**未寫入 spec**，回填前逐項親驗）
CTR=0x8003C003、TCMTR=0x00010001、ID_PFR0=0x00000131、ID_PFR1=0x00000001、ID_DFR0=0x00010400、
ID_AFR0=0、ID_MMFR0=0x00210030、MMFR1=0、MMFR2=0x01200000、MMFR3=0x00000211、
ID_ISAR1=0x13112111、ISAR2=0x21232131、ISAR3=0x01112131、ISAR4=0x00010142、ISAR5=0、
AIDR=0、CPACR=0、PMCR=0x41151800、FPSID=0x41023153、MVFR0=0x10110221、MVFR1=0x00000011

**已知衝突（R3 確認，不得直接回填）**：ID_ISAR0 — Table 4-2 印 0x01101111（Divide=僅 Thumb），
但 Table 4-15 明定 r1p0 起 ARM+Thumb 皆有 SDIV/UDIV（Divide=0x2）→ r1p2 應推導 0x02101111。
TRM 內部矛盾，需硬體實測、errata 或新版 TRM 定案。

### R5 其他待辦
- SCTLR 產品固定位（FI/RR/Z 的 SBO/無效行為）：親驗 Table 4-24 後把 Access/Reset 產品化
- DFSR/IFSR 產品欄名（審查稱 bit12=SD、bit11=RW、bit10=S）：親驗 §4.3.20 後改名
- TRM 專屬未收顆：Secondary ACTLR、TCM Selection（c9,c2,0，Xilinx 佐證存在）、Slave Port Control、
  Correctable Fault Location、Build Options、Pin Options、周邊介面區域暫存器——親驗後補收
- R5 vs R5F 的 schema 級 requires:FPU 機制（見第四節）

### A55（審查轉錄的 Table 3-49 讀值——未寫入 spec）
CTR_EL0=0x84448004、ID_AA64DFR0=0x…10305408、ID_AA64ISAR1=0x…00100001、ID_AA64MMFR0=0x…00101122、
ID_AA64MMFR1=0x…10212122、ID_AA64MMFR2=0x…00001011、ID_AA64PFR1=0x…00000010、REVIDR=0、AIDR=0、CSSELR=0
- 疑點待回問：審查稱 MMFR0[63:24] 為 RES0——但 TGran4[31:28]/TGran64[27:24] 是 v8.0 基線欄位，
  讀 0＝「支援」（官方編碼），非 RES0。待 Figure 原文釐清 TRM 畫法。
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
| R2 測試備註 | 「170 passed 3 skipped」暗示 repo 測試異常 | 環境差異：該環境缺 Python playwright 套件（3 條 bridge 測試 skip）。Claude 環境 node v22.22.2＋playwright 皆備，173 passed 0 skipped |

## 四、雙方同意、尚未實作的機制改進

1. **requires/predicate 欄位**：spec 格式增加 `- Requires:`（如 `FPU`、`mmsc_cfg.HSP=1`、`RVS`），
   解析器與 UI 呈現存在條件——目前條件寫在 Description，機器可讀化排入下一輪（與產品 overlay 一併做）
2. **Verified 分層標籤**的機器可讀化（目前以 Verified 文字＋Description 慣例表達，分層定義見本檔開頭）
3. n25/n45 測試由「全等」改為「base＋overlay 差異表」：已知差異（mcounterovf 清除語意、marchid）已鎖測試
