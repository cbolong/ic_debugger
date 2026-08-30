# CPU: ARM Cortex-R5
# Version: r1p2 · ARMv7-R
# Width: 32
# Source: ARM DDI 0406C.d（ARMv7-A/R Architecture Reference Manual，官方 PDF 逐欄轉錄；含 SCTLR 的 Figure B6-1 reset 圖親驗）／ARM DDI 0460D（Cortex-R5 TRM：TCMTR 親驗；ACTLR／ADFSR／AIFSR／ATCMRR／BTCMRR／FPEXC 六顆位元表，以及 SCTLR（Table 4-24）與 DFSR／IFSR（Table 4-28/4-29/4-30）的產品 overlay 為審查轉錄）
# Status: ⚠ 62 顆中 56 顆的位元定義已親驗對照官方文件（55 顆依 ARM DDI 0406C.d §B6/§B1/§B8 逐欄轉錄、TCMTR 依 DDI 0460D 圖表、MVFR0/MVFR1 依 DDI 0406C.d §B6.1），出處見各暫存器的 Verified。另 6 顆（ACTLR／ADFSR／AIFSR／ATCMRR／BTCMRR／FPEXC）的產品位元表依 2026-08 三輪交叉審查轉錄自 DDI 0460D（Table 4-25/4-31/4-32/4-43/4-44/11-6），**尚未親驗原文**，該顆的 Description 逐一註明「審查轉錄」——以此為據修改硬體設定前請先核對 TRM。2026-08-29 依交叉審查修正：ATCMRR/BTCMRR 編碼互換（正確為 ATCM=c9,c1,1、BTCM=c9,c1,0）、補 TCM Size 欄、DFSR/IFSR 改 RW、FPEXC 產品化（DEX[29]）、FPSCR trap 位改 RAZ/WI、RGNR 改 4-bit。2026-08-30 R5/R6 輪再套用：SCTLR 依 Table 4-24 產品 overlay（FI/Z 為 SBO、reset 依 0406C Figure B6-1 親驗回填）、DFSR/IFSR 依 §4.3.20 改產品欄名（SD/RW/S/Domain/Status）且 Status enum 對齊 Table 4-28（八個產品編碼，其餘保留）。待辦與待親驗值清單見 SPEC_REVIEW_LOG.md。R5 與 R5F 差異：FPSID/FPSCR/FPEXC/MVFR0/MVFR1 僅 R5F（各顆 Description 已標）
# Description: ARMv7-R（PMSAv7）架構 Table B5-11 清單中本工具可 dump 的可讀 CP15 系統控制暫存器＋選收的 Cortex-R5 產品暫存器（ATCMRR/BTCMRR）＋CPSR＋FPU（R5F），依官方 Table B5-11 順序排列；不含 c15 實作定義群與其他僅見於 TRM 的暫存器（範圍見下方註解的不收清單）

<!--
  ── Offset 對應約定 ────────────────────────────────────────────────
  Offset ＝ 此暫存器的值在 bin dump 中的「位元組位移」（從 0 起算），
  不是 CP15 的 (CRn, op1, CRm, op2) 編碼。請讓 dump 腳本的輸出順序與
  下面的 Offset 順序一致（examples/sample_r5.bin 即依此順序產生）。
  每顆的 CP15 編碼寫在該暫存器 Description 的 MRC 指令範例中。

  ── 本版順序（2026-08-28 完整化改版）───────────────────────────────
  順序改依官方 DDI 0406C.d Table B5-11（PMSA CP15 暫存器總表，CRn 序）：
  c0 識別群 → c1 控制群 → c5/c6 故障群 → c6 MPU 區域群 → c9 PMU 群
  →（c9 實作定義 TCM 區域）→ c13 context/thread → CPSR → FPU。
  與 2026-08-24 之前的 18 顆版不相容——dump 腳本必須改用新順序。

  ── 對照狀態（2026-08-28）──────────────────────────────────────────
  ✔ 位元定義已對照：官方 ARMv7-A/R ARM（DDI 0406C.d）§B6.1 逐顆轉錄，
     55 顆；TCMTR 依 DDI 0460D §4 Figure 4.9/Table 4.5（現場截圖）。
  ✘ 尚未對照（需 Cortex-R5 TRM（DDI 0460）原文）：
     * ACTLR／ADFSR／AIFSR 的逐位意義（架構只定義位置，內容實作定義）
     * ATCMRR／BTCMRR 的欄位切分（TRM §4.3.14/4.3.15）
     * 各 ID 暫存器（ID_PFR0…ID_ISAR5、CCSIDR、CLIDR、AIDR）的實際讀值
     * 各暫存器的實際 Reset 值（本檔僅寫架構明訂者）
     * PMU 是否實作與計數器數量（讀 PMCR.N 可自證）
  ✘ 官方 Table B5-11 有、本檔刻意不收（讀不到值或 R5 未實作）：
     * c7 全部 cache/branch predictor 維護操作與 CP15ISB/DSB/DMB（寫入型
       操作，dump 不到狀態）、PMSWINC（WO）
     * IRBAR／IRSR／IRACR（僅「指令與資料分離的 MPU」實作；MPUIR.nU=0
       （unified，R5 的組態）時官方定義不實作——dump 值可由 MPUIR 自證）
     * c14 Generic Timer 群（CNTFRQ 等 10 顆：選配擴充；是否實作可由
       ID_PFR1[19:16] 自證，Cortex-R5 未實作）
     * c11 TCM DMA 群、c15 實作定義群（需 TRM；含 Secondary ACTLR、
       Correctable Fault Location 等，見 DDI 0460 §4.1 的 c15 清單）
-->

## MIDR
- Offset: 0x000
- Reset: 0x411FC152
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「MIDR, Main ID Register, PMSA」— 位元切分依官方逐欄核對＋Table B6-4/B6-5（Reset 值 0x411FC152 由檔頭宣告的 r1p2 與 Cortex-R5 部件編號 0xC15 推得，尚未用 DDI 0460D 確認）
- Description: Main ID Register — CPU 識別碼（MRC p15,0,Rt,c0,c0,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:24 | Implementer | RO | 0x41 | 實作者代碼（官方 Table B6-4） |
| 23:20 | Variant | RO | 0x1 | 實作定義的主要版本（rXpY 的 X） |
| 19:16 | Architecture | RO | 0xF | 架構代碼（官方 Table B6-5） |
| 15:4 | PartNum | RO | 0xC15 | 實作定義的部件編號 |
| 3:0 | Revision | RO | 0x2 | 實作定義的次要版本（rXpY 的 Y） |

### Enum: Implementer
- 0x41: ARM Limited
- 0x44: Digital Equipment
- 0x4D: Motorola/Freescale
- 0x51: Qualcomm
- 0x56: Marvell
- 0x69: Intel

### Enum: Architecture
- 0x1: ARMv4
- 0x2: ARMv4T
- 0x3: ARMv5
- 0x4: ARMv5T
- 0x5: ARMv5TE
- 0x6: ARMv5TEJ
- 0x7: ARMv6
- 0xF: 由 CPUID scheme 定義（ARMv7 起固定此值）

### Enum: PartNum
- 0xC15: Cortex-R5

## CTR
- Offset: 0x004
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「CTR, Cache Type Register, PMSA」— 位元切分依官方逐欄核對（PMSA 版 bits[15:14] 為 RAO，與 VMSA 版的 L1Ip 欄不同）
- Description: Cache Type Register — 快取架構資訊（值隨實際配置的快取而定；MRC p15,0,Rt,c0,c0,1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:29 | Format | RO | 0b100 | 暫存器格式 |
| 28 | RES0 | RO | 0 | 保留（官方標 RAZ） |
| 27:24 | CWG | RO | - | Cache Write-back Granule — 一次 eviction 最多改寫的記憶體大小（log2 words；0b0000 = 未提供此資訊） |
| 23:20 | ERG | RO | - | Exclusives Reservation Granule — LDREX/STREX 保留粒度（log2 words） |
| 19:16 | DminLine | RO | - | 所有 D-cache／unified cache 最小 line 大小（log2 words） |
| 15:14 | RES1 | RO | 0b11 | 官方 PMSA 版標 RAO（恆讀 1） |
| 13:4 | RES0 | RO | 0 | 保留 |
| 3:0 | IminLine | RO | - | 所有 I-cache 最小 line 大小（log2 words） |

### Enum: Format
- 0b100: ARMv7 格式
- 0b000: ARMv6 格式

## TCMTR
- Offset: 0x008
- Reset: -
- Verified: ARM DDI 0460D（Cortex-R5 TRM r1p2）§4 Figure 4.9 / Table 4.5 — 位元切分依官方圖示逐欄核對
- Description: TCM Type Register — 告知處理器系統中 ATCM 與 BTCM 的數量（唯讀，僅特權模式可存取；MRC p15,0,Rt,c0,c0,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:29 | RES0 | RO | 0b000 | 保留（官方圖示標示為 0） |
| 28:19 | RES0 | RO | 0 | 保留 |
| 18:16 | BTCM | RO | - | 系統中 BTCM 的數量 |
| 15:3 | RES0 | RO | 0 | 保留 |
| 2:0 | ATCM | RO | - | 系統中 ATCM 的數量 |

## MPUIR
- Offset: 0x00C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「MPUIR, MPU Type Register, PMSA」— 位元切分依官方逐欄核對
- Description: MPU Type Register — MPU 區域數量與組態（唯讀；MRC p15,0,Rt,c0,c0,4）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:24 | RES0 | RO | - | 保留（官方標 UNK） |
| 23:16 | IRegion | RO | - | 指令區域數（unified MPU 時官方標 UNK，讀為 0） |
| 15:8 | DRegion | RO | - | 資料／統一區域數（0 = 未實作 MPU，使用預設記憶體映射） |
| 7:1 | RES0 | RO | - | 保留（官方標 UNK） |
| 0 | nU | RO | - | MPU 是否為非統一映射 |

### Enum: nU
- 0: 統一（unified）記憶體映射——bits[23:16] 讀為 0
- 1: 指令與資料分離的記憶體映射

## MPIDR
- Offset: 0x010
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「MPIDR, Multiprocessor Affinity Register, PMSA」— 位元切分依官方逐欄核對
- Description: Multiprocessor Affinity Register — 多處理器親和性（識別本核心在叢集中的位置；MRC p15,0,Rt,c0,c0,5）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | M | RO | 1 | 官方定義：實作多處理器擴充時讀 1（RAO） |
| 30 | U | RO | - | 單處理器系統指示 |
| 29:25 | RES0 | RO | 0 | 保留 |
| 24 | MT | RO | - | 最低親和層級是否為多執行緒核心 |
| 23:16 | Aff2 | RO | - | 親和層級 2（實作定義） |
| 15:8 | Aff1 | RO | - | 親和層級 1（叢集內核心編號等，實作定義） |
| 7:0 | Aff0 | RO | - | 親和層級 0（實作定義） |

### Enum: U
- 0: 多處理器系統的一部分
- 1: 單處理器系統

### Enum: MT
- 0: 各核心獨立
- 1: 以多執行緒方式實作

## REVIDR
- Offset: 0x014
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「REVIDR, Revision ID Register, PMSA」— 位元切分依官方逐欄核對
- Description: Revision ID Register — 實作特定的小改版資訊，須與 MIDR 一併解讀（選配；未實作時此編碼為 MIDR 的別名，讀值 = MIDR 即代表未實作；MRC p15,0,Rt,c0,c0,6）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | REVIDR | RO | - | 實作定義（官方：bit assignments are IMPLEMENTATION DEFINED） |

## ID_PFR0
- Offset: 0x018
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_PFR0, Processor Feature Register 0, PMSA」— 位元切分依官方逐欄核對
- Description: Processor Feature Register 0 — 指令集狀態支援（CPUID；須與 ID_PFR1 一併解讀；MRC p15,0,Rt,c0,c1,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:16 | RES0 | RO | - | 保留（官方標 UNK） |
| 15:12 | State3 | RO | - | ThumbEE 指令集支援 |
| 11:8 | State2 | RO | - | Jazelle 擴充支援 |
| 7:4 | State1 | RO | - | Thumb 指令集支援 |
| 3:0 | State0 | RO | - | ARM 指令集支援 |

### Enum: State3
- 0b0000: 未實作
- 0b0001: 已實作 ThumbEE（僅 State1=0b0011 時允許）

### Enum: State2
- 0b0000: 未實作
- 0b0001: Jazelle 已實作（例外進入不清 JOSCR.CV）
- 0b0010: Jazelle 已實作（例外進入清 JOSCR.CV）

### Enum: State1
- 0b0000: 未實作 Thumb
- 0b0001: Thumb-2 之前的編碼（全 16-bit）
- 0b0011: Thumb-2 之後的完整 16/32-bit 編碼

### Enum: State0
- 0b0000: 未實作 ARM 指令集
- 0b0001: 已實作 ARM 指令集

## ID_PFR1
- Offset: 0x01C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_PFR1, Processor Feature Register 1, PMSA」— 位元切分依官方逐欄核對
- Description: Processor Feature Register 1 — 程式設計模型與安全擴充支援（CPUID；官方：Virtualization／Security 兩欄在 PMSA 實作必為 0；MRC p15,0,Rt,c0,c1,1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:20 | RES0 | RO | - | 保留（官方標 UNK） |
| 19:16 | GenTimer | RO | - | Generic Timer 擴充支援 |
| 15:12 | Virt | RO | - | 虛擬化擴充支援（PMSA 必為 0b0000） |
| 11:8 | MProfile | RO | - | M-profile 程式設計模型支援 |
| 7:4 | Security | RO | - | 安全擴充支援（PMSA 必為 0b0000） |
| 3:0 | ProgMod | RO | - | 標準（ARMv4 起）程式設計模型支援 |

### Enum: GenTimer
- 0b0000: 未實作
- 0b0001: 已實作 Generic Timer 擴充

### Enum: MProfile
- 0b0000: 不支援
- 0b0010: 支援雙堆疊（two-stack）模型

### Enum: ProgMod
- 0b0000: 不支援
- 0b0001: 支援 User/FIQ/IRQ/Supervisor/Abort/Undefined/System 模式

## ID_DFR0
- Offset: 0x020
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_DFR0, Debug Feature Register 0, PMSA」— 位元切分依官方逐欄核對
- Description: Debug Feature Register 0 — 除錯系統頂層資訊（CPUID；MRC p15,0,Rt,c0,c1,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | RES0 | RO | - | 保留（官方標 UNK） |
| 27:24 | PerfMon | RO | - | coprocessor 介面的效能監視擴充（A/R profile） |
| 23:20 | MDbg_M | RO | - | M-profile 記憶體映射除錯模型 |
| 19:16 | MMapTrc | RO | - | 記憶體映射 trace 模型 |
| 15:12 | CopTrc | RO | - | coprocessor（CP14）trace 模型 |
| 11:8 | MMapDbg | RO | - | 記憶體映射除錯模型（A/R profile） |
| 7:4 | CopSDbg | RO | - | coprocessor Secure 除錯模型（僅含安全擴充的 A profile） |
| 3:0 | CopDbg | RO | - | coprocessor（CP14）除錯模型（A/R profile） |

### Enum: PerfMon
- 0b0000: 不表示是否支援 PMUv1
- 0b0001: 支援 PMUv1
- 0b0010: 支援 PMUv2
- 0b1111: 無 ARM 效能監視擴充

### Enum: MMapDbg
- 0b0000: 不支援（或 ARMv6 之前）
- 0b0100: v7 Debug，記憶體映射存取
- 0b0101: v7.1 Debug，記憶體映射存取

### Enum: CopDbg
- 0b0000: 不支援
- 0b0010: v6 Debug，CP14 存取
- 0b0011: v6.1 Debug，CP14 存取
- 0b0100: v7 Debug，CP14 存取
- 0b0101: v7.1 Debug，CP14 存取

## ID_AFR0
- Offset: 0x024
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_AFR0, Auxiliary Feature Register 0, PMSA」— 位元切分依官方逐欄核對
- Description: Auxiliary Feature Register 0 — 四個 4-bit 實作定義特徵欄，意義由實作者（見 MIDR.Implementer）定義（CPUID；MRC p15,0,Rt,c0,c1,3）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:16 | RES0 | RO | - | 保留（官方標 UNK） |
| 15:12 | IMPDEF3 | RO | - | 實作定義 |
| 11:8 | IMPDEF2 | RO | - | 實作定義 |
| 7:4 | IMPDEF1 | RO | - | 實作定義 |
| 3:0 | IMPDEF0 | RO | - | 實作定義 |

## ID_MMFR0
- Offset: 0x028
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_MMFR0, Memory Model Feature Register 0, PMSA」— 位元切分依官方逐欄核對
- Description: Memory Model Feature Register 0 — 記憶體模型與管理支援（CPUID；R profile 應顯示 PMSA=0b0011、VMSA=0b0000；MRC p15,0,Rt,c0,c1,4）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | InnerShr | RO | - | 最內層 shareability 域（僅 ShrLvl 非 0 時有效） |
| 27:24 | FCSE | RO | - | FCSE 支援（僅 VMSA>0b0010 時允許非 0） |
| 23:20 | AuxReg | RO | - | 輔助暫存器支援 |
| 19:16 | TCM | RO | - | TCM 與其 DMA 支援 |
| 15:12 | ShrLvl | RO | - | shareability 層級數 |
| 11:8 | OuterShr | RO | - | 最外層 shareability 域 |
| 7:4 | PMSA | RO | - | PMSA 支援（非 0 時 VMSA 欄必為 0） |
| 3:0 | VMSA | RO | - | VMSA 支援（非 0 時 PMSA 欄必為 0） |

### Enum: AuxReg
- 0b0000: 無
- 0b0001: 僅 Auxiliary Control Register
- 0b0010: ACTLR ＋ Auxiliary Fault Status（ADFSR/AIFSR）

### Enum: TCM
- 0b0000: 不支援
- 0b0001: 實作定義（ARMv7 規定值）
- 0b0010: 僅 TCM（ARMv6 型）
- 0b0011: TCM＋DMA（ARMv6 型）

### Enum: ShrLvl
- 0b0000: 一層
- 0b0001: 兩層

### Enum: PMSA
- 0b0000: 不支援
- 0b0001: 實作定義的 PMSA
- 0b0010: PMSAv6
- 0b0011: PMSAv7（支援 memory subsections；ARMv7-R）

### Enum: VMSA
- 0b0000: 不支援
- 0b0011: VMSAv7（ARMv7-A）
- 0b0100: VMSAv7＋PXN
- 0b0101: VMSAv7＋PXN＋Long-descriptor

## ID_MMFR1
- Offset: 0x02C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_MMFR1, Memory Model Feature Register 1, PMSA」— 位元切分依官方逐欄核對
- Description: Memory Model Feature Register 1 — cache 維護與分支預測管理需求（CPUID；官方：多數 L1 欄位在 ARMv7 規定為 0b0000；MRC p15,0,Rt,c0,c1,5）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | BPred | RO | - | 分支預測器維護需求 |
| 27:24 | L1TstCln | RO | - | L1 資料快取 test-and-clean（ARMv7 規定 0b0000） |
| 23:20 | L1Uni | RO | - | L1 整體維護（unified；ARMv7 規定 0b0000） |
| 19:16 | L1Hvd | RO | - | L1 整體維護（Harvard；ARMv7 規定 0b0000） |
| 15:12 | L1UniSW | RO | - | L1 set/way 維護（unified；ARMv7 規定 0b0000） |
| 11:8 | L1HvdSW | RO | - | L1 set/way 維護（Harvard；ARMv7 規定 0b0000） |
| 7:4 | L1UniVA | RO | - | L1 MVA 維護（unified；ARMv7 規定 0b0000） |
| 3:0 | L1HvdVA | RO | - | L1 MVA 維護（Harvard；ARMv7 規定 0b0000） |

### Enum: BPred
- 0b0000: 無分支預測器或無 MMU
- 0b0001: 多情境需 flush
- 0b0010: MMU 相關變更需 flush
- 0b0011: 僅寫入指令位置需 flush
- 0b0100: 永不需要 flush

## ID_MMFR2
- Offset: 0x030
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_MMFR2, Memory Model Feature Register 2, PMSA」— 位元切分依官方逐欄核對
- Description: Memory Model Feature Register 2 — WFI／barrier／TLB 支援（CPUID；官方：HWAcc 在 ARMv7-R 必為 0；MRC p15,0,Rt,c0,c1,6）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | HWAcc | RO | - | 硬體 Access flag（VMSAv7 專屬；ARMv7-R 必為 0b0000） |
| 27:24 | WFI | RO | - | WFI 停頓（stalling）支援 |
| 23:20 | MemBarr | RO | - | CP15 記憶體 barrier 操作支援 |
| 19:16 | UniTLB | RO | - | unified TLB 維護操作（PMSA 無 TLB，讀 0） |
| 15:12 | HvdTLB | RO | - | Harvard TLB 維護操作（legacy 欄位） |
| 11:8 | L1HvdRng | RO | - | L1 Harvard cache 範圍維護 |
| 7:4 | L1HvdBG | RO | - | L1 Harvard cache 背景（非阻塞）預取 |
| 3:0 | L1HvdFG | RO | - | L1 Harvard cache 前景（阻塞）預取 |

### Enum: WFI
- 0b0000: 不支援
- 0b0001: 支援 WFI 停頓

## ID_MMFR3
- Offset: 0x034
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_MMFR3, Memory Model Feature Register 3, PMSA」— 位元切分依官方逐欄核對
- Description: Memory Model Feature Register 3 — 維護操作與位址範圍（CPUID；MRC p15,0,Rt,c0,c1,7）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | SuperSec | RO | - | Supersection 支援（VMSA；官方：0 = 支援，本欄反向） |
| 27:24 | CMemSz | RO | - | 快取可覆蓋的實體位址範圍 |
| 23:20 | CohWalk | RO | - | 翻譯表更新是否需 clean 到 PoU（VMSA） |
| 19:16 | RES0 | RO | - | 保留（官方標 UNK） |
| 15:12 | MaintBcst | RO | - | 維護操作廣播範圍 |
| 11:8 | BPMaint | RO | - | 分支預測器維護操作（階層式） |
| 7:4 | CMaintSW | RO | - | set/way cache 維護操作（階層式） |
| 3:0 | CMaintVA | RO | - | MVA cache 維護操作（階層式） |

### Enum: CMemSz
- 0b0000: 4GB（32-bit 實體位址）
- 0b0001: 64GB（36-bit）
- 0b0010: 1TB（40-bit）

### Enum: MaintBcst
- 0b0000: 僅影響本地
- 0b0001: 廣播（不含 hint）
- 0b0010: 全部廣播

## ID_ISAR0
- Offset: 0x038
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_ISAR0, Instruction Set Attribute Register 0, PMSA」— 位元切分依官方逐欄核對
- Description: Instruction Set Attribute Register 0（CPUID；須與 ISAR1–4 一併解讀；MRC p15,0,Rt,c0,c2,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | RES0 | RO | - | 保留（官方標 UNK） |
| 27:24 | Divide | RO | - | 除法指令 |
| 23:20 | Debug | RO | - | 除錯指令 |
| 19:16 | Coproc | RO | - | 泛用 coprocessor 指令 |
| 15:12 | CmpBranch | RO | - | Thumb 比較兼分支指令 |
| 11:8 | Bitfield | RO | - | 位元欄位指令 |
| 7:4 | BitCount | RO | - | 位元計數指令 |
| 3:0 | Swap | RO | - | ARM Swap 指令 |

### Enum: Divide
- 0b0000: 無
- 0b0001: Thumb 的 SDIV/UDIV
- 0b0010: Thumb＋ARM 的 SDIV/UDIV

### Enum: Debug
- 0b0000: 無
- 0b0001: 加入 BKPT

### Enum: Coproc
- 0b0000: 無（架構另行歸屬者除外）
- 0b0001: CDP/LDC/MCR/MRC/STC
- 0b0010: 再加 *2 形式
- 0b0011: 再加 MCRR/MRRC
- 0b0100: 再加 MCRR2/MRRC2

### Enum: CmpBranch
- 0b0000: 無
- 0b0001: 加入 CBNZ/CBZ

### Enum: Bitfield
- 0b0000: 無
- 0b0001: 加入 BFC/BFI/SBFX/UBFX

### Enum: BitCount
- 0b0000: 無
- 0b0001: 加入 CLZ

### Enum: Swap
- 0b0000: 無
- 0b0001: 加入 SWP/SWPB

## ID_ISAR1
- Offset: 0x03C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_ISAR1, Instruction Set Attribute Register 1, PMSA」— 位元切分依官方逐欄核對
- Description: Instruction Set Attribute Register 1（CPUID；MRC p15,0,Rt,c0,c2,1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | Jazelle | RO | - | Jazelle 擴充指令 |
| 27:24 | Interwork | RO | - | 互通（interworking）指令 |
| 23:20 | Immediate | RO | - | 長立即值資料處理指令 |
| 19:16 | IfThen | RO | - | Thumb If-Then 指令 |
| 15:12 | Extend | RO | - | 純量擴展（sign/zero-extend）指令 |
| 11:8 | Except_AR | RO | - | A/R profile 例外處理指令 |
| 7:4 | Except | RO | - | ARM 例外處理指令（LDM/STM 特殊形式） |
| 3:0 | Endian | RO | - | 位元組序指令 |

### Enum: Jazelle
- 0b0000: 無
- 0b0001: 加入 BXJ 與 PSR 的 J bit

### Enum: Interwork
- 0b0000: 無
- 0b0001: BX＋PSR T bit
- 0b0010: 再加 BLX；PC 載入具 BX 行為
- 0b0011: 再保證資料處理指令寫 PC 具 BX 行為

### Enum: Immediate
- 0b0000: 無
- 0b0001: 加入 MOVT、MOV(16-bit imm)、ADD/SUB(12-bit imm)

### Enum: IfThen
- 0b0000: 無
- 0b0001: 加入 IT 指令與 PSR 的 IT bits

### Enum: Extend
- 0b0000: 無
- 0b0001: SXTB/SXTH/UXTB/UXTH
- 0b0010: 再加 *16 與帶加法形式

### Enum: Except_AR
- 0b0000: 無
- 0b0001: 加入 SRS/RFE 與 A/R 形式的 CPS

### Enum: Except
- 0b0000: 無
- 0b0001: LDM/STM 的 exception return／User registers 形式

### Enum: Endian
- 0b0000: 無
- 0b0001: 加入 SETEND 與 PSR 的 E bit

## ID_ISAR2
- Offset: 0x040
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_ISAR2, Instruction Set Attribute Register 2, PMSA」— 位元切分依官方逐欄核對
- Description: Instruction Set Attribute Register 2（CPUID；MRC p15,0,Rt,c0,c2,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | Reversal | RO | - | 位元／位元組反轉指令 |
| 27:24 | PSR_AR | RO | - | A/R profile 的 PSR 操作指令 |
| 23:20 | MultU | RO | - | 進階無號乘法 |
| 19:16 | MultS | RO | - | 進階有號乘法 |
| 15:12 | Mult | RO | - | 附加乘法指令 |
| 11:8 | MultiAccess | RO | - | 可中斷的多重存取（LDM/STM） |
| 7:4 | MemHint | RO | - | 記憶體提示（PLD 系列） |
| 3:0 | LoadStore | RO | - | 附加載入／儲存指令 |

### Enum: Reversal
- 0b0000: 無
- 0b0001: REV/REV16/REVSH
- 0b0010: 再加 RBIT

### Enum: PSR_AR
- 0b0000: 無
- 0b0001: MRS/MSR 與 exception return 形式

### Enum: MultU
- 0b0000: 無
- 0b0001: UMULL/UMLAL
- 0b0010: 再加 UMAAL

### Enum: MultS
- 0b0000: 無
- 0b0001: SMULL/SMLAL
- 0b0010: 再加 16-bit 乘法族與 Q bit
- 0b0011: 再加 SMLAD 等 DSP 乘加族

### Enum: Mult
- 0b0000: 僅 MUL
- 0b0001: 加 MLA
- 0b0010: 再加 MLS

### Enum: MultiAccess
- 0b0000: LDM/STM 不可中斷
- 0b0001: LDM/STM 可重啟
- 0b0010: 可續行（v7-A/R 不允許）

### Enum: MemHint
- 0b0000: 無
- 0b0001: PLD
- 0b0010: PLD（與 0b0001 同義）
- 0b0011: 再加 PLI
- 0b0100: 再加 PLDW

### Enum: LoadStore
- 0b0000: 無
- 0b0001: 加入 LDRD/STRD

## ID_ISAR3
- Offset: 0x044
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_ISAR3, Instruction Set Attribute Register 3, PMSA」— 位元切分依官方逐欄核對＋Table B6-3
- Description: Instruction Set Attribute Register 3（CPUID；MRC p15,0,Rt,c0,c2,3）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | ThumbEE | RO | - | ThumbEE 擴充指令（僅 ID_PFR0.State3=0b0001 時可非 0） |
| 27:24 | TrueNOP | RO | - | 真 NOP 指令 |
| 23:20 | ThumbCopy | RO | - | Thumb 低暫存器 MOV 支援 |
| 19:16 | TabBranch | RO | - | Thumb 表格分支指令 |
| 15:12 | SynchPrim | RO | - | 同步原語（與 ID_ISAR4.SynchPrim_frac 併讀，官方 Table B6-3） |
| 11:8 | SVC | RO | - | SVC 指令 |
| 7:4 | SIMD | RO | - | SIMD 指令（核心暫存器上） |
| 3:0 | Saturate | RO | - | 飽和指令 |

### Enum: TrueNOP
- 0b0000: 無
- 0b0001: Thumb＋ARM 真 NOP，允許 NOP 相容 hint

### Enum: TabBranch
- 0b0000: 無
- 0b0001: 加入 TBB/TBH

### Enum: SynchPrim
- 0b0000: 無（frac=0000）
- 0b0001: LDREX/STREX；frac=0011 再加 CLREX/B/H 形式
- 0b0010: 再加 LDREXD/STREXD（frac=0000）

### Enum: SVC
- 0b0000: 無
- 0b0001: 加入 SVC

### Enum: SIMD
- 0b0000: 無
- 0b0001: SSAT/USAT 與 Q bit
- 0b0011: 完整 SIMD 族與 GE[3:0]

### Enum: Saturate
- 0b0000: 無
- 0b0001: QADD/QDADD/QDSUB/QSUB 與 Q bit

## ID_ISAR4
- Offset: 0x048
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_ISAR4, Instruction Set Attribute Register 4, PMSA」— 位元切分依官方逐欄核對
- Description: Instruction Set Attribute Register 4（CPUID；MRC p15,0,Rt,c0,c2,4）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | SWP_frac | RO | - | SWP/SWPB 匯流排鎖定資訊（僅 ISAR0.Swap=0 時有效） |
| 27:24 | PSR_M | RO | - | M-profile 的 PSR 操作指令 |
| 23:20 | SynchPrim_frac | RO | - | 同步原語補充欄（與 ISAR3.SynchPrim 併讀） |
| 19:16 | Barrier | RO | - | barrier 指令（DMB/DSB/ISB） |
| 15:12 | SMC | RO | - | SMC 指令 |
| 11:8 | Writeback | RO | - | writeback 定址模式 |
| 7:4 | WithShifts | RO | - | 帶位移的指令 |
| 3:0 | Unpriv | RO | - | 非特權（T 變體）指令 |

### Enum: Barrier
- 0b0000: 僅 CP15 barrier 操作
- 0b0001: 加入 DMB/DSB/ISB 指令

### Enum: SMC
- 0b0000: 無
- 0b0001: 加入 SMC

### Enum: Writeback
- 0b0000: 基本支援
- 0b0001: 支援 ARMv7 全部 writeback 模式

### Enum: WithShifts
- 0b0000: 僅 MOV／shift 指令
- 0b0001: 載入／儲存 LSL 0-3
- 0b0011: 再加其他常數位移
- 0b0100: 再加暫存器控制位移

### Enum: Unpriv
- 0b0000: 無
- 0b0001: LDRBT/LDRT/STRBT/STRT
- 0b0010: 再加 H/SB/SH 形式

## ID_ISAR5
- Offset: 0x04C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「ID_ISAR5, Instruction Set Attribute Register 5, PMSA」— 位元切分依官方逐欄核對
- Description: Instruction Set Attribute Register 5 — 官方保留供未來擴充，全 32 位保留（MRC p15,0,Rt,c0,c2,5）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | RES0 | RO | - | 保留（官方標 UNK） |

## CCSIDR
- Offset: 0x050
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「CCSIDR, Cache Size ID Registers, PMSA」— 位元切分依官方逐欄核對＋Table B6-1
- Description: Cache Size ID Register — 由 CSSELR 選定之快取的架構參數（官方：僅為 set/way 維護所需的架構可見參數，不保證等於實際微架構；MRC p15,1,Rt,c0,c0,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | WT | RO | - | 支援 write-through |
| 30 | WB | RO | - | 支援 write-back |
| 29 | RA | RO | - | 支援 read-allocation |
| 28 | WA | RO | - | 支援 write-allocation |
| 27:13 | NumSets | RO | - | set 數 − 1（不必為 2 的冪） |
| 12:3 | Associativity | RO | - | 關聯度 − 1（不必為 2 的冪） |
| 2:0 | LineSize | RO | - | log2(每 line words) − 2（0 = 4 words） |

### Enum: WT
- 0: 不支援
- 1: 支援

### Enum: WB
- 0: 不支援
- 1: 支援

### Enum: RA
- 0: 不支援
- 1: 支援

### Enum: WA
- 0: 不支援
- 1: 支援

## CLIDR
- Offset: 0x054
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「CLIDR, Cache Level ID Register, PMSA」— 位元切分依官方逐欄核對＋Table B6-2
- Description: Cache Level ID Register — 各層快取型別與 LoC/LoU（MRC p15,1,Rt,c0,c0,1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:30 | RES0 | RO | - | 保留（官方標 UNK） |
| 29:27 | LoUU | RO | - | Level of Unification Uniprocessor |
| 26:24 | LoC | RO | - | Level of Coherence |
| 23:21 | LoUIS | RO | - | Level of Unification Inner Shareable（無多處理器擴充時 RAZ） |
| 20:18 | Ctype7 | RO | - | 第 7 層快取型別 |
| 17:15 | Ctype6 | RO | - | 第 6 層快取型別 |
| 14:12 | Ctype5 | RO | - | 第 5 層快取型別 |
| 11:9 | Ctype4 | RO | - | 第 4 層快取型別 |
| 8:6 | Ctype3 | RO | - | 第 3 層快取型別 |
| 5:3 | Ctype2 | RO | - | 第 2 層快取型別 |
| 2:0 | Ctype1 | RO | - | 第 1 層快取型別（讀到 0b000 後更外層皆無快取） |

### Enum: Ctype1
- 0b000: 無快取
- 0b001: 僅 I-cache
- 0b010: 僅 D-cache
- 0b011: 分離的 I 與 D cache
- 0b100: unified cache

## AIDR
- Offset: 0x058
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「AIDR, IMPLEMENTATION DEFINED Auxiliary ID Register, PMSA」— 位元切分依官方逐欄核對
- Description: Auxiliary ID Register — 實作定義的補充識別資訊，須與 MIDR 一併解讀（MRC p15,1,Rt,c0,c0,7）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | AIDR | RO | - | 實作定義。審查轉錄：Cortex-R5 r1p2 讀值為 0x00000000（Table 4-2，待親驗） |

## CSSELR
- Offset: 0x05C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「CSSELR, Cache Size Selection Register, PMSA」— 位元切分依官方逐欄核對
- Description: Cache Size Selection Register — 選擇 CCSIDR 要顯示哪一個快取（RW；MRC p15,2,Rt,c0,c0,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:4 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 3:1 | Level | RW | - | 快取層級。架構允許 0b000=L1…0b110=L7；Cortex-R5 僅有 L1（審查轉錄：本產品此欄唯讀、寫入忽略，待 TRM 親驗） |
| 0 | InD | RW | - | 指令／資料選擇 |

### Enum: InD
- 0: 資料或 unified cache
- 1: 指令 cache

## SCTLR
- Offset: 0x060
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「SCTLR, System Control Register, PMSA」— 位元位置與架構層讀值（RAO/RAZ）依官方逐欄核對；產品層分組與固定行為依 DDI 0460D §4.3.16 Table 4-24 審查轉錄（尚未親驗原文，各欄註明兩層出處）
- Description: System Control Register — 核心主控制（Reset 值依 VINITHIm／CFGEE／TEINIT 等組態接腳而異；MRC p15,0,Rt,c1,c0,0）。2026-08 第五輪審查套用 DDI 0460D Table 4-24 產品 overlay：保留段依產品表分組；SBO/SBZ 位 Access 標 RO——0406C.d 玻璃屋親驗：SBO/SBZ＝「硬體必須忽略寫入」，且軟體應寫全 1／全 0、否則須預期 UNPREDICTABLE；SBO/SBZ 本身不保證讀值，Reset 欄只在「架構層 RAO/RAZ 親驗」、「0406C.d Figure B6-1 reset 圖親驗」或「Table 4-24 明文」時才填（2026-08 R6 補：Figure B6-1 是逐位 reset 明文，證據力等同前者）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | IE | RO | - | 指令 endianness——產品層明文 RO，讀值由 CFGIE 接腳決定（Table 4-24 轉錄；IE=1 且 EE=0 為 UNPREDICTABLE） |
| 30 | TE | RW | - | 例外進入時的指令集狀態（reset 值＝TEINIT 接腳，轉錄） |
| 29 | AFE | RO | 0 | Access Flag Enable——R5 不使用：產品標 SBZ（轉錄）；架構層 RAZ（0406C 親驗）故讀 0 |
| 28 | TRE | RO | 0 | TEX Remap Enable——R5 不使用：產品標 SBZ（轉錄）；架構層 RAZ（0406C 親驗）故讀 0 |
| 27 | NMFI | RO | - | 不可遮罩 FIQ——產品層明文 RO，讀值由 CFGNMFIm 接腳決定（轉錄） |
| 26 | RESERVED | RO | 0 | 保留——產品 SBZ（轉錄）；架構層 RAZ/SBZP（親驗） |
| 25 | EE | RW | - | 例外時載入 CPSR.E 的值（reset 值＝CFGEE 接腳，轉錄） |
| 24 | VE | RW | 0 | 中斷向量化（實作定義的 FIQ/IRQ 向量；reset 0＝Table 4-24 明文，轉錄） |
| 23:22 | RESERVED | RO | 0b11 | 保留——產品表整段併標 SBO（轉錄，不再拆出架構 U 欄）；架構層 bit23 RAO/SBOP、bit22 U 恆 1（親驗）故讀 0b11 |
| 21 | FI | RO | 0 | Fast Interrupts 恆啟用——產品標 SBO（轉錄）：寫入忽略、軟體應寫 1 否則 UNPREDICTABLE（0406C 玻璃屋親驗）。reset 0＝0406C.d Figure B6-1（PMSAv7 SCTLR reset 圖，親驗）——SBO 是寫入規則，不牴觸架構 reset 值 |
| 20 | RESERVED | RO | 0 | 保留——產品 SBZ（轉錄）；架構層 RAZ/SBZP（親驗） |
| 19 | DZ | RW | 0 | 除以零產生 Undefined 例外（reset 0＝Table 4-24 明文，轉錄） |
| 18 | RESERVED | RO | 1 | 保留——產品 SBO（轉錄）；架構層 RAO/SBOP（親驗）故讀 1 |
| 17 | BR | RW | 0 | MPU 背景區域致能（reset 0＝0406C.d Figure B6-1 親驗；Table 4-24 未另給 reset） |
| 16 | RESERVED | RO | 1 | 保留——產品 SBO（轉錄）；架構層 RAO/SBOP（親驗）故讀 1 |
| 15 | RESERVED | RO | 0 | 保留——產品 SBZ（轉錄）；架構層 RAZ/SBZP（親驗） |
| 14 | RR | RW | 0 | cache 取代策略選擇（reset 0＝Table 4-24 明文，轉錄）。產品行為：無論此位為何，Cortex-R5 皆使用 random replacement——此位功能無效（Table 4-24 轉錄） |
| 13 | V | RW | - | 例外向量基底位址選擇（reset 值＝VINITHIm 接腳，轉錄） |
| 12 | I | RW | 0 | I-cache 全域致能（reset 0＝Table 4-24 明文；無 I-cache 組態時 SBZ，轉錄） |
| 11 | Z | RO | - | 分支預測——產品標 SBO（轉錄；2026-08 第五輪修正：舊版誤標 RW）：R5 恆支援分支預測、此位寫入忽略，實際預測策略由 ACTLR 控制。Reset 維持 `-`：Figure B6-1 將此位標 †（可為 RO 實作定義值、否則 reset 0——親驗，無單一定值） |
| 10 | SW | RW | 0 | SWP/SWPB 指令致能（1 時以完整 bus lock 執行；reset 0＝Table 4-24 明文，轉錄） |
| 9:7 | RESERVED | RO | 0 | 保留——產品表整段併標 SBZ（轉錄，不再拆出架構 B 欄）；架構層 [9:8] RAZ/SBZP、[7] B 恆 0（親驗）故讀 0 |
| 6:3 | RESERVED | RO | 0b1111 | 保留——產品表整段併標 SBO（轉錄，不再拆出架構 CP15BEN 欄）；架構層 [6]/[4:3] RAO/SBOP、[5] CP15BEN 兩情形皆 1（有實作→reset 1、未實作→RAO/WI；0406C §B6.1 條文＋Figure B6-1 親驗） |
| 2 | C | RW | 0 | D-cache／unified cache 全域致能（reset 0＝Table 4-24 明文；無 D-cache 組態時 SBZ，轉錄） |
| 1 | A | RW | 0 | 對齊檢查致能（reset 0＝Table 4-24 明文，轉錄） |
| 0 | M | RW | 0 | MPU 全域致能（reset 0＝Table 4-24 明文；無 MPU 組態時 SBZ，轉錄） |

### Enum: TE
- 0: 例外（含 reset）以 ARM 狀態進入
- 1: 例外（含 reset）以 Thumb 狀態進入

### Enum: NMFI
- 0: 軟體可設 CPSR.F 遮罩 FIQ
- 1: 軟體不可設 CPSR.F（FIQ 不可遮罩）

### Enum: EE
- 0: 例外時資料為 little-endian
- 1: 例外時資料為 big-endian

### Enum: VE
- 0: 使用向量表的 FIQ/IRQ 向量
- 1: 使用實作定義的 FIQ/IRQ 向量（VIC 埠）

### Enum: DZ
- 0: 除以零回傳 0，不產生例外
- 1: 除以零產生 Undefined 例外

### Enum: BR
- 0: 未命中任何 MPU 區域即 Background fault
- 1: 特權存取改用預設記憶體映射當背景區域

### Enum: RR
- 0: random replacement（Cortex-R5 實際策略）
- 1: 對 Cortex-R5 無效——仍為 random replacement（Table 4-24：此位不改變策略，轉錄）

### Enum: V
- 0: 低位例外向量（0x00000000）
- 1: 高位例外向量（0xFFFF0000）

### Enum: I
- 0: I-cache 關閉
- 1: I-cache 開啟

### Enum: SW
- 0: SWP/SWPB 為 UNDEFINED
- 1: SWP/SWPB 可用

### Enum: C
- 0: D-cache 關閉
- 1: D-cache 開啟

### Enum: A
- 0: 對齊檢查關閉
- 1: 對齊檢查開啟

### Enum: M
- 0: MPU 關閉
- 1: MPU 開啟

## ACTLR
- Offset: 0x064
- Reset: -
- Description: Auxiliary Control Register — Cortex-R5 的核心行為控制（dual issue／分支預測／cache・TCM ECC／AXI slave 等；MRC/MCR p15,0,Rt,c1,c0,1）。整表依 2026-08 交叉審查轉錄自 DDI 0460D §4.3.17 Table 4-25，尚未親驗原文——以此為據修改硬體設定前請先核對 TRM

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | DICDI | RW | - | 停用 dual issue（審查轉錄） |
| 30 | DIB2DI | RW | - | 停用 dual issue 分組 B2（審查轉錄） |
| 29 | DIB1DI | RW | - | 停用 dual issue 分組 B1（審查轉錄） |
| 28 | DIADI | RW | - | 停用 dual issue 分組 A（審查轉錄） |
| 27 | B1TCMPCEN | RW | - | B1TCM 同位／ECC 致能（審查轉錄） |
| 26 | B0TCMPCEN | RW | - | B0TCM 同位／ECC 致能（審查轉錄） |
| 25 | ATCMPCEN | RW | - | ATCM 同位／ECC 致能（審查轉錄） |
| 24 | AXISCEN | RW | - | AXI slave cache RAM 存取致能（審查轉錄） |
| 23 | AXISCUEN | RW | - | AXI slave 非特權 cache RAM 存取致能（審查轉錄） |
| 22 | DILSM | RW | - | 停用 low interrupt latency 於 load/store multiple（審查轉錄） |
| 21 | DEOLP | RW | - | 停用 end-of-loop 預測（審查轉錄） |
| 20 | DBHE | RW | - | 停用分支歷史（審查轉錄） |
| 19 | FRCDIS | RW | - | Fault 路徑組合邏輯停用（審查轉錄） |
| 18 | RES0 | RO | 0 | 保留（SBZ；審查轉錄） |
| 17 | RSDIS | RW | - | 停用 return stack（審查轉錄） |
| 16:15 | BP | RW | - | 分支預測策略（審查轉錄） |
| 14 | DBWR | RW | - | 停用 write burst（審查轉錄） |
| 13 | DLFO | RW | - | 停用 linefill 最佳化（審查轉錄） |
| 12 | ERPEG | RW | - | 隨機同位錯誤產生致能（驗證用；審查轉錄） |
| 11 | DNCH | RW | - | 停用 non-cacheable streaming 增強（審查轉錄） |
| 10 | FORA | RW | - | 強制 outer read allocate（審查轉錄） |
| 9 | FWT | RW | - | 強制 write-through（審查轉錄） |
| 8 | FDSnS | RW | - | 強制 D-cache non-shareable 時 write-through（審查轉錄） |
| 7 | sMOV | RW | - | 序列化 MOV 至 coprocessor（審查轉錄） |
| 6 | DILS | RW | - | 停用 low interrupt latency 於所有 load/store（審查轉錄） |
| 5:3 | CEC | RW | - | cache 錯誤控制（ECC／同位組態；審查轉錄） |
| 2 | B1TCMECEN | RW | - | B1TCM 外部錯誤致能（審查轉錄） |
| 1 | B0TCMECEN | RW | - | B0TCM 外部錯誤致能（審查轉錄） |
| 0 | ATCMECEN | RW | - | ATCM 外部錯誤致能（審查轉錄） |

### Enum: BP
- 0b00: 正常運作（動態分支預測）
- 0b01: 恆預測為 taken
- 0b10: 恆預測為 not taken
- 0b11: 保留

## CPACR
- Offset: 0x068
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「CPACR, Coprocessor Access Control Register, PMSA」— 位元切分依官方逐欄核對
- Description: Coprocessor Access Control Register — 協同處理器（FPU）存取權限（ARMv7 重置值為實作定義；MRC p15,0,Rt,c1,c0,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | ASEDIS | RO | - | 審查轉錄（R5 產品語意）：0=未配置 FPU；1=已配置 FPU 但無 Advanced SIMD（R5F 恆讀 1）。待 TRM Table 4-27 親驗 |
| 30 | D32DIS | RO | - | 審查轉錄（R5 產品語意）：0=未配置 FPU；1=已配置 FPU 但 D16–D31 不可用（R5F 為 VFPv3-D16，恆讀 1）。待 TRM 親驗 |
| 29:26 | RES0 | RO | 0 | 保留（官方標 UNK/SBZP） |
| 25:24 | RES0 | RO | 0 | cp12–cp13 存取權（ARMv7 未定義用途，官方建議 RAZ/WI） |
| 23:22 | cp11 | RW | - | cp11（FPU 資料傳輸）存取權限（重置值實作定義） |
| 21:20 | cp10 | RW | - | cp10（FPU）存取權限（重置值實作定義） |
| 19:0 | RES0 | RO | 0 | cp0–cp9 存取控制（R5 未實作這些協同處理器，RAZ/WI） |

### Enum: cp11
- 0b00: 拒絕存取（產生 Undefined 例外）
- 0b01: 僅特權模式可存取
- 0b10: 保留
- 0b11: 完全存取

### Enum: cp10
- 0b00: 拒絕存取（產生 Undefined 例外）
- 0b01: 僅特權模式可存取
- 0b10: 保留
- 0b11: 完全存取

## DFSR
- Offset: 0x06C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「DFSR, Data Fault Status Register, PMSA」— 位元位置依官方逐欄核對＋Table B5-8（PMSAv7 encodings）；產品欄名（SD/RW/S/Domain/Status）與 [9:4] 拆分依 DDI 0460D §4.3.20 Figure 4-31／Table 4-29 審查轉錄（尚未親驗原文）
- Description: Data Fault Status Register — 最近一次資料中止的狀態（與 DFAR 搭配）。官方屬性為 32-bit RW 暫存器（軟體可寫回，供 context save/restore；2026-08 審查修正：舊版誤標 RO）；MRC/MCR p15,0,Rt,c5,c0,0。2026-08 第五輪套用產品欄名：架構欄名 ExT/WnR/FS[4]/FS[3:0] 依 Table 4-29 改為 SD/RW/S/Status，並拆出 [9:8] 與 Domain[7:4]

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:13 | RESERVED | RO | - | 保留——SBZ、寫入忽略（架構層標 UNK/SBZP，親驗） |
| 12 | SD | RW | - | 外部中止子分類（僅 external abort 有效）：0＝AXI DECERR 或 AHB error、1＝AXI SLVERR 或不支援的 exclusive access；其他 abort 類型讀 0（產品欄名 Table 4-29 轉錄；架構欄名 ExT） |
| 11 | RW | RW | - | 0＝讀取造成、1＝寫入造成（產品欄名即「RW」，Table 4-29 轉錄；架構欄名 WnR） |
| 10 | S | RW | - | 故障狀態最高位（與 Status[3:0] 併讀；產品欄名 Table 4-29 轉錄；架構欄名 FS[4]） |
| 9:8 | RESERVED | RO | 0 | 恆讀 0、寫入忽略（Table 4-29 明文 always read 0／writes ignored，轉錄） |
| 7:4 | Domain | RO | - | 產品表仍列欄名 Domain，但 Cortex-R5 無 domains——SBZ、寫入忽略（Table 4-29 轉錄） |
| 3:0 | Status | RW | - | 故障狀態低四位（主編碼＝S:Status，產品 Table 4-28——DFSR/IFSR 共用編碼表，轉錄；external abort 再以 SD 分子類，SD 不併入主編碼）。enum 只列 Table 4-28 的八個產品編碼，未列的 S:Status 組合皆為保留 |

### Enum: RW
- 0: 由讀取指令造成
- 1: 由寫入指令造成

### Enum: Status
- 0b0000: S=0＝背景故障（未命中任何 MPU 區域，DFAR 有效）／S=1＝保留
- 0b0001: S=0＝對齊故障（DFAR 有效）／S=1＝保留
- 0b0010: S=0＝watchpoint 除錯事件（v7 Debug 時 DFAR 為 UNKNOWN）／S=1＝保留
- 0b0110: S=0＝保留／S=1＝非同步外部中止（DFAR 為 UNKNOWN）
- 0b1000: S=0＝同步外部中止（DFAR 有效）／S=1＝非同步同位/ECC 錯誤（DFAR 為 UNKNOWN）
- 0b1001: S=0＝保留／S=1＝同步同位/ECC 錯誤
- 0b1101: S=0＝權限故障（MPU，DFAR 有效）／S=1＝保留

## IFSR
- Offset: 0x070
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「IFSR, Instruction Fault Status Register, PMSA」— 位元位置依官方逐欄核對＋Table B5-7（PMSAv7 encodings）；產品欄名（SD/S/Domain/Status）與 [9:4] 拆分依 DDI 0460D §4.3.20 Figure 4-32／Table 4-30 審查轉錄（尚未親驗原文）
- Description: Instruction Fault Status Register — 最近一次 Prefetch Abort 的狀態（與 IFAR 搭配）。官方屬性為 32-bit RW 暫存器（2026-08 審查修正：舊版誤標 RO）；MRC/MCR p15,0,Rt,c5,c0,1。2026-08 第五輪套用產品欄名：架構欄名 ExT/FS[4]/FS[3:0] 依 Table 4-30 改為 SD/S/Status，並拆出 [9:8] 與 Domain[7:4]

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:13 | RESERVED | RO | - | 保留——SBZ、寫入忽略（架構層標 UNK/SBZP，親驗） |
| 12 | SD | RW | - | 外部中止子分類（僅 external abort 有效）：0＝AXI DECERR、1＝AXI SLVERR；其他 abort 類型讀 0（產品欄名 Table 4-30 轉錄；架構欄名 ExT） |
| 11 | RESERVED | RO | - | 保留——SBZ（Table 4-30 轉錄） |
| 10 | S | RW | - | 故障狀態最高位（與 Status[3:0] 併讀；產品欄名 Table 4-30 轉錄；架構欄名 FS[4]） |
| 9:8 | RESERVED | RO | - | 保留——SBZ（Table 4-30 未如 DFSR 明寫 always-read-0，Reset 不填；轉錄） |
| 7:4 | Domain | RO | - | 產品表仍列欄名 Domain，但 Cortex-R5 無 domains——SBZ（Table 4-30 轉錄） |
| 3:0 | Status | RW | - | 故障狀態低四位（主編碼＝S:Status，產品 Table 4-28——DFSR/IFSR 共用編碼表，轉錄；external abort 再以 SD 分子類）。enum 只列 Table 4-28 的八個產品編碼，未列的 S:Status 組合皆為保留 |

### Enum: Status
- 0b0000: S=0＝背景故障（未命中任何 MPU 區域，IFAR 有效）／S=1＝保留
- 0b0001: S=0＝對齊故障（IFAR 有效）／S=1＝保留
- 0b0010: S=0＝產生 Prefetch Abort 的除錯事件（IFAR 為 UNKNOWN）／S=1＝保留
- 0b0110: S=0＝保留／S=1＝非同步外部中止（Table 4-28 為 DFSR/IFSR 共用編碼表，轉錄；非同步中止時 IFAR 為 UNKNOWN——架構慣例）
- 0b1000: S=0＝同步外部中止（IFAR 有效）／S=1＝非同步同位/ECC 錯誤（Table 4-28 轉錄）
- 0b1001: S=0＝保留／S=1＝同步同位/ECC 錯誤（IFAR 有效）
- 0b1101: S=0＝權限故障（MPU，IFAR 有效）／S=1＝保留

## ADFSR
- Offset: 0x074
- Reset: -
- Description: Auxiliary Data Fault Status Register — 資料側同位／ECC 錯誤的定位資訊（來源、cache way、index、可否恢復；MRC/MCR p15,0,Rt,c5,c1,0）。整表依 2026-08 交叉審查轉錄自 DDI 0460D Figure 4-33／Table 4-31/4-32，尚未親驗原文

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | RES0 | RO | 0 | 保留（SBZ；審查轉錄） |
| 27:24 | CacheWay | RW | - | 發生錯誤的 cache way（審查轉錄） |
| 23:22 | Side | RW | - | 錯誤來源側（cache／TCM／AXI 等分類與 SideExt 併讀；審查轉錄） |
| 21 | Recoverable | RW | - | 錯誤可否恢復（審查轉錄） |
| 20 | SideExt | RW | - | 錯誤來源側擴充位（審查轉錄） |
| 19:14 | RES0 | RO | 0 | 保留（SBZ；審查轉錄） |
| 13:5 | Index | RW | - | 發生錯誤的 index（審查轉錄） |
| 4:0 | RES0 | RO | 0 | 保留（SBZ；審查轉錄） |

## AIFSR
- Offset: 0x078
- Reset: -
- Description: Auxiliary Instruction Fault Status Register — 指令側同位／ECC 錯誤的定位資訊（來源、cache way、index、可否恢復；MRC/MCR p15,0,Rt,c5,c1,1）。整表依 2026-08 交叉審查轉錄自 DDI 0460D Figure 4-33／Table 4-31/4-32，尚未親驗原文

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | RES0 | RO | 0 | 保留（SBZ；審查轉錄） |
| 27:24 | CacheWay | RW | - | 發生錯誤的 cache way（審查轉錄） |
| 23:22 | Side | RW | - | 錯誤來源側（cache／TCM／AXI 等分類與 SideExt 併讀；審查轉錄） |
| 21 | Recoverable | RW | - | 錯誤可否恢復（審查轉錄） |
| 20 | SideExt | RW | - | 錯誤來源側擴充位（審查轉錄） |
| 19:14 | RES0 | RO | 0 | 保留（SBZ；審查轉錄） |
| 13:5 | Index | RW | - | 發生錯誤的 index（審查轉錄） |
| 4:0 | RES0 | RO | 0 | 保留（SBZ；審查轉錄） |

## DFAR
- Offset: 0x07C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「DFAR, Data Fault Address Register, PMSA」— 位元切分依官方逐欄核對
- Description: Data Fault Address Register — 造成同步資料中止的位址（有效性見 DFSR 的 S:Status 主編碼各項說明；external abort 子類另看 DFSR.SD。MRC p15,0,Rt,c6,c0,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | Address | RW | - | 故障位址（VA） |

## IFAR
- Offset: 0x080
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「IFAR, Instruction Fault Address Register, PMSA」— 位元切分依官方逐欄核對
- Description: Instruction Fault Address Register — 造成 Prefetch Abort 的指令位址（有效性見 IFSR 的 S:Status 主編碼各項說明；external abort 子類另看 IFSR.SD。MRC p15,0,Rt,c6,c0,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | Address | RW | - | 故障位址（VA） |

## RGNR
- Offset: 0x084
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「RGNR, MPU Region Number Register, PMSA」— 位元切分依官方逐欄核對
- Description: MPU Region Number Register — 選擇 DRBAR／DRSR／DRACR 目前操作的區域編號（0 起算；寫入超過實作區域數為 UNPREDICTABLE；MRC p15,0,Rt,c6,c2,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:4 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 3:0 | Region | RW | - | 目前區域編號（官方規則：欄寬 = log2(區域數) 向上取整；R5 為 12 或 16 區 → 4 bits。2026-08 審查修正：舊版以 8 bits 呈現） |

## DRBAR
- Offset: 0x088
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「DRBAR, Data Region Base Address Register, PMSA」— 位元切分依官方逐欄核對
- Description: Data Region Base Address Register — 由 RGNR 選定區域的基底位址（區域大小見 DRSR；基底須對齊區域大小；MRC p15,0,Rt,c6,c1,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:5 | Base | RW | - | 區域基底實體位址 [31:5]（最小區域 32 bytes） |
| 4:0 | RES0 | RO | 0 | 保留（官方標 SBZ） |

## DRSR
- Offset: 0x08C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「DRSR, Data Region Size and Enable Register, PMSA」— 位元切分依官方逐欄核對
- Description: Data Region Size and Enable Register — 由 RGNR 選定區域的大小、子區域停用與致能（區域 <256B 時 SnD 欄不定義；官方：大小 = 2^(RSize+1) bytes；MRC p15,0,Rt,c6,c1,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:16 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 15 | S7D | RW | - | 子區域 7 停用 |
| 14 | S6D | RW | - | 子區域 6 停用 |
| 13 | S5D | RW | - | 子區域 5 停用 |
| 12 | S4D | RW | - | 子區域 4 停用 |
| 11 | S3D | RW | - | 子區域 3 停用 |
| 10 | S2D | RW | - | 子區域 2 停用 |
| 9 | S1D | RW | - | 子區域 1 停用 |
| 8 | S0D | RW | - | 子區域 0 停用 |
| 7:6 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 5:1 | RSize | RW | - | 區域大小（0 保留且 UNPREDICTABLE；大小 = 2^(RSize+1) bytes） |
| 0 | En | RW | 0 | 區域致能（官方 §B5.3：重置時所有區域停用） |

### Enum: RSize
- 0b00100: 32 bytes
- 0b00101: 64 bytes
- 0b00110: 128 bytes
- 0b00111: 256 bytes
- 0b01000: 512 bytes
- 0b01001: 1 KB
- 0b01010: 2 KB
- 0b01011: 4 KB
- 0b01100: 8 KB
- 0b01101: 16 KB
- 0b01110: 32 KB
- 0b01111: 64 KB
- 0b10000: 128 KB
- 0b10001: 256 KB
- 0b10010: 512 KB
- 0b10011: 1 MB
- 0b10100: 2 MB
- 0b10101: 4 MB
- 0b10110: 8 MB
- 0b10111: 16 MB
- 0b11000: 32 MB
- 0b11001: 64 MB
- 0b11010: 128 MB
- 0b11011: 256 MB
- 0b11100: 512 MB
- 0b11101: 1 GB
- 0b11110: 2 GB
- 0b11111: 4 GB

### Enum: En
- 0: 區域停用
- 1: 區域啟用

### Enum: S0D
- 0: 子區域屬於此區域
- 1: 子區域被排除

## DRACR
- Offset: 0x090
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「DRACR, Data Region Access Control Register, PMSA」— 位元切分依官方逐欄核對＋§B5.2/§B5.3（AP／TEX,C,B 編碼）
- Description: Data Region Access Control Register — 由 RGNR 選定區域的權限與記憶體屬性（MRC p15,0,Rt,c6,c1,4）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:13 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 12 | XN | RW | - | 禁止執行（execute-never） |
| 11 | RES0 | RO | - | 保留 |
| 10:8 | AP | RW | - | 存取權限（官方 §B5.2 Access permissions） |
| 7:6 | RES0 | RO | - | 保留 |
| 5:3 | TEX | RW | - | 記憶體型別擴充（與 C、B 併讀，官方 §B5.3） |
| 2 | S | RW | - | Shareable（僅 Normal memory 有意義） |
| 1 | C | RW | - | 記憶體屬性 C（與 TEX、B 併讀） |
| 0 | B | RW | - | 記憶體屬性 B（與 TEX、C 併讀） |

### Enum: XN
- 0: 區域可含可執行碼
- 1: 區域禁止取指

### Enum: AP
- 0b000: 特權與非特權皆不可存取
- 0b001: 僅特權可讀寫
- 0b010: 特權可讀寫；非特權唯讀
- 0b011: 特權與非特權皆可讀寫
- 0b101: 僅特權唯讀
- 0b110: 特權與非特權皆唯讀

### Enum: S
- 0: Normal memory 為 Non-shareable
- 1: Normal memory 為 Shareable

## PMCR
- Offset: 0x094
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMCR, Performance Monitors Control Register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Control Register — PMU 實作資訊與總控制（官方：DP/X/D/E 重置為 0；MRC p15,0,Rt,c9,c12,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:24 | IMP | RO | - | 實作者代碼（同 MIDR[31:24] 的解讀） |
| 23:16 | IDCODE | RO | - | 識別碼（實作者自行維護的清單） |
| 15:11 | N | RO | - | 事件計數器數量（0b00000 = 只有 PMCCNTR） |
| 10:6 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 5 | DP | RW | 0 | 非侵入式除錯未授權時停用 PMCCNTR |
| 4 | X | RW | 0 | 事件匯出致能（無事件匯流排時 RAZ/WI） |
| 3 | D | RW | 0 | PMCCNTR 時脈除頻 |
| 2 | C | WO | - | 寫 1 將 PMCCNTR 歸零（讀恆 0；不清除溢位旗標） |
| 1 | P | WO | - | 寫 1 將全部事件計數器歸零（讀恆 0；不含 PMCCNTR） |
| 0 | E | RW | 0 | 全部計數器（含 PMCCNTR）總致能 |

### Enum: D
- 0: PMCCNTR 每個時脈遞增
- 1: PMCCNTR 每 64 個時脈遞增

### Enum: E
- 0: 全部計數器停用
- 1: 全部計數器啟用

## PMCNTENSET
- Offset: 0x098
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMCNTENSET, Performance Monitors Count Enable Set register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Count Enable Set — 各計數器的致能（讀出目前致能狀態；寫 1 設定、寫 0 無效；本表以 3 個事件計數器呈現，實際數量見 PMCR.N；MRC p15,0,Rt,c9,c12,1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | C | RW | - | PMCCNTR（cycle counter）致能 |
| 30:3 | RES0 | RO | - | 保留（超出實作計數器數的位元 RAZ/WI） |
| 2 | P2 | RW | - | 事件計數器 2 致能 |
| 1 | P1 | RW | - | 事件計數器 1 致能 |
| 0 | P0 | RW | - | 事件計數器 0 致能 |

### Enum: C
- 0: PMCCNTR 停用
- 1: PMCCNTR 啟用

## PMCNTENCLR
- Offset: 0x09C
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMCNTENCLR, Performance Monitors Count Enable Clear register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Count Enable Clear — 寫 1 清除對應計數器致能（讀出目前致能狀態，與 PMCNTENSET 同一組狀態；MRC p15,0,Rt,c9,c12,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | C | RW | - | 寫 1 停用 PMCCNTR |
| 30:3 | RES0 | RO | - | 保留（超出實作計數器數的位元 RAZ/WI） |
| 2 | P2 | RW | - | 寫 1 停用事件計數器 2 |
| 1 | P1 | RW | - | 寫 1 停用事件計數器 1 |
| 0 | P0 | RW | - | 寫 1 停用事件計數器 0 |

## PMOVSR
- Offset: 0x0A0
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMOVSR, Performance Monitors Overflow Flag Status Register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Overflow Flag Status — 各計數器的溢位旗標（寫 1 清除；MRC p15,0,Rt,c9,c12,3）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | C | RW | - | PMCCNTR 溢位旗標 |
| 30:3 | RES0 | RO | - | 保留（超出實作計數器數的位元 RAZ/WI） |
| 2 | P2 | RW | - | 事件計數器 2 溢位旗標 |
| 1 | P1 | RW | - | 事件計數器 1 溢位旗標 |
| 0 | P0 | RW | - | 事件計數器 0 溢位旗標 |

## PMSELR
- Offset: 0x0A4
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMSELR, Performance Monitors Event Counter Selection Register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Event Counter Selection — 選擇 PMXEVTYPER／PMXEVCNTR 操作的事件計數器（PMUv2 下 0b11111 選 PMCCNTR 供 PMXEVTYPER 讀 0x1F；MRC p15,0,Rt,c9,c12,5）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:5 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 4:0 | SEL | RW | - | 事件計數器編號（0 到 PMCR.N−1） |

## PMCEID0
- Offset: 0x0A8
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMCEID0 and PMCEID1, Performance Monitors Common Event ID registers, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Common Event ID 0 — 事件編號 0x00–0x1F 各自是否支援（bit n = 事件 n；MRC p15,0,Rt,c9,c12,6）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | CE | RO | - | bit n = 1 表示支援共通事件 n（事件定義見官方 §C12.8） |

## PMCEID1
- Offset: 0x0AC
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMCEID0 and PMCEID1, Performance Monitors Common Event ID registers, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Common Event ID 1 — 事件編號 0x20–0x3F 各自是否支援（bit n = 事件 0x20+n；MRC p15,0,Rt,c9,c12,7）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | CE | RO | - | bit n = 1 表示支援共通事件 0x20+n |

## PMCCNTR
- Offset: 0x0B0
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMCCNTR, Performance Monitors Cycle Count Register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Cycle Count — 週期計數器（受 PMCR.E／PMCNTENSET.C 控制，PMCR.D 選擇除頻；MRC p15,0,Rt,c9,c13,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | CCNT | RW | - | 週期計數值 |

## PMXEVTYPER
- Offset: 0x0B4
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMXEVTYPER, Performance Monitors Event Type Select Register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Event Type Select — 由 PMSELR 選定計數器要數的事件（選到 PMCCNTR（SEL=31）時本欄保留；MRC p15,0,Rt,c9,c13,1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:8 | RES0 | RO | - | 保留（官方標 UNK/SBZP；PMUv2 的 P/U 過濾位在 R profile 無安全擴充時不適用） |
| 7:0 | evtCount | RW | - | 事件編號（官方 §C12.8 共通事件 ＋ 實作定義事件） |

## PMXEVCNTR
- Offset: 0x0B8
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMXEVCNTR, Performance Monitors Event Count Register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Event Count — 由 PMSELR 選定的事件計數器值（MRC p15,0,Rt,c9,c13,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | ECNT | RW | - | 事件計數值 |

## PMUSERENR
- Offset: 0x0BC
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMUSERENR, Performance Monitors User Enable Register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors User Enable — 允許 User mode 存取 PMU（User mode 讀本暫存器恆可；MRC p15,0,Rt,c9,c14,0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:1 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 0 | EN | RW | 0 | User mode 存取 PMU 致能 |

### Enum: EN
- 0: User mode 不可存取 PMU
- 1: User mode 可存取 PMU

## PMINTENSET
- Offset: 0x0C0
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMINTENSET, Performance Monitors Interrupt Enable Set register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Interrupt Enable Set — 各計數器溢位中斷致能（寫 1 設定；MRC p15,0,Rt,c9,c14,1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | C | RW | - | PMCCNTR 溢位中斷致能 |
| 30:3 | RES0 | RO | - | 保留（超出實作計數器數的位元 RAZ/WI） |
| 2 | P2 | RW | - | 事件計數器 2 溢位中斷致能 |
| 1 | P1 | RW | - | 事件計數器 1 溢位中斷致能 |
| 0 | P0 | RW | - | 事件計數器 0 溢位中斷致能 |

## PMINTENCLR
- Offset: 0x0C4
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「PMINTENCLR, Performance Monitors Interrupt Enable Clear register, PMSA」— 位元切分依官方逐欄核對
- Description: Performance Monitors Interrupt Enable Clear — 寫 1 清除對應溢位中斷致能（與 PMINTENSET 同一組狀態；MRC p15,0,Rt,c9,c14,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | C | RW | - | 寫 1 停用 PMCCNTR 溢位中斷 |
| 30:3 | RES0 | RO | - | 保留（超出實作計數器數的位元 RAZ/WI） |
| 2 | P2 | RW | - | 寫 1 停用事件計數器 2 溢位中斷 |
| 1 | P1 | RW | - | 寫 1 停用事件計數器 1 溢位中斷 |
| 0 | P0 | RW | - | 寫 1 停用事件計數器 0 溢位中斷 |

## ATCMRR
- Offset: 0x0C8
- Reset: -
- Description: ATCM Region Register — ATCM 基底位址、大小與致能。編碼為 c9,c1,1（MRC p15,0,Rt,c9,c1,1；2026-08 交叉審查修正：舊版誤植為 c9,c1,0，正確編碼經 DDI 0460D Table 4-44 與 AMD/Xilinx 官方 R5 BSP（xreg_cortexr5.h）雙重確認）。欄位切分依審查轉錄自 DDI 0460D Table 4-44，尚未親驗原文

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:12 | Base | RW | - | ATCM 區域基底位址（對齊 TCM 大小） |
| 11:7 | RES0 | RO | - | 讀為 UNP、寫入須為 0（審查轉錄） |
| 6:2 | Size | RO | - | ATCM 大小（唯讀，寫入忽略；0=0KB、3=4KB…13=4MB，2^(Size+9) bytes；審查轉錄） |
| 1 | RES0 | RO | 0 | 保留（SBZ） |
| 0 | En | RW | - | ATCM 致能 |

### Enum: En
- 0: ATCM 停用
- 1: ATCM 啟用

## BTCMRR
- Offset: 0x0CC
- Reset: -
- Description: BTCM Region Register — BTCM 基底位址、大小與致能。編碼為 c9,c1,0（MRC p15,0,Rt,c9,c1,0；2026-08 交叉審查修正：舊版誤植為 c9,c1,1，正確編碼經 DDI 0460D Table 4-43 與 AMD/Xilinx 官方 R5 BSP（xreg_cortexr5.h）雙重確認）。欄位切分依審查轉錄自 DDI 0460D Table 4-43，尚未親驗原文

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:12 | Base | RW | - | BTCM 區域基底位址（對齊 TCM 大小） |
| 11:7 | RES0 | RO | - | 讀為 UNP、寫入須為 0（審查轉錄） |
| 6:2 | Size | RO | - | BTCM 大小（唯讀，寫入忽略；同 ATCMRR 編碼；審查轉錄） |
| 1 | RES0 | RO | 0 | 保留（SBZ） |
| 0 | En | RW | - | BTCM 致能 |

### Enum: En
- 0: BTCM 停用
- 1: BTCM 啟用

## CONTEXTIDR
- Offset: 0x0D0
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「CONTEXTIDR, Context ID Register, PMSA」— 位元切分依官方逐欄核對
- Description: Context ID Register — 目前 context 識別碼，供 debug／trace 判別目前程序（舊文件稱 Process ID Register；MRC p15,0,Rt,c13,c0,1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | ContextID | RW | - | 目前程序的唯一識別值 |

## TPIDRURW
- Offset: 0x0D4
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「TPIDRURW, User Read/Write Thread ID Register, PMSA」— 位元切分依官方逐欄核對
- Description: User Read/Write Thread ID Register — 軟體自由使用的執行緒識別（User 可讀寫；硬體永不更新；MRC p15,0,Rt,c13,c0,2）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | TID | RW | - | 軟體定義（典型為 TLS 指標） |

## TPIDRURO
- Offset: 0x0D8
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「TPIDRURO, User Read-Only Thread ID Register, PMSA」— 位元切分依官方逐欄核對
- Description: User Read-Only Thread ID Register — User 唯讀、PL1 可寫的執行緒識別（硬體永不更新；MRC p15,0,Rt,c13,c0,3）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | TID | RW | - | 軟體定義 |

## TPIDRPRW
- Offset: 0x0DC
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「TPIDRPRW, PL1 only Thread ID Register, PMSA」— 位元切分依官方逐欄核對
- Description: PL1 only Thread ID Register — 僅特權可見的執行緒識別（硬體永不更新；MRC p15,0,Rt,c13,c0,4）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:0 | TID | RW | - | 軟體定義（典型為 OS 的 per-CPU/thread 結構指標） |

## CPSR
- Offset: 0x0E0
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B1.3.3「Program Status Registers (PSRs)」— 位元切分依官方逐欄核對
- Description: Current Program Status Register — 目前處理器狀態（模式、遮罩、條件旗標；非 CP15，經 MRS 讀出）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | N | RW | - | 負數條件旗標 |
| 30 | Z | RW | - | 零條件旗標 |
| 29 | C | RW | - | 進位條件旗標 |
| 28 | V | RW | - | 溢位條件旗標 |
| 27 | Q | RW | - | 累積飽和旗標 |
| 26:25 | IT[1:0] | RW | - | IT 執行狀態低 2 位（官方：IT[7:0] 分佈於 bits[15:10,26:25]） |
| 24 | J | RW | - | Jazelle 執行狀態（與 T 併讀決定指令集狀態） |
| 23:20 | RES0 | RO | 0 | 保留（官方標 RAZ/SBZP） |
| 19:16 | GE | RW | - | SIMD Greater-than-or-Equal 旗標 |
| 15:10 | IT[7:2] | RW | - | IT 執行狀態高 6 位 |
| 9 | E | RW | - | 資料存取 endianness（取指不受影響） |
| 8 | A | RW | - | 非同步中止遮罩 |
| 7 | I | RW | - | IRQ 遮罩 |
| 6 | F | RW | - | FIQ 遮罩（NMFI 時軟體不可設 1） |
| 5 | T | RW | - | Thumb 執行狀態（與 J 併讀） |
| 4:0 | M | RW | - | 處理器模式（保留值 UNPREDICTABLE） |

### Enum: E
- 0: 資料 little-endian
- 1: 資料 big-endian

### Enum: A
- 0: 非同步中止未遮罩
- 1: 非同步中止已遮罩

### Enum: I
- 0: IRQ 未遮罩
- 1: IRQ 已遮罩

### Enum: F
- 0: FIQ 未遮罩
- 1: FIQ 已遮罩

### Enum: T
- 0: ARM 狀態（J=0 時）
- 1: Thumb 狀態（J=0 時）

### Enum: M
- 0b10000: User
- 0b10001: FIQ
- 0b10010: IRQ
- 0b10011: Supervisor
- 0b10111: Abort
- 0b11011: Undefined
- 0b11111: System

## FPSID
- Offset: 0x0E4
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「FPSID, Floating-point System ID Register, PMSA」— 位元切分依官方逐欄核對
- Description: Floating-point System ID Register — FPU 識別（僅 R5F 有 FPU；VMRS Rt,FPSID）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:24 | Implementer | RO | - | 實作者代碼（同 MIDR 的編碼；ARM = 0x41） |
| 23 | SW | RO | - | 純軟體模擬指示 |
| 22:16 | Subarch | RO | - | 子架構版本（ARM 設計者最高位為 0） |
| 15:8 | PartNum | RO | - | FPU 部件編號（實作定義） |
| 7:4 | Variant | RO | - | 變體（實作定義） |
| 3:0 | Revision | RO | - | 版本（實作定義） |

### Enum: SW
- 0: 硬體支援浮點指令
- 1: 僅軟體模擬

### Enum: Subarch
- 0b0000010: VFPv3/v4 的 Common VFP subarchitecture v2
- 0b0000011: VFPv3/v4，null subarchitecture（無支援碼）
- 0b0000100: 如 0b0000011 並支援 trap 例外

## FPSCR
- Offset: 0x0E8
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「FPSCR, Floating-point Status and Control Register, PMSA」— 位元切分依官方逐欄核對
- Description: Floating-point Status and Control Register — 浮點旗標、模式與例外狀態（VMRS Rt,FPSCR）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | N | RW | - | 浮點比較：負數 |
| 30 | Z | RW | - | 浮點比較：零 |
| 29 | C | RW | - | 浮點比較：進位 |
| 28 | V | RW | - | 浮點比較：溢位 |
| 27 | QC | RO | - | SIMD 累積飽和 — R5F 無 Advanced SIMD，架構層 UNK/SBZP；審查轉錄稱產品為 DNM/RAZ（待 TRM 親驗） |
| 26 | AHP | RO | - | 半精度格式選擇 — R5F 無半精度擴充；審查轉錄稱產品為 DNM/RAZ（待 TRM 親驗） |
| 25 | DN | RW | - | Default NaN 模式 |
| 24 | FZ | RW | - | Flush-to-zero 模式 |
| 23:22 | RMode | RW | - | 捨入模式 |
| 21:20 | Stride | RW | - | 官方已棄用（VFP 向量模式遺留） |
| 19 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 18:16 | Len | RW | - | 官方已棄用（VFP 向量模式遺留） |
| 15 | IDE | RO | 0 | Input Denormal 例外 trap 致能 — R5F 為 VFPv3（非 U 變體），此位 RAZ/WI（DDI 0406C.d 親驗：僅 VFPv2/VFPv3U/VFPv4U 支援 trap） |
| 14:13 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 12 | IXE | RO | 0 | Inexact 例外 trap 致能 — R5F 為 VFPv3（非 U 變體），此位 RAZ/WI（DDI 0406C.d 親驗：僅 VFPv2/VFPv3U/VFPv4U 支援 trap） |
| 11 | UFE | RO | 0 | Underflow 例外 trap 致能 — R5F 為 VFPv3（非 U 變體），此位 RAZ/WI（DDI 0406C.d 親驗：僅 VFPv2/VFPv3U/VFPv4U 支援 trap） |
| 10 | OFE | RO | 0 | Overflow 例外 trap 致能 — R5F 為 VFPv3（非 U 變體），此位 RAZ/WI（DDI 0406C.d 親驗：僅 VFPv2/VFPv3U/VFPv4U 支援 trap） |
| 9 | DZE | RO | 0 | Division by Zero 例外 trap 致能 — R5F 為 VFPv3（非 U 變體），此位 RAZ/WI（DDI 0406C.d 親驗：僅 VFPv2/VFPv3U/VFPv4U 支援 trap） |
| 8 | IOE | RO | 0 | Invalid Operation 例外 trap 致能 — R5F 為 VFPv3（非 U 變體），此位 RAZ/WI（DDI 0406C.d 親驗：僅 VFPv2/VFPv3U/VFPv4U 支援 trap） |
| 7 | IDC | RW | - | Input Denormal 累積例外旗標 |
| 6:5 | RES0 | RO | - | 保留（官方標 UNK/SBZP） |
| 4 | IXC | RW | - | Inexact 累積例外旗標 |
| 3 | UFC | RW | - | Underflow 累積例外旗標 |
| 2 | OFC | RW | - | Overflow 累積例外旗標 |
| 1 | DZC | RW | - | Division by Zero 累積例外旗標 |
| 0 | IOC | RW | - | Invalid Operation 累積例外旗標 |

### Enum: AHP
- 0: IEEE 半精度格式
- 1: 替代半精度格式

### Enum: DN
- 0: NaN 運算元照常傳遞
- 1: 任何 NaN 輸入輸出 Default NaN

### Enum: FZ
- 0: 完全符合 IEEE 754
- 1: Flush-to-zero 模式

### Enum: RMode
- 0b00: Round to Nearest（RN）
- 0b01: Round towards Plus Infinity（RP)
- 0b10: Round towards Minus Infinity（RM）
- 0b11: Round towards Zero（RZ）

## FPEXC
- Offset: 0x0EC
- Reset: -
- Description: Floating-Point Exception Control Register — FPU 總開關與例外狀態（VMRS Rt,FPEXC；僅 R5F）。2026-08 交叉審查修正：架構通用版的 EX[31]＋SUBARCH[29:0] 在 Cortex-R5F 不成立——產品切分依審查轉錄自 DDI 0460D §11.3.3 Table 11-6（bit31 RAZ、bit29 為 DEX），Linux kernel 的 FPEXC_DEX=(1<<29) 佐證，尚未親驗原文

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31 | RES0 | RO | 0 | R5F 讀為 0（架構的 EX 位在本產品 RAZ；審查轉錄） |
| 30 | EN | RW | 0 | FPU 總致能（0 時多數浮點指令 UNDEFINED） |
| 29 | DEX | RW | 0 | Defined synchronous instruction exceptional flag — 嘗試執行未定義的向量運算時置 1（審查轉錄；Linux FPEXC_DEX 佐證） |
| 28:0 | RES0 | RO | 0 | R5F 讀為 0（審查轉錄） |

### Enum: EN
- 0: FPU 停用（浮點指令產生 Undefined 例外）
- 1: FPU 啟用

## MVFR0
- Offset: 0x0F0
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「MVFR0, Media and VFP Feature Register 0, PMSA」— 位元切分依官方逐欄核對
- Description: Media and VFP Feature Register 0 — FPU 能力識別（單/倍精度、除法、開方、trap 支援；僅 R5F；VMRS Rt,MVFR0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | RMode | RO | - | 支援的捨入模式 |
| 27:24 | ShortVec | RO | - | VFP short vector 支援 |
| 23:20 | Sqrt | RO | - | 硬體開方（VSQRT）支援 |
| 19:16 | Divide | RO | - | 硬體除法（VDIV）支援 |
| 15:12 | TrapExc | RO | - | 例外 trap 支援（官方：VFPv3/VFPv4 此欄為 0） |
| 11:8 | DP | RO | - | 倍精度支援 |
| 7:4 | SP | RO | - | 單精度支援 |
| 3:0 | SIMDReg | RO | - | Advanced SIMD 暫存器組 |

### Enum: RMode
- 0b0000: 僅 Round to Nearest（VCVT 例外地支援 RZ）
- 0b0001: 支援全部捨入模式

### Enum: TrapExc
- 0b0000: 不支援 trap（VFPv3/VFPv4 固定值）
- 0b0001: 支援例外 trap

### Enum: DP
- 0b0000: 硬體不支援倍精度
- 0b0001: 支援倍精度

### Enum: SP
- 0b0000: 硬體不支援單精度
- 0b0001: 支援單精度

### Enum: SIMDReg
- 0b0000: 不支援
- 0b0001: 支援 16×64-bit 暫存器組

## MVFR1
- Offset: 0x0F4
- Reset: -
- Verified: ARM DDI 0406C.d（ARMv7-A/R 架構手冊） §B6.1「MVFR1, Media and VFP Feature Register 1, PMSA」— 位元切分依官方逐欄核對
- Description: Media and VFP Feature Register 1 — FMAC／半精度／SIMD／NaN・FtZ 模式識別（僅 R5F；VMRS Rt,MVFR1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:28 | SIMDFMAC | RO | - | 融合乘加（FMA）指令支援 |
| 27:24 | VFPHPFP | RO | - | VFP 半精度轉換指令支援 |
| 23:20 | SIMDHPFP | RO | - | Advanced SIMD 半精度支援 |
| 19:16 | SIMDSPFP | RO | - | Advanced SIMD 單精度支援 |
| 15:12 | SIMDInt | RO | - | Advanced SIMD 整數指令支援 |
| 11:8 | SIMDLS | RO | - | Advanced SIMD 載入／儲存支援 |
| 7:4 | DNaN | RO | - | NaN 傳遞模式支援 |
| 3:0 | FtZ | RO | - | Flush-to-Zero 模式支援 |

### Enum: DNaN
- 0b0000: 硬體僅支援 Default NaN 模式
- 0b0001: 硬體支援 NaN 值傳遞

### Enum: FtZ
- 0b0000: 硬體僅支援 Flush-to-Zero 模式
- 0b0001: 硬體支援完整 denormalized 運算
