# CPU: ARM Cortex-A55
# Version: r2p0 · ARMv8.2-A AArch64
# Width: 64
# Source: Arm Architecture Reference Manual for A-profile (ARM DDI 0487)／Cortex-A55 TRM (ARM 100442)
# Status: ⚠ 本檔定位為 **A55_EL1_debug_subset**（EL1 除錯視角常用集，非產品完整 register model；範圍見檔頭註解）。55 顆中 45 顆的欄位位置已親驗對照（41 顆依 Arm 機讀架構規格 sail-arm、CCSIDR 依 DDI 0406C.d 同佈局、3 顆實作定義顆之具名位依 ARM 官方 TF-A），出處見各暫存器的 Verified；其中 CPUECTLR／CPUPWRCTLR 的完整切分與多顆產品讀值依 2026-08 三輪交叉審查轉錄自 A55 TRM（100442_0200_02_en），該等內容標「審查轉錄」**尚未親驗原文**。2026-08-29 依交叉審查修正：SCTLR_EL1[29:28]→RES1、CCSIDR 補 WT/WB/RA/WA、CSSELR.TnD→RES0、REVIDR 移除 v7 別名語意、ID 暫存器逐欄標註產品存在性（位置不變）。2026-08-30 R5/R6 輪再修正：AIDR/REVIDR/AFSR0/AFSR1 上半部依原圖標 Reserved（非 RES0）、下半部依原圖（AIDR/AFSR＝RES0、REVIDR＝IMPDEF）；AIDR/REVIDR 的 Reset 0x0 依 Table 3-49 轉錄；AFSR 明寫「暫存器介面 RW、產品內容無可寫資訊」的分層。CNTKCTL 的 EL0PTEN/EL0VTEN 為 v8.0 基線欄位（審查曾誤判為 ECV，已三方確認維持）。待親驗值清單見 SPEC_REVIEW_LOG.md
# Description: AArch64 EL1 系統暫存器常用子集（識別、控制、位址轉換、例外狀態）

<!--
  ── Offset 對應約定 ────────────────────────────────────────────────
  AArch64 系統暫存器一律 64-bit，因此每個暫存器佔 8 bytes，Offset 以 8 遞增。
  Offset ＝ 值在 bin dump 中的位元組位移（little-endian），請讓 dump 腳本的
  輸出順序與下面一致。

  ── 對照狀態（2026-08-24）──────────────────────────────────────────
  ✔ 已對照：14 顆暫存器的欄位位置，逐欄對照 rems-project/sail-arm 的
     arm-v9.4-a/src/v8_base.sail bitfield 定義（該模型由 Arm 官方
     machine-readable specification 產生），125 個具名欄位位置全數相符。
     只驗「欄位在第幾位元」，沒有驗欄位語意、Reset 值與完整性。
  ✘ 未對照：CurrentEL／DAIF／VBAR_EL1／FAR_EL1／ELR_EL1／CNTFRQ_EL0
     （模型無對應 bitfield）；以及全部的 Reset 值 —— MIDR_EL1 的
     0x412FD050 是照「r2p0 ＋ Cortex-A55 部件編號 0xD05」推出來的，
     必須用 Cortex-A55 TRM 確認過才算數。
  ⚠ 版本落差：對照用的模型是 Armv9.4-A，本核心是 Armv8.2-A。既有欄位的
     位元位置在版本之間不會移動（新功能佔用原本的 RES0），所以位置相符
     可信；但「這顆核心到底有沒有這個欄位」只有 A55 TRM 說了算。

  ── 與官方文件的剩餘落差（2026-08-28 完整化改版後）────────────────
  本檔已收錄 55 顆：識別（MIDR／MPIDR／REVIDR／AIDR＋AArch64 ID 全套 8 顆
  ＋CCSIDR／CLIDR／CSSELR）、控制與位址轉換（SCTLR／CPACR／TCR／TTBR0/1／
  MAIR）、例外狀態（ESR／FAR／ELR／SPSR／VBAR／AFSR0/1）、context/thread
  （CONTEXTIDR／TPIDR_EL1／TPIDR_EL0／TPIDRRO_EL0）、Generic Timer 9 顆、
  PMU 7 顆、實作定義 3 顆（CPUECTLR／CPUACTLR／CPUPWRCTLR）。
  仍未收錄（需要時照格式補）：
   * EL2／EL3 全部暫存器（SCTLR_EL2/EL3、HCR_EL2、SCR_EL3、VTTBR_EL2…）
     — 本檔以 EL1 除錯視角為範圍
   * PMU 的 PMEVCNTR0-5／PMEVTYPER0-5（個別計數器直接視圖；本檔收
     PMSELR＋PMXEV* 間接視圖即可讀全部）、PMCEID0/1、PMSWINC（WO）、
     PMINTENSET/CLR（中斷路徑）、PMMIR
   * AArch32 視圖的 ID 暫存器（ID_PFR0 等 AArch64 鏡像）、MVFR0-2
   * ID_AA64AFR0/1_EL1（實作定義特徵）、ID_AA64ZFR0（SVE，A55 無）
   * RAS 群（ERR*）、AMU（A55 無）、SPE（A55 無）、GIC 系統暫存器
     （ICC_*，依 GIC 組態）
   * DSU 叢集暫存器（CLUSTERCFR_EL1 等；TF-A 的 dsu_def.h 可為編碼憑據）
   * CPUCFR_EL1、L2CTLR_EL1 等其餘實作定義暫存器（需 A55 TRM）

  ── 與官方文件的落差（2026-08-24 首輪稽核備註）─────────────────────
  本檔收錄的 20 顆是「除錯最常看的 EL1 系統暫存器」，**遠不是完整清單**：
  AArch64 架構定義的系統暫存器有數百顆（DDI 0487 附錄），Cortex-A55 TRM
  另有一整組 IMPLEMENTATION DEFINED 暫存器。需要哪顆就照格式補哪顆。
  常見但本檔尚未收錄：SCTLR_EL2/EL3、HCR_EL2、SCR_EL3、TTBR0_EL2、
  VTTBR_EL2、AMAIR_EL1、CONTEXTIDR_EL1、TPIDR_EL0/EL1、
  ID_AA64ISAR0/1_EL1、ID_AA64MMFR1/2_EL1、ID_AA64DFR0_EL1、
  CCSIDR_EL1、CSSELR_EL1、PMCR_EL0 等效能監控群組、
  CNTP_CTL_EL0／CNTV_CTL_EL0 等計時器群組。

  ── 尚未收錄（IMPLEMENTATION DEFINED，需查 Cortex-A55 TRM 逐欄補上）────
  * CPUECTLR_EL1   S3_0_C15_C1_4   核心擴充控制（預取、匯流排行為）
  * CPUACTLR_EL1   S3_0_C15_C1_0   核心輔助控制（各種 errata 開關）
  * CPUPWRCTLR_EL1 S3_0_C15_C2_7   核心電源控制
  * L2CTLR_EL1     S3_1_C11_C0_2   L2／叢集控制
  * CPUCFR_EL1     S3_0_C15_C0_0   核心組態（ECC 等）
  * ERR<n>* RAS 記錄群組
  另可依需求補：SCTLR_EL2／EL3、HCR_EL2、SCR_EL3、AMAIR、CONTEXTIDR_EL1、
  ID_AA64ISAR0/1_EL1、ID_AA64MMFR1/2_EL1、PMCR_EL0 等。
-->

## MIDR_EL1
- Offset: 0x000
- Reset: 0x412FD050
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield MIDR_EL1_Type — 5 個欄位位置逐欄相符
- Description: Main ID Register — CPU 識別碼（Reset 值 0x412FD050 是由 r2p0 與 Cortex-A55 的部件編號 0xD05 推得，尚未用 A55 TRM 確認）

| Bits  | Field        | Access | Reset | Description |
|-------|--------------|--------|-------|-------------|
| 63:32 | RES0         | RO     | 0     | 保留 |
| 31:24 | Implementer  | RO     | 0x41  | 實作者代碼 |
| 23:20 | Variant      | RO     | 0x2   | 主要版本（rXpY 的 X） |
| 19:16 | Architecture | RO     | 0xF   | 架構代碼（固定值，實際架構查 ID_AA64* 系列） |
| 15:4  | PartNum      | RO     | 0xD05 | 部件編號 |
| 3:0   | Revision     | RO     | 0x0   | 次要版本（rXpY 的 Y） |

### Enum: Implementer
- 0x41: ARM Limited

### Enum: PartNum
- 0xD03: Cortex-A53
- 0xD05: Cortex-A55
- 0xD07: Cortex-A57
- 0xD08: Cortex-A72

## MPIDR_EL1
- Offset: 0x008
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield MPIDR_EL1_Type — 6 個欄位位置逐欄相符
- Description: Multiprocessor Affinity Register — 本核心在叢集中的位置

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:40 | RES0  | RO     | 0     | 保留 |
| 39:32 | Aff3  | RO     | -     | 親和性層級 3 |
| 31    | RES1  | RO     | 1     | 保留，讀為 1 |
| 30    | U     | RO     | -     | 單處理器旗標 |
| 29:25 | RES0  | RO     | 0     | 保留 |
| 24    | MT    | RO     | -     | 多執行緒實作旗標 |
| 23:16 | Aff2  | RO     | -     | 親和性層級 2（通常為叢集編號） |
| 15:8  | Aff1  | RO     | -     | 親和性層級 1 |
| 7:0   | Aff0  | RO     | -     | 親和性層級 0（核心編號） |

### Enum: U
- 0: 多處理器系統中的一員
- 1: 單處理器

## CurrentEL
- Offset: 0x010
- Reset: -
- Description: Current Exception Level — 目前的例外等級（除錯時第一個要確認的狀態）

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| 63:4 | RES0  | RO     | 0     | 保留 |
| 3:2  | EL    | RO     | -     | 目前例外等級 |
| 1:0  | RES0  | RO     | 0     | 保留 |

### Enum: EL
- 0b00: EL0（應用程式）
- 0b01: EL1（作業系統核心）
- 0b10: EL2（Hypervisor）
- 0b11: EL3（Secure Monitor）

## DAIF
- Offset: 0x018
- Reset: -
- Description: Interrupt Mask Bits — 中斷遮罩狀態（查「中斷為什麼沒進來」先看這裡）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:10 | RES0  | RO     | 0     | 保留 |
| 9     | D     | RW     | 1     | 除錯例外遮罩 |
| 8     | A     | RW     | 1     | SError（非同步中止）遮罩 |
| 7     | I     | RW     | 1     | IRQ 遮罩 |
| 6     | F     | RW     | 1     | FIQ 遮罩 |
| 5:0   | RES0  | RO     | 0     | 保留 |

### Enum: D
- 0: 除錯例外未遮罩
- 1: 除錯例外已遮罩

### Enum: A
- 0: SError 未遮罩
- 1: SError 已遮罩

### Enum: I
- 0: IRQ 開啟
- 1: IRQ 已遮罩（關閉）

### Enum: F
- 0: FIQ 開啟
- 1: FIQ 已遮罩（關閉）

## SCTLR_EL1
- Offset: 0x020
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield SCTLR_EL1_Type — 22 個欄位位置逐欄相符
- Description: System Control Register (EL1) — MMU／快取／對齊等主控制。標 RES0 者為 ARMv8.3 之後才定義、本核心未實作；bit 20 與 22 在 ARMv8.5 分別成為 TSCXT／EIS

| Bits  | Field    | Access | Reset | Description |
|-------|----------|--------|-------|-------------|
| 63:32 | RES0     | RO     | 0     | 保留 |
| 31    | RES0     | RO     | 0     | ARMv8.3 EnIA（指標驗證），本核心未實作 |
| 30    | RES0     | RO     | 0     | ARMv8.3 EnIB（指標驗證），本核心未實作 |
| 29:28 | RES1    | RO     | 0b11  | 恆為 1（本核心無 FEAT_LSMAOC，架構規定 RES1；Linux kernel SCTLR_EL1_RES1 遮罩含 bit29/28、審查確認 A55 TRM Figure 3-162 同。2026-08 審查修正：舊版誤列為 LSMAOE/nTLSMD RW） |
| 27    | RES0     | RO     | 0     | ARMv8.3 EnDA，本核心未實作 |
| 26    | UCI      | RW     | 0     | EL0 是否可執行快取維護指令 |
| 25    | EE       | RW     | 0     | EL1 資料存取 endianness |
| 24    | E0E      | RW     | 0     | EL0 資料存取 endianness |
| 23    | SPAN     | RW     | -     | 例外進入時是否設定 PSTATE.PAN |
| 22    | RES1     | RO     | 1     | 保留，讀為 1 |
| 21    | IESB     | RW     | 0     | 例外進出時插入隱含錯誤同步屏障（RAS） |
| 20    | RES1     | RO     | 1     | 保留，讀為 1 |
| 19    | WXN      | RW     | 0     | 可寫的頁一律不可執行 |
| 18    | nTWE     | RW     | 0     | EL0 執行 WFE 是否攔截到 EL1 |
| 17    | RES0     | RO     | 0     | 保留 |
| 16    | nTWI     | RW     | 0     | EL0 執行 WFI 是否攔截到 EL1 |
| 15    | UCT      | RW     | 0     | EL0 是否可讀取 CTR_EL0 |
| 14    | DZE      | RW     | 0     | EL0 是否可執行 DC ZVA |
| 13    | RES0     | RO     | 0     | ARMv8.3 EnDB，本核心未實作 |
| 12    | I        | RW     | 0     | 指令快取致能 |
| 11    | RES1     | RO     | 1     | 保留，讀為 1 |
| 10    | RES0     | RO     | 0     | ARMv8.5 EnRCTX，本核心未實作 |
| 9     | UMA      | RW     | 0     | EL0 是否可存取中斷遮罩（DAIF） |
| 8     | SED      | RW     | -     | AArch32 SETEND 指令是否停用 |
| 7     | ITD      | RW     | -     | AArch32 IT 區塊限制 |
| 6     | RES0     | RO     | 0     | ARMv8.4 nAA，本核心未實作 |
| 5     | CP15BEN  | RW     | -     | AArch32 CP15 屏障指令致能 |
| 4     | SA0      | RW     | 0     | EL0 堆疊指標對齊檢查 |
| 3     | SA       | RW     | 0     | EL1 堆疊指標對齊檢查 |
| 2     | C        | RW     | 0     | 資料與統一快取致能 |
| 1     | A        | RW     | 0     | 對齊檢查致能 |
| 0     | M        | RW     | 0     | MMU 致能 |

### Enum: EE
- 0: EL1 資料為 little-endian
- 1: EL1 資料為 big-endian

### Enum: E0E
- 0: EL0 資料為 little-endian
- 1: EL0 資料為 big-endian

### Enum: SPAN
- 0: 例外進入 EL1 時將 PSTATE.PAN 設為 1
- 1: 例外進入時不改變 PSTATE.PAN（相容舊行為）

### Enum: WXN
- 0: 可寫與可執行互不影響
- 1: 任何可寫的區域一律不可執行

### Enum: nTWE
- 0: EL0 的 WFE 會攔截到 EL1
- 1: EL0 的 WFE 不攔截

### Enum: nTWI
- 0: EL0 的 WFI 會攔截到 EL1
- 1: EL0 的 WFI 不攔截

### Enum: I
- 0: 指令快取關閉
- 1: 指令快取開啟

### Enum: C
- 0: 資料快取關閉
- 1: 資料快取開啟

### Enum: A
- 0: 不做對齊檢查
- 1: 未對齊存取產生 Alignment fault

### Enum: M
- 0: MMU 關閉（所有存取視為 Device-nGnRnE）
- 1: MMU 開啟

## CPACR_EL1
- Offset: 0x028
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield CPACR_EL1_Type — TTA／FPEN 位置相符
- Description: Architectural Feature Access Control Register — 浮點／SIMD 與追蹤存取權限

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:29 | RES0  | RO     | 0     | 保留 |
| 28    | TTA   | RW     | 0     | 攔截系統暫存器追蹤存取 |
| 27:22 | RES0  | RO     | 0     | 保留 |
| 21:20 | FPEN  | RW     | 0b00  | 浮點／Advanced SIMD 存取權限 |
| 19:0  | RES0  | RO     | 0     | 保留（ZEN 為 SVE 用，本核心未實作 SVE） |

### Enum: FPEN
- 0b00: EL0 與 EL1 存取皆攔截到 EL1
- 0b01: 僅 EL0 存取被攔截
- 0b10: EL0 與 EL1 存取皆攔截到 EL1
- 0b11: 不攔截（正常可用）

## TCR_EL1
- Offset: 0x030
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield TCR_EL1_Type — 21 個欄位位置逐欄相符；HWU0/HWU1 官方逐位元命名為 HWU059–HWU062／HWU159–HWU162，本檔以 4-bit 群組呈現（位元範圍相同）
- Description: Translation Control Register (EL1) — 位址轉換組態。注意 TG0 與 TG1 的頁面大小編碼不同，是常見的設定錯誤來源

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:55 | RES0  | RO     | 0     | 保留 |
| 54:51 | RES0  | RO     | 0     | SVE NFD／ARMv8.3 TBID，本核心未實作 |
| 50:47 | HWU1  | RW     | 0     | TTBR1 頁表描述子位元 62:59 由硬體使用的致能 |
| 46:43 | HWU0  | RW     | 0     | TTBR0 頁表描述子位元 62:59 由硬體使用的致能 |
| 42    | HPD1  | RW     | 0     | TTBR1 階層權限停用 |
| 41    | HPD0  | RW     | 0     | TTBR0 階層權限停用 |
| 40    | HD    | RW     | 0     | 硬體管理 dirty 狀態 |
| 39    | HA    | RW     | 0     | 硬體管理 access flag |
| 38    | TBI1  | RW     | 0     | TTBR1 位址最高位元組忽略 |
| 37    | TBI0  | RW     | 0     | TTBR0 位址最高位元組忽略 |
| 36    | AS    | RW     | 0     | ASID 大小 |
| 35    | RES0  | RO     | 0     | 保留 |
| 34:32 | IPS   | RW     | -     | 中介實體位址大小 |
| 31:30 | TG1   | RW     | -     | TTBR1 頁面大小 |
| 29:28 | SH1   | RW     | -     | TTBR1 頁表走訪的可共享性 |
| 27:26 | ORGN1 | RW     | -     | TTBR1 頁表走訪的外層快取性 |
| 25:24 | IRGN1 | RW     | -     | TTBR1 頁表走訪的內層快取性 |
| 23    | EPD1  | RW     | 0     | 停用 TTBR1 的頁表走訪 |
| 22    | A1    | RW     | 0     | ASID 由哪個 TTBR 定義 |
| 21:16 | T1SZ  | RW     | -     | TTBR1 位址空間大小（64 - T1SZ 位元） |
| 15:14 | TG0   | RW     | -     | TTBR0 頁面大小 |
| 13:12 | SH0   | RW     | -     | TTBR0 頁表走訪的可共享性 |
| 11:10 | ORGN0 | RW     | -     | TTBR0 頁表走訪的外層快取性 |
| 9:8   | IRGN0 | RW     | -     | TTBR0 頁表走訪的內層快取性 |
| 7     | EPD0  | RW     | 0     | 停用 TTBR0 的頁表走訪 |
| 6     | RES0  | RO     | 0     | 保留 |
| 5:0   | T0SZ  | RW     | -     | TTBR0 位址空間大小（64 - T0SZ 位元） |

### Enum: HD
- 0: 硬體不更新 dirty 狀態
- 1: 硬體自動更新 dirty 狀態

### Enum: HA
- 0: 硬體不更新 access flag
- 1: 硬體自動更新 access flag

### Enum: AS
- 0: ASID 為 8 位元
- 1: ASID 為 16 位元

### Enum: A1
- 0: ASID 由 TTBR0_EL1 定義
- 1: ASID 由 TTBR1_EL1 定義

### Enum: EPD1
- 0: TTBR1 正常走訪頁表
- 1: 停用 TTBR1 走訪（命中即產生 translation fault）

### Enum: EPD0
- 0: TTBR0 正常走訪頁表
- 1: 停用 TTBR0 走訪（命中即產生 translation fault）

### Enum: IPS
- 0b000: 32 位元（4 GB）
- 0b001: 36 位元（64 GB）
- 0b010: 40 位元（1 TB）
- 0b011: 42 位元（4 TB）
- 0b100: 44 位元（16 TB）
- 0b101: 48 位元（256 TB）
- 0b110: 52 位元（4 PB）

### Enum: TG1
- 0b01: 16 KB 頁
- 0b10: 4 KB 頁
- 0b11: 64 KB 頁

### Enum: TG0
- 0b00: 4 KB 頁
- 0b01: 64 KB 頁
- 0b10: 16 KB 頁

### Enum: SH1
- 0b00: 不可共享
- 0b10: 外層可共享
- 0b11: 內層可共享

### Enum: SH0
- 0b00: 不可共享
- 0b10: 外層可共享
- 0b11: 內層可共享

### Enum: ORGN1
- 0b00: 不可快取
- 0b01: Write-Back Write-Allocate
- 0b10: Write-Through
- 0b11: Write-Back no Write-Allocate

### Enum: IRGN1
- 0b00: 不可快取
- 0b01: Write-Back Write-Allocate
- 0b10: Write-Through
- 0b11: Write-Back no Write-Allocate

### Enum: ORGN0
- 0b00: 不可快取
- 0b01: Write-Back Write-Allocate
- 0b10: Write-Through
- 0b11: Write-Back no Write-Allocate

### Enum: IRGN0
- 0b00: 不可快取
- 0b01: Write-Back Write-Allocate
- 0b10: Write-Through
- 0b11: Write-Back no Write-Allocate

## TTBR0_EL1
- Offset: 0x038
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield TTBR0_Type（BADDR 47..1、CnP 0..0）＋ TTBR0_EL1_Type（ASID 63..48）
- Description: Translation Table Base Register 0 — 低位址空間（使用者空間）的頁表基底

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:48 | ASID  | RW     | -     | 位址空間識別碼（TCR_EL1.A1=0 時由此定義） |
| 47:1  | BADDR | RW     | -     | 轉換表基底位址 |
| 0     | CnP   | RW     | 0     | 共用同一組轉換表（Common not Private） |

### Enum: CnP
- 0: 本核心的轉換表為私有
- 1: 與其他核心共用同一組轉換表

## TTBR1_EL1
- Offset: 0x040
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield TTBR1_Type（BADDR 47..1、CnP 0..0）＋ TTBR1_EL1_Type（ASID 63..48）
- Description: Translation Table Base Register 1 — 高位址空間（核心空間）的頁表基底

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:48 | ASID  | RW     | -     | 位址空間識別碼（TCR_EL1.A1=1 時由此定義） |
| 47:1  | BADDR | RW     | -     | 轉換表基底位址 |
| 0     | CnP   | RW     | 0     | 共用同一組轉換表 |

### Enum: CnP
- 0: 本核心的轉換表為私有
- 1: 與其他核心共用同一組轉換表

## MAIR_EL1
- Offset: 0x048
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield MAIR_EL1_Type — Attr0–Attr7 八個位元組位置逐欄相符
- Description: Memory Attribute Indirection Register — 8 組記憶體屬性，頁表描述子的 AttrIndx 指向其中一組

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:56 | Attr7 | RW     | -     | 屬性 7 |
| 55:48 | Attr6 | RW     | -     | 屬性 6 |
| 47:40 | Attr5 | RW     | -     | 屬性 5 |
| 39:32 | Attr4 | RW     | -     | 屬性 4 |
| 31:24 | Attr3 | RW     | -     | 屬性 3 |
| 23:16 | Attr2 | RW     | -     | 屬性 2 |
| 15:8  | Attr1 | RW     | -     | 屬性 1 |
| 7:0   | Attr0 | RW     | -     | 屬性 0 |

### Enum: Attr0
- 0x00: Device-nGnRnE
- 0x04: Device-nGnRE
- 0x08: Device-nGRE
- 0x0C: Device-GRE
- 0x44: Normal，內外層 Non-cacheable
- 0xAA: Normal，內外層 Write-Through
- 0xFF: Normal，內外層 Write-Back Read/Write-Allocate

### Enum: Attr1
- 0x00: Device-nGnRnE
- 0x04: Device-nGnRE
- 0x08: Device-nGRE
- 0x0C: Device-GRE
- 0x44: Normal，內外層 Non-cacheable
- 0xAA: Normal，內外層 Write-Through
- 0xFF: Normal，內外層 Write-Back Read/Write-Allocate

## VBAR_EL1
- Offset: 0x050
- Reset: -
- Description: Vector Base Address Register (EL1) — EL1 例外向量表基底位址

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:11 | VBA   | RW     | -     | 向量表基底位址（2 KB 對齊） |
| 10:0  | RES0  | RO     | 0     | 保留 |

## ESR_EL1
- Offset: 0x058
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ESRType/ESR_EL1_Type — EC 31..26、IL 25、ISS 24..0 相符
- Description: Exception Syndrome Register (EL1) — 例外原因（當機分析第一站：先看 EC）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RES0  | RO     | 0     | 保留 |
| 31:26 | EC    | RW     | -     | 例外類別 |
| 25    | IL    | RW     | -     | 造成例外的指令長度 |
| 24:0  | ISS   | RW     | -     | 例外詳細資訊（意義依 EC 而定） |

### Enum: EC
- 0x00: 未知原因
- 0x01: 攔截的 WFI 或 WFE
- 0x03: 攔截的 AArch32 MCR／MRC（cp15）
- 0x07: 攔截的 SIMD／浮點存取
- 0x0E: 非法的執行狀態
- 0x11: AArch32 SVC
- 0x15: AArch64 SVC
- 0x16: AArch64 HVC
- 0x17: AArch64 SMC
- 0x18: 攔截的 MSR／MRS／系統指令
- 0x20: 較低例外等級的指令中止（instruction abort）
- 0x21: 同一例外等級的指令中止
- 0x22: PC 對齊錯誤
- 0x24: 較低例外等級的資料中止（data abort）
- 0x25: 同一例外等級的資料中止
- 0x26: SP 對齊錯誤
- 0x28: AArch32 浮點例外
- 0x2C: AArch64 浮點例外
- 0x2F: SError 中斷
- 0x30: 較低例外等級的斷點
- 0x31: 同一例外等級的斷點
- 0x32: 較低例外等級的單步
- 0x33: 同一例外等級的單步
- 0x34: 較低例外等級的觀察點
- 0x35: 同一例外等級的觀察點
- 0x3C: BRK 指令（AArch64）

### Enum: IL
- 0: 16 位元指令
- 1: 32 位元指令

## FAR_EL1
- Offset: 0x060
- Reset: -
- Description: Fault Address Register (EL1) — 造成資料／指令中止的虛擬位址

| Bits | Field   | Access | Reset | Description |
|------|---------|--------|-------|-------------|
| 63:0 | Address | RW     | -     | 發生 fault 的虛擬位址 |

## ELR_EL1
- Offset: 0x068
- Reset: -
- Description: Exception Link Register (EL1) — 例外返回位址（當機時的 PC）

| Bits | Field   | Access | Reset | Description |
|------|---------|--------|-------|-------------|
| 63:0 | Address | RW     | -     | 例外返回位址 |

## SPSR_EL1
- Offset: 0x070
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield SPSR_EL1_Type — 12 個欄位位置逐欄相符；M[4]／M[3:0] 官方以模式編碼另行定義，不在該 bitfield 內
- Description: Saved Program Status Register (EL1) — 進入例外前的處理器狀態

| Bits  | Field   | Access | Reset | Description |
|-------|---------|--------|-------|-------------|
| 63:32 | RES0    | RO     | 0     | 保留 |
| 31    | N       | RW     | -     | 負值條件旗標 |
| 30    | Z       | RW     | -     | 零值條件旗標 |
| 29    | C       | RW     | -     | 進位條件旗標 |
| 28    | V       | RW     | -     | 溢位條件旗標 |
| 27:26 | RES0    | RO     | 0     | 保留 |
| 25    | RES0    | RO     | 0     | ARMv8.5 TCO，本核心未實作 |
| 24    | RES0    | RO     | 0     | ARMv8.4 DIT，本核心未實作 |
| 23    | UAO     | RW     | -     | User Access Override（ARMv8.2） |
| 22    | PAN     | RW     | -     | 特權存取不可觸及使用者記憶體 |
| 21    | SS      | RW     | -     | 軟體單步 |
| 20    | IL      | RW     | -     | 非法執行狀態 |
| 19:10 | RES0    | RO     | 0     | 保留 |
| 9     | D       | RW     | -     | 除錯例外遮罩 |
| 8     | A       | RW     | -     | SError 遮罩 |
| 7     | I       | RW     | -     | IRQ 遮罩 |
| 6     | F       | RW     | -     | FIQ 遮罩 |
| 5     | RES0    | RO     | 0     | 保留 |
| 4     | M[4]    | RW     | -     | 執行狀態 |
| 3:0   | M[3:0]  | RW     | -     | 例外進入前的模式／例外等級 |

### Enum: PAN
- 0: 特權存取可觸及使用者記憶體
- 1: 特權存取觸及使用者記憶體會產生 permission fault

### Enum: M[4]
- 0: AArch64 狀態
- 1: AArch32 狀態

### Enum: M[3:0]
- 0b0000: EL0t（EL0，使用 SP_EL0）
- 0b0100: EL1t（EL1，使用 SP_EL0）
- 0b0101: EL1h（EL1，使用 SP_EL1）
- 0b1000: EL2t
- 0b1001: EL2h
- 0b1100: EL3t
- 0b1101: EL3h

## CLIDR_EL1
- Offset: 0x078
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield CLIDR_EL1_Type — 10 個欄位位置逐欄相符
- Description: Cache Level ID Register — 各階快取的種類與一致性層級

| Bits  | Field  | Access | Reset | Description |
|-------|--------|--------|-------|-------------|
| 63:30 | RES0   | RO     | 0     | 保留 |
| 29:27 | LoUU   | RO     | -     | Level of Unification Uniprocessor |
| 26:24 | LoC    | RO     | -     | Level of Coherence |
| 23:21 | LoUIS  | RO     | -     | Level of Unification Inner Shareable |
| 20:18 | Ctype7 | RO     | 0b000 | 第 7 階快取種類 |
| 17:15 | Ctype6 | RO     | 0b000 | 第 6 階快取種類 |
| 14:12 | Ctype5 | RO     | 0b000 | 第 5 階快取種類 |
| 11:9  | Ctype4 | RO     | 0b000 | 第 4 階快取種類 |
| 8:6   | Ctype3 | RO     | 0b000 | 第 3 階快取種類 |
| 5:3   | Ctype2 | RO     | -     | 第 2 階快取種類 |
| 2:0   | Ctype1 | RO     | -     | 第 1 階快取種類 |

### Enum: Ctype1
- 0b000: 無快取
- 0b001: 只有指令快取
- 0b010: 只有資料快取
- 0b011: 指令與資料快取分離
- 0b100: 統一快取

### Enum: Ctype2
- 0b000: 無快取
- 0b001: 只有指令快取
- 0b010: 只有資料快取
- 0b011: 指令與資料快取分離
- 0b100: 統一快取

## CTR_EL0
- Offset: 0x080
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield CTR_EL0_Type — 7 個欄位位置逐欄相符
- Description: Cache Type Register — 快取行大小與策略（自修改程式碼維護的依據）

| Bits  | Field    | Access | Reset | Description |
|-------|----------|--------|-------|-------------|
| 63:32 | RES0     | RO     | 0     | 保留 |
| 31    | RES1     | RO     | 1     | 保留，讀為 1 |
| 30    | RES0     | RO     | 0     | 保留 |
| 29    | DIC      | RO     | -     | 指令快取一致性（是否免做 IC 維護） |
| 28    | IDC      | RO     | -     | 資料快取一致性（是否免做 DC 清除） |
| 27:24 | CWG      | RO     | -     | Cache writeback granule（log2 words） |
| 23:20 | ERG      | RO     | -     | Exclusives reservation granule（log2 words） |
| 19:16 | DminLine | RO     | -     | 最小資料快取行（log2 words） |
| 15:14 | L1Ip     | RO     | -     | L1 指令快取索引／標籤策略 |
| 13:4  | RES0     | RO     | 0     | 保留 |
| 3:0   | IminLine | RO     | -     | 最小指令快取行（log2 words） |

### Enum: DIC
- 0: 需要 IC 維護指令
- 1: 資料到指令的一致性由硬體保證

### Enum: IDC
- 0: 需要 DC 清除到統一點
- 1: 硬體保證，免做 DC 清除

### Enum: L1Ip
- 0b10: VIPT
- 0b11: PIPT

## ID_AA64PFR0_EL1
- Offset: 0x088
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ID_AA64PFR0_EL1_Type — 15 個欄位位置逐欄相符（55:52 官方為 Armv9 的 RME，本核心標 RES0）
- Description: AArch64 Processor Feature Register 0 — 各例外等級與功能的實作狀況

| Bits  | Field    | Access | Reset | Description |
|-------|----------|--------|-------|-------------|
| 63:60 | CSV3     | RO     | -     | 推測執行側通道（快取）緩解 |
| 59:56 | CSV2     | RO     | -     | 推測執行側通道（分支）緩解 |
| 55:52 | RES0     | RO     | 0     | 保留 |
| 51:48 | DIT      | RO     | -     | 資料無關時序（ARMv8.4）。本核心（Armv8.2）讀 0（較新架構才定義） |
| 47:44 | AMU      | RO     | -     | 活動監控單元。本核心（Armv8.2）讀 0（較新架構才定義） |
| 43:40 | MPAM     | RO     | -     | 記憶體分區與監控。本核心（Armv8.2）讀 0（較新架構才定義） |
| 39:36 | SEL2     | RO     | -     | Secure EL2。本核心（Armv8.2）讀 0（較新架構才定義） |
| 35:32 | SVE      | RO     | -     | 可縮放向量擴充。本核心（Armv8.2）讀 0（較新架構才定義） |
| 31:28 | RAS      | RO     | -     | 可靠性／可用性／可服務性擴充 |
| 27:24 | GIC      | RO     | -     | GIC 系統暫存器介面 |
| 23:20 | AdvSIMD  | RO     | -     | Advanced SIMD |
| 19:16 | FP       | RO     | -     | 浮點運算 |
| 15:12 | EL3      | RO     | -     | EL3 實作狀況 |
| 11:8  | EL2      | RO     | -     | EL2 實作狀況 |
| 7:4   | EL1      | RO     | -     | EL1 實作狀況 |
| 3:0   | EL0      | RO     | -     | EL0 實作狀況 |

### Enum: EL0
- 0b0000: 未實作
- 0b0001: 僅支援 AArch64
- 0b0010: 支援 AArch64 與 AArch32

### Enum: EL1
- 0b0000: 未實作
- 0b0001: 僅支援 AArch64
- 0b0010: 支援 AArch64 與 AArch32

### Enum: EL2
- 0b0000: 未實作
- 0b0001: 僅支援 AArch64
- 0b0010: 支援 AArch64 與 AArch32

### Enum: EL3
- 0b0000: 未實作
- 0b0001: 僅支援 AArch64
- 0b0010: 支援 AArch64 與 AArch32

### Enum: FP
- 0b0000: 已實作（不含半精度）
- 0b0001: 已實作（含半精度）
- 0b1111: 未實作

### Enum: AdvSIMD
- 0b0000: 已實作（不含半精度）
- 0b0001: 已實作（含半精度）
- 0b1111: 未實作

### Enum: GIC
- 0b0000: 無系統暫存器介面
- 0b0001: 有 GICv3／GICv4 系統暫存器介面

### Enum: RAS
- 0b0000: 未實作
- 0b0001: ARMv8.2 RAS 擴充

### Enum: SVE
- 0b0000: 未實作
- 0b0001: 已實作

## ID_AA64MMFR0_EL1
- Offset: 0x090
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ID_AA64MMFR0_EL1_Type — 12 個欄位位置逐欄相符
- Description: AArch64 Memory Model Feature Register 0 — 實體位址範圍與頁面大小支援度。2026-08 第四輪審查補記：A55 TRM §3.2.60／Figure 3-127（審查轉錄）的產品圖把 [63:24] 整段併標 RES0（本核心該區讀 0）；但其中 TGran4/TGran64 是 Armv8.0 架構基線欄位、0 是「支援」的有效編碼——本表保留架構欄位切分，並在該兩欄同時記錄兩層語意

| Bits  | Field     | Access | Reset | Description |
|-------|-----------|--------|-------|-------------|
| 63:48 | RES0      | RO     | 0     | 保留 |
| 47:44 | ExS       | RO     | -     | 例外進出時的內容同步。本核心（Armv8.2）讀 0（較新架構才定義） |
| 43:40 | TGran4_2  | RO     | -     | 第 2 階轉換的 4 KB 頁支援。本核心（Armv8.2）讀 0（較新架構才定義） |
| 39:36 | TGran64_2 | RO     | -     | 第 2 階轉換的 64 KB 頁支援。本核心（Armv8.2）讀 0（較新架構才定義） |
| 35:32 | TGran16_2 | RO     | -     | 第 2 階轉換的 16 KB 頁支援。本核心（Armv8.2）讀 0（較新架構才定義） |
| 31:28 | TGran4    | RO     | -     | 4 KB 頁支援。Armv8.0 架構基線欄位，官方編碼 0＝支援 4KB（0b1111＝不支援）；A55 TRM Figure 3-127 產品圖將此固定零值併入 [63:24] RES0 標示（審查轉錄）——兩層描述皆為真 |
| 27:24 | TGran64   | RO     | -     | 64 KB 頁支援。Armv8.0 架構基線欄位，官方編碼 0＝支援 64KB（0b1111＝不支援）；A55 TRM Figure 3-127 產品圖將此固定零值併入 [63:24] RES0 標示（審查轉錄） |
| 23:20 | TGran16   | RO     | -     | 16 KB 頁支援 |
| 19:16 | BigEndEL0 | RO     | -     | EL0 混合 endian 支援 |
| 15:12 | SNSMem    | RO     | -     | 安全／非安全記憶體區分 |
| 11:8  | BigEnd    | RO     | -     | 混合 endian 支援 |
| 7:4   | ASIDBits  | RO     | -     | ASID 位元數 |
| 3:0   | PARange   | RO     | -     | 實體位址範圍 |

### Enum: PARange
- 0b0000: 32 位元（4 GB）
- 0b0001: 36 位元（64 GB）
- 0b0010: 40 位元（1 TB）
- 0b0011: 42 位元（4 TB）
- 0b0100: 44 位元（16 TB）
- 0b0101: 48 位元（256 TB）
- 0b0110: 52 位元（4 PB）

### Enum: ASIDBits
- 0b0000: 8 位元 ASID
- 0b0010: 16 位元 ASID

### Enum: TGran4
- 0b0000: 支援 4 KB 頁
- 0b1111: 不支援 4 KB 頁

### Enum: TGran64
- 0b0000: 支援 64 KB 頁
- 0b1111: 不支援 64 KB 頁

### Enum: TGran16
- 0b0000: 不支援 16 KB 頁
- 0b0001: 支援 16 KB 頁

## CNTFRQ_EL0
- Offset: 0x098
- Reset: -
- Description: Counter-timer Frequency Register — 系統計時器頻率（單位 Hz，由開機軟體寫入；為 0 表示韌體沒設定）

| Bits  | Field     | Access | Reset | Description |
|-------|-----------|--------|-------|-------------|
| 63:32 | RES0      | RO     | 0     | 保留 |
| 31:0  | Frequency | RW     | -     | 系統計時器頻率（Hz） |

## REVIDR_EL1
- Offset: 0x0A0
- Reset: 0x0000000000000000
- Description: Revision ID Register — 實作特定小改版（errata 修補）資訊，須與 MIDR_EL1 一併解讀（MRS Rt,REVIDR_EL1）。2026-08 審查修正：舊版沿用了 ARMv7 REVIDR 的「未實作時讀值=MIDR」選配別名語意——AArch64 的 REVIDR_EL1 為必備暫存器，無此行為。2026-08 第五輪修正：上半部依 A55 TRM §3.2.92／Figure 3-160 標 Reserved（非 RES0——兩者不可在無架構佐證時互換）；Reset 0x0 依 Table 3-49（Type=RO、Reset=0x00000000）審查轉錄，待親驗

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RESERVED | RO | 0 | 保留（Figure 3-160：Reserved，審查轉錄） |
| 31:0 | IMPDEF | RO | 0 | Figure 3-160 原圖標籤＝IMPLEMENTATION DEFINED（2026-08 R6 修正：欄名照原圖，不再自命名 REVIDR）；語意＝REVIDR（errata 修補資訊），r2p0 reset/讀值 0（Table 3-49 審查轉錄） |

## AIDR_EL1
- Offset: 0x0A8
- Reset: 0x0000000000000000
- Description: Auxiliary ID Register — Cortex-A55 未使用此暫存器（MRS Rt,AIDR_EL1）。2026-08 第四輪審查修正：舊版誤列整顆 [63:0] 實作定義。2026-08 第五輪修正：上半部依 A55 TRM §3.2.14／Figure 3-91 標 Reserved（原文即 Reserved，非 RES0——僅下半部原文為 RES0）；Reset 0x0 依 Table 3-49（Type=RO、Reset=0x00000000）審查轉錄，待親驗

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RESERVED | RO | 0 | 保留（Figure 3-91：Reserved，審查轉錄） |
| 31:0 | RES0 | RO | 0 | Cortex-A55 未使用，讀 0（Figure 3-91：RES0，審查轉錄） |

## ID_AA64PFR1_EL1
- Offset: 0x0B0
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ID_AA64PFR1_EL1_Type — 欄位位置逐欄相符
- Description: AArch64 Processor Feature Register 1（MRS Rt,ID_AA64PFR1_EL1）（特徵值意義見 DDI 0487；v8.3 之後才引入的欄位在本核心（v8.2）讀 0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:60 | PFAR | RO | - | 實體錯誤位址擴充。本核心（Armv8.2）讀 0（較新架構才定義） |
| 59:56 | DF2 | RO | - | 二次錯誤注入。本核心（Armv8.2）讀 0（較新架構才定義） |
| 55:52 | MTEX | RO | - | MTE 擴充。本核心（Armv8.2）讀 0（較新架構才定義） |
| 51:48 | THE | RO | - | 轉譯強化。本核心（Armv8.2）讀 0（較新架構才定義） |
| 47:44 | GCS | RO | - | Guarded Control Stack。本核心（Armv8.2）讀 0（較新架構才定義） |
| 43:40 | MTE_frac | RO | - | MTE 次版本。本核心（Armv8.2）讀 0（較新架構才定義） |
| 39:36 | NMI | RO | - | 非遮罩中斷支援。本核心（Armv8.2）讀 0（較新架構才定義） |
| 35:32 | CSV2_frac | RO | - | CSV2 次版本。本核心（Armv8.2）讀 0（較新架構才定義） |
| 31:28 | RNDR_trap | RO | - | 亂數 trap。本核心（Armv8.2）讀 0（較新架構才定義） |
| 27:24 | SME | RO | - | SME 支援。本核心（Armv8.2）讀 0（較新架構才定義） |
| 23:20 | RES0 | RO | - | 保留 |
| 19:16 | MPAM_frac | RO | - | MPAM 次版本。本核心（Armv8.2）讀 0（較新架構才定義） |
| 15:12 | RAS_frac | RO | - | RAS 次版本。本核心（Armv8.2）讀 0（較新架構才定義） |
| 11:8 | MTE | RO | - | 記憶體標籤擴充。本核心（Armv8.2）讀 0（較新架構才定義） |
| 7:4 | SSBS | RO | - | 推測性 Store Bypass Safe |
| 3:0 | BT | RO | - | 分支目標識別（BTI）。本核心（Armv8.2）讀 0（較新架構才定義） |

## ID_AA64DFR0_EL1
- Offset: 0x0B8
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ID_AA64DFR0_EL1_Type — 欄位位置逐欄相符
- Description: AArch64 Debug Feature Register 0 — 中斷點／監看點數量與 PMU 版本（MRS Rt,ID_AA64DFR0_EL1）（特徵值意義見 DDI 0487；v8.3 之後才引入的欄位在本核心（v8.2）讀 0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:60 | HPMN0 | RO | - | HPMN 可為 0。本核心（Armv8.2）讀 0（較新架構才定義） |
| 59:56 | ExtTrcBuff | RO | - | 外部 trace buffer。本核心（Armv8.2）讀 0（較新架構才定義） |
| 55:52 | BRBE | RO | - | Branch Record Buffer。本核心（Armv8.2）讀 0（較新架構才定義） |
| 51:48 | MTPMU | RO | - | 多執行緒 PMU。本核心（Armv8.2）讀 0（較新架構才定義） |
| 47:44 | TraceBuffer | RO | - | trace buffer 擴充。本核心（Armv8.2）讀 0（較新架構才定義） |
| 43:40 | TraceFilt | RO | - | trace 過濾。本核心（Armv8.2）讀 0（較新架構才定義） |
| 39:36 | DoubleLock | RO | - | OS Double Lock |
| 35:32 | PMSVer | RO | - | 統計剖析（SPE）版本 |
| 31:28 | CTX_CMPs | RO | - | context 比對中斷點數 − 1 |
| 27:24 | SEBEP | RO | - | 同步例外剖析。本核心（Armv8.2）讀 0（較新架構才定義） |
| 23:20 | WRPs | RO | - | 監看點數 − 1 |
| 19:16 | PMSS | RO | - | PMU 快照。本核心（Armv8.2）讀 0（較新架構才定義） |
| 15:12 | BRPs | RO | - | 中斷點數 − 1 |
| 11:8 | PMUVer | RO | - | PMU 架構版本 |
| 7:4 | TraceVer | RO | - | trace 支援 |
| 3:0 | DebugVer | RO | - | 除錯架構版本 |

## ID_AA64ISAR0_EL1
- Offset: 0x0C0
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ID_AA64ISAR0_EL1_Type — 欄位位置逐欄相符
- Description: AArch64 Instruction Set Attribute Register 0 — 密碼學／原子／CRC 指令支援（MRS Rt,ID_AA64ISAR0_EL1）（特徵值意義見 DDI 0487；v8.3 之後才引入的欄位在本核心（v8.2）讀 0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:60 | RNDR | RO | - | 亂數指令。本核心（Armv8.2）讀 0（較新架構才定義） |
| 59:56 | TLB | RO | - | TLBI 範圍操作。本核心（Armv8.2）讀 0（較新架構才定義） |
| 55:52 | TS | RO | - | 旗標操作指令。本核心（Armv8.2）讀 0（較新架構才定義） |
| 51:48 | FHM | RO | - | FMLAL/FMLSL。本核心（Armv8.2）讀 0（較新架構才定義） |
| 47:44 | DP | RO | - | 點積指令 |
| 43:40 | SM4 | RO | - | SM4 指令。本核心依密碼學擴充組態，讀值自證 |
| 39:36 | SM3 | RO | - | SM3 指令。本核心依密碼學擴充組態，讀值自證 |
| 35:32 | SHA3 | RO | - | SHA3 指令。本核心依密碼學擴充組態，讀值自證 |
| 31:28 | RDM | RO | - | SQRDMLAH/SQRDMLSH |
| 27:24 | TME | RO | - | 交易記憶體。本核心（Armv8.2）讀 0（較新架構才定義） |
| 23:20 | Atomic | RO | - | LSE 原子指令 |
| 19:16 | CRC32 | RO | - | CRC32 指令 |
| 15:12 | SHA2 | RO | - | SHA2 指令 |
| 11:8 | SHA1 | RO | - | SHA1 指令 |
| 7:4 | AES | RO | - | AES 指令 |
| 3:0 | RES0 | RO | - | 保留 |

## ID_AA64ISAR1_EL1
- Offset: 0x0C8
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ID_AA64ISAR1_EL1_Type — 欄位位置逐欄相符
- Description: AArch64 Instruction Set Attribute Register 1 — 指標驗證／原子記憶體語意等（MRS Rt,ID_AA64ISAR1_EL1）（特徵值意義見 DDI 0487；v8.3 之後才引入的欄位在本核心（v8.2）讀 0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:60 | LS64 | RO | - | 64-byte 載入儲存。本核心（Armv8.2）讀 0（較新架構才定義） |
| 59:56 | XS | RO | - | XS 屬性。本核心（Armv8.2）讀 0（較新架構才定義） |
| 55:52 | I8MM | RO | - | Int8 矩陣乘。本核心（Armv8.2）讀 0（較新架構才定義） |
| 51:48 | DGH | RO | - | Data Gathering Hint。本核心（Armv8.2）讀 0（較新架構才定義） |
| 47:44 | BF16 | RO | - | BFloat16。本核心（Armv8.2）讀 0（較新架構才定義） |
| 43:40 | SPECRES | RO | - | 預測失效指令。本核心（Armv8.2）讀 0（較新架構才定義） |
| 39:36 | SB | RO | - | Speculation Barrier。本核心（Armv8.2）讀 0（較新架構才定義） |
| 35:32 | FRINTTS | RO | - | FRINT32/64。本核心（Armv8.2）讀 0（較新架構才定義） |
| 31:28 | GPI | RO | - | 實作定義 generic PAC。本核心（Armv8.2）讀 0（較新架構才定義） |
| 27:24 | GPA | RO | - | QARMA generic PAC。本核心（Armv8.2）讀 0（較新架構才定義） |
| 23:20 | LRCPC | RO | - | LDAPR 系列 |
| 19:16 | FCMA | RO | - | 複數運算。本核心（Armv8.2）讀 0（較新架構才定義） |
| 15:12 | JSCVT | RO | - | JavaScript 轉換。本核心（Armv8.2）讀 0（較新架構才定義） |
| 11:8 | API | RO | - | 實作定義位址 PAC。本核心（Armv8.2）讀 0（較新架構才定義） |
| 7:4 | APA | RO | - | QARMA 位址 PAC。本核心（Armv8.2）讀 0（較新架構才定義） |
| 3:0 | DPB | RO | - | DC CVAP（持久性清理） |

## ID_AA64MMFR1_EL1
- Offset: 0x0D0
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ID_AA64MMFR1_EL1_Type — 欄位位置逐欄相符
- Description: AArch64 Memory Model Feature Register 1 — PAN／VHE／HPDS 等（MRS Rt,ID_AA64MMFR1_EL1）（特徵值意義見 DDI 0487；v8.3 之後才引入的欄位在本核心（v8.2）讀 0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:60 | ECBHB | RO | - | 分支歷史清除行為。本核心（Armv8.2）讀 0（較新架構才定義） |
| 59:56 | CMOW | RO | - | cache 維護權限檢查。本核心（Armv8.2）讀 0（較新架構才定義） |
| 55:52 | TIDCP1 | RO | - | 實作定義暫存器 trap。本核心（Armv8.2）讀 0（較新架構才定義） |
| 51:48 | nTLBPA | RO | - | TLB 中介位址快取資訊。本核心（Armv8.2）讀 0（較新架構才定義） |
| 47:44 | AFP | RO | - | 替代浮點行為。本核心（Armv8.2）讀 0（較新架構才定義） |
| 43:40 | HCX | RO | - | HCRX_EL2 支援。本核心（Armv8.2）讀 0（較新架構才定義） |
| 39:36 | ETS | RO | - | 增強轉譯同步。本核心（Armv8.2）讀 0（較新架構才定義） |
| 35:32 | TWED | RO | - | WFE trap 延遲。本核心（Armv8.2）讀 0（較新架構才定義） |
| 31:28 | XNX | RO | - | EL0/EL1 XN 區分 |
| 27:24 | SpecSEI | RO | - | 推測性 SError。本核心（Armv8.2）讀 0（較新架構才定義） |
| 23:20 | PAN | RO | - | 特權存取禁止（PAN） |
| 19:16 | LO | RO | - | LORegions |
| 15:12 | HPDS | RO | - | 階層式權限停用 |
| 11:8 | VH | RO | - | 虛擬化主機擴充（VHE） |
| 7:4 | VMIDBits | RO | - | VMID 位元數 |
| 3:0 | HAFDBS | RO | - | 硬體 Access/Dirty 旗標 |

## ID_AA64MMFR2_EL1
- Offset: 0x0D8
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield ID_AA64MMFR2_EL1_Type — 欄位位置逐欄相符
- Description: AArch64 Memory Model Feature Register 2 — CnP／UAO／IESB 等（MRS Rt,ID_AA64MMFR2_EL1）（特徵值意義見 DDI 0487；v8.3 之後才引入的欄位在本核心（v8.2）讀 0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:60 | E0PD | RO | - | EL0 轉譯早期停用。本核心（Armv8.2）讀 0（較新架構才定義） |
| 59:56 | EVT | RO | - | 增強虛擬化 trap。本核心（Armv8.2）讀 0（較新架構才定義） |
| 55:52 | BBM | RO | - | break-before-make 等級。本核心（Armv8.2）讀 0（較新架構才定義） |
| 51:48 | TTL | RO | - | TTL 提示。本核心（Armv8.2）讀 0（較新架構才定義） |
| 47:44 | RES0 | RO | - | 保留 |
| 43:40 | FWB | RO | - | stage2 強制 write-back。本核心（Armv8.2）讀 0（較新架構才定義） |
| 39:36 | IDS | RO | - | ID 空間 trap 回報。本核心（Armv8.2）讀 0（較新架構才定義） |
| 35:32 | AT | RO | - | 非對齊單拷貝原子性。本核心（Armv8.2）讀 0（較新架構才定義） |
| 31:28 | ST | RO | - | 小型轉譯表。本核心（Armv8.2）讀 0（較新架構才定義） |
| 27:24 | NV | RO | - | 巢狀虛擬化。本核心（Armv8.2）讀 0（較新架構才定義） |
| 23:20 | CCIDX | RO | - | CCSIDR 大索引格式（本核心讀 0：CCSIDR_EL1 用 32-bit 佈局） |
| 19:16 | VARange | RO | - | 虛擬位址範圍 |
| 15:12 | IESB | RO | - | 隱含 error barrier |
| 11:8 | LSM | RO | - | LSMAOE/nTLSMD 支援 |
| 7:4 | UAO | RO | - | 使用者存取覆寫 |
| 3:0 | CnP | RO | - | Common not Private |

## CCSIDR_EL1
- Offset: 0x0E0
- Reset: -
- Verified: ARM DDI 0406C.d §B6.1「CCSIDR, Cache Size ID Registers」（v7/v8 無 CCIDX 之同佈局，含 WT/WB/RA/WA[31:28]，親驗）＋交叉審查確認 A55 TRM §3.2.23（Figure 3-99）同佈局（原文待親驗）
- Description: Cache Size ID Register — 由 CSSELR_EL1 選定之快取的參數。本核心 ID_AA64MMFR2.CCIDX=0，用 32-bit 佈局（2026-08 審查修正：補上舊版遺漏的 WT/WB/RA/WA 四個能力位；MRS Rt,CCSIDR_EL1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RES0 | RO | - | 保留 |
| 31 | WT | RO | - | 支援 write-through |
| 30 | WB | RO | - | 支援 write-back |
| 29 | RA | RO | - | 支援 read-allocation |
| 28 | WA | RO | - | 支援 write-allocation |
| 27:13 | NumSets | RO | - | set 數 − 1 |
| 12:3 | Associativity | RO | - | 關聯度 − 1 |
| 2:0 | LineSize | RO | - | log2(每 line words) − 2（0 = 4 words = 16 bytes） |

## CSSELR_EL1
- Offset: 0x0E8
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield CSSELR_EL1_Type — 欄位位置逐欄相符
- Description: Cache Size Selection Register — 選擇 CCSIDR_EL1 顯示哪個快取（MRS/MSR Rt,CSSELR_EL1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:5 | RES0 | RO | - | 保留 |
| 4 | RES0 | RO | 0 | 保留（TnD 需 FEAT_MTE；A55 無 MTE，恆為 0。2026-08 審查修正：舊版誤列為可寫欄位） |
| 3:1 | Level | RW | - | 快取層級（0b000 = L1） |
| 0 | InD | RW | - | 指令／資料選擇 |

### Enum: InD
- 0: 資料或 unified cache
- 1: 指令 cache

## AFSR0_EL1
- Offset: 0x0F0
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register AFSR0_EL1（無切分的整顆暫存器）
- Description: Auxiliary Fault Status Register 0 — 實作定義的故障補充資訊。Cortex-A55 未使用此暫存器（2026-08 審查修正：舊版表格誤列整顆 IMPDEF RW 內容，與說明矛盾）。存取分層（2026-08 第五輪釐清）：**暫存器指令介面為 RW**（MRS/MSR 皆可，Table 3-54 Type=RW 審查轉錄）——RW 的是介面，不是內容；產品內容無可用可寫資訊：[63:32] Reserved、[31:0] RES0（§3.2.8／Figure 3-85 轉錄）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RESERVED | RO | - | 保留（Figure 3-85：Reserved，審查轉錄；非 RES0——2026-08 R6 修正：Reserved 無讀值/reset 保證，reset 回 `-`） |
| 31:0 | RES0 | RO | 0 | A55：RES0（Figure 3-85 審查轉錄；RES0 讀 0 有架構依據） |

## AFSR1_EL1
- Offset: 0x0F8
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register AFSR1_EL1（無切分的整顆暫存器）
- Description: Auxiliary Fault Status Register 1 — 實作定義的故障補充資訊。Cortex-A55 未使用此暫存器（2026-08 審查修正：舊版表格誤列整顆 IMPDEF RW 內容，與說明矛盾）。存取分層（2026-08 第五輪釐清）：**暫存器指令介面為 RW**（MRS/MSR 皆可，Table 3-54 Type=RW 審查轉錄）——RW 的是介面，不是內容；產品內容無可用可寫資訊：[63:32] Reserved、[31:0] RES0（§3.2.11／Figure 3-88 轉錄）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RESERVED | RO | - | 保留（Figure 3-88：Reserved，審查轉錄；非 RES0——2026-08 R6 修正：Reserved 無讀值/reset 保證，reset 回 `-`） |
| 31:0 | RES0 | RO | 0 | A55：RES0（Figure 3-88 審查轉錄；RES0 讀 0 有架構依據） |

## CONTEXTIDR_EL1
- Offset: 0x100
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield CONTEXTIDR_EL1_Type — 欄位位置逐欄相符
- Description: Context ID Register — 目前程序識別碼，供 debug／trace（MRS/MSR Rt,CONTEXTIDR_EL1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RES0 | RO | - | 保留 |
| 31:0 | PROCID | RW | - | 程序識別值 |

## TPIDR_EL1
- Offset: 0x108
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register TPIDR_EL1（無切分的整顆暫存器）
- Description: EL1 軟體執行緒 ID（僅特權可見） — 硬體永不更新（MRS Rt,TPIDR_EL1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:0 | TID | RW | - | 軟體定義 |

## TPIDR_EL0
- Offset: 0x110
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register TPIDR_EL0（無切分的整顆暫存器）
- Description: EL0 讀寫執行緒 ID（典型為 TLS 指標） — 硬體永不更新（MRS Rt,TPIDR_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:0 | TID | RW | - | 軟體定義 |

## TPIDRRO_EL0
- Offset: 0x118
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register TPIDRRO_EL0（無切分的整顆暫存器）
- Description: EL0 唯讀執行緒 ID（EL1 可寫） — 硬體永不更新（MRS Rt,TPIDRRO_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:0 | TID | RW | - | 軟體定義 |

## CNTKCTL_EL1
- Offset: 0x120
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield CNTKCTL_EL1_Type — 欄位位置逐欄相符
- Description: Counter-timer Kernel Control — EL0 對計時器／計數器的存取控制（MRS/MSR Rt,CNTKCTL_EL1）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:18 | RES0 | RO | - | 保留 |
| 17 | EVNTIS | RW | - | 事件流位元選擇放大（v8.6；本核心讀 0） |
| 16:10 | RES0 | RO | - | 保留 |
| 9 | EL0PTEN | RW | - | EL0 可存取實體計時器（CNTP_*）。v8.0 基線欄位（ARMv7 CNTKCTL.PL0PTEN 之對應；非 FEAT_ECV——三輪審查已確認） |
| 8 | EL0VTEN | RW | - | EL0 可存取虛擬計時器（CNTV_*）。v8.0 基線欄位（ARMv7 CNTKCTL.PL0VTEN 之對應） |
| 7:4 | EVNTI | RW | - | 事件流觸發位元選擇 |
| 3 | EVNTDIR | RW | - | 事件流觸發邊緣 |
| 2 | EVNTEN | RW | - | 事件流致能 |
| 1 | EL0VCTEN | RW | - | EL0 可讀 CNTVCT／CNTFRQ |
| 0 | EL0PCTEN | RW | - | EL0 可讀 CNTPCT／CNTFRQ |

## CNTPCT_EL0
- Offset: 0x128
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register CNTPCT_EL0（無切分的整顆暫存器）
- Description: Physical Count — 實體計數器目前值（頻率見 CNTFRQ_EL0；MRS Rt,CNTPCT_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:0 | COUNT | RO | - | 實體計數值 |

## CNTVCT_EL0
- Offset: 0x130
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register CNTVCT_EL0（無切分的整顆暫存器）
- Description: Virtual Count — 虛擬計數器目前值（= CNTPCT − CNTVOFF；MRS Rt,CNTVCT_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:0 | COUNT | RO | - | 虛擬計數值 |

## CNTP_CTL_EL0
- Offset: 0x138
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield CNTP_CTL_EL0_Type — 欄位位置逐欄相符
- Description: EL1 Physical Timer Control（MRS/MSR Rt,CNTP_CTL_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:3 | RES0 | RO | - | 保留 |
| 2 | ISTATUS | RO | - | 計時器條件已成立（中斷狀態，不受 IMASK 影響） |
| 1 | IMASK | RW | - | 中斷遮罩 |
| 0 | ENABLE | RW | - | 計時器致能 |

### Enum: ENABLE
- 0: 計時器停用
- 1: 計時器啟用

### Enum: IMASK
- 0: 中斷未遮罩
- 1: 中斷已遮罩

## CNTP_CVAL_EL0
- Offset: 0x140
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register CNTP_CVAL_EL0（無切分的整顆暫存器）
- Description: EL1 Physical Timer CompareValue — CNTPCT ≥ CVAL 時觸發（MRS/MSR Rt,CNTP_CVAL_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:0 | CVAL | RW | - | 比較值 |

## CNTP_TVAL_EL0
- Offset: 0x148
- Reset: -
- Description: EL1 Physical Timer TimerValue — 倒數視圖（讀值 = CVAL − CNTPCT 的低 32 位；MRS/MSR Rt,CNTP_TVAL_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RES0 | RO | - | 保留 |
| 31:0 | TVAL | RW | - | 倒數值（有號） |

## CNTV_CTL_EL0
- Offset: 0x150
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield CNTV_CTL_EL0_Type — 欄位位置逐欄相符
- Description: Virtual Timer Control（MRS/MSR Rt,CNTV_CTL_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:3 | RES0 | RO | - | 保留 |
| 2 | ISTATUS | RO | - | 計時器條件已成立（中斷狀態，不受 IMASK 影響） |
| 1 | IMASK | RW | - | 中斷遮罩 |
| 0 | ENABLE | RW | - | 計時器致能 |

### Enum: ENABLE
- 0: 計時器停用
- 1: 計時器啟用

### Enum: IMASK
- 0: 中斷未遮罩
- 1: 中斷已遮罩

## CNTV_CVAL_EL0
- Offset: 0x158
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register CNTV_CVAL_EL0（無切分的整顆暫存器）
- Description: Virtual Timer CompareValue（MRS/MSR Rt,CNTV_CVAL_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:0 | CVAL | RW | - | 比較值 |

## CNTV_TVAL_EL0
- Offset: 0x160
- Reset: -
- Description: Virtual Timer TimerValue — 倒數視圖（MRS/MSR Rt,CNTV_TVAL_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RES0 | RO | - | 保留 |
| 31:0 | TVAL | RW | - | 倒數值（有號） |

## PMCR_EL0
- Offset: 0x168
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield PMCR_EL0_Type（FZS/FZO/LP 為 v8.5+ 欄位，本核心讀 0） — 欄位位置逐欄相符
- Description: Performance Monitors Control Register（MRS/MSR Rt,PMCR_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:33 | RES0 | RO | - | 保留 |
| 32 | FZS | RO | - | SPE 凍結（v8.7；本核心讀 0） |
| 31:24 | IMP | RO | - | 實作者代碼（同 MIDR 解讀） |
| 23:16 | IDCODE | RO | - | 識別碼 |
| 15:11 | N | RO | - | 事件計數器數量 |
| 10 | RES0 | RO | - | 保留 |
| 9 | FZO | RO | - | 溢位凍結（v8.7；本核心讀 0） |
| 8 | RES0 | RO | - | 保留 |
| 7 | LP | RO | - | 長事件計數器（v8.5；本核心讀 0） |
| 6 | LC | RW | - | 長週期計數器致能（64-bit cycle overflow） |
| 5 | DP | RW | - | 禁止情境下停用 cycle counter |
| 4 | X | RW | - | 事件匯出致能 |
| 3 | D | RW | - | cycle counter 除 64 |
| 2 | C | WO | - | 寫 1 歸零 PMCCNTR |
| 1 | P | WO | - | 寫 1 歸零全部事件計數器 |
| 0 | E | RW | 0 | 計數器總致能 |

### Enum: E
- 0: 全部計數器停用
- 1: 全部計數器啟用

## PMCNTENSET_EL0
- Offset: 0x170
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield PMCNTENSET_EL0_Type（以 A55 的 6 個事件計數器呈現） — 欄位位置逐欄相符
- Description: Performance Monitors Count Enable Set — 讀出目前致能；寫 1 設定（MRS/MSR Rt,PMCNTENSET_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:33 | RES0 | RO | - | 保留 |
| 32 | F0 | RO | - | 固定功能計數器 0（v9.4 欄位；本核心讀 0） |
| 31 | C | RW | - | PMCCNTR（cycle counter） |
| 30:6 | RES0 | RO | - | 保留（超出實作計數器數的位元 RAZ/WI） |
| 5 | P5 | RW | - | 事件計數器 5 |
| 4 | P4 | RW | - | 事件計數器 4 |
| 3 | P3 | RW | - | 事件計數器 3 |
| 2 | P2 | RW | - | 事件計數器 2 |
| 1 | P1 | RW | - | 事件計數器 1 |
| 0 | P0 | RW | - | 事件計數器 0 |

## PMOVSCLR_EL0
- Offset: 0x178
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield PMOVSCLR_EL0_Type（以 A55 的 6 個事件計數器呈現） — 欄位位置逐欄相符
- Description: Performance Monitors Overflow Flag Status Clear — 溢位旗標（寫 1 清除；MRS/MSR Rt,PMOVSCLR_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:33 | RES0 | RO | - | 保留 |
| 32 | F0 | RO | - | 固定功能計數器 0（v9.4 欄位；本核心讀 0） |
| 31 | C | RW | - | PMCCNTR（cycle counter） |
| 30:6 | RES0 | RO | - | 保留（超出實作計數器數的位元 RAZ/WI） |
| 5 | P5 | RW | - | 事件計數器 5 |
| 4 | P4 | RW | - | 事件計數器 4 |
| 3 | P3 | RW | - | 事件計數器 3 |
| 2 | P2 | RW | - | 事件計數器 2 |
| 1 | P1 | RW | - | 事件計數器 1 |
| 0 | P0 | RW | - | 事件計數器 0 |

## PMCCNTR_EL0
- Offset: 0x180
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） register PMCCNTR_EL0（無切分的整顆暫存器）
- Description: Performance Monitors Cycle Count — 64-bit 週期計數器（MRS/MSR Rt,PMCCNTR_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:0 | CCNT | RW | - | 週期計數值 |

## PMCCFILTR_EL0
- Offset: 0x188
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield PMCCFILTR_EL0_Type（NSK/NSU/NSH/M/SH/T/RL* 依安全狀態與擴充存在） — 欄位位置逐欄相符
- Description: Performance Monitors Cycle Count Filter — 週期計數的特權過濾（MRS/MSR Rt,PMCCFILTR_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:32 | RES0 | RO | - | 保留 |
| 31 | P | RW | - | EL1 不計數 |
| 30 | U | RW | - | EL0 不計數 |
| 29 | NSK | RW | - | Non-secure EL1 計數選擇 |
| 28 | NSU | RW | - | Non-secure EL0 計數選擇 |
| 27 | NSH | RW | - | EL2 計數致能 |
| 26 | M | RW | - | Secure EL3 計數選擇 |
| 25 | RES0 | RO | - | 保留 |
| 24 | SH | RW | - | Secure EL2 計數選擇（無 Secure EL2 時 RES0） |
| 23 | T | RW | - | 交易狀態過濾（無 TME 時 RES0） |
| 22 | RLK | RW | - | Realm EL1 計數（無 RME 時 RES0） |
| 21 | RLU | RW | - | Realm EL0 計數（無 RME 時 RES0） |
| 20 | RLH | RW | - | Realm EL2 計數（無 RME 時 RES0） |
| 19:0 | RES0 | RO | - | 保留 |

## PMSELR_EL0
- Offset: 0x190
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield PMSELR_EL0_Type — 欄位位置逐欄相符
- Description: Performance Monitors Event Counter Selection — 選擇 PMXEV* 操作的計數器（MRS/MSR Rt,PMSELR_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:5 | RES0 | RO | - | 保留 |
| 4:0 | SEL | RW | - | 計數器編號（31 = 選 PMCCNTR） |

## PMUSERENR_EL0
- Offset: 0x198
- Reset: -
- Verified: Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a、src/v8_base.sail） bitfield PMUSERENR_EL0_Type（TID/IR/UEN 為 v8.9/FEAT_PMUv3p9 欄位，本核心讀 0） — 欄位位置逐欄相符
- Description: Performance Monitors User Enable — EL0 存取 PMU 的許可（MRS/MSR Rt,PMUSERENR_EL0）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:7 | RES0 | RO | - | 保留 |
| 6 | TID | RO | - | trap ID（v8.9；本核心讀 0） |
| 5 | IR | RO | - | 指令引退唯讀（v8.9；本核心讀 0） |
| 4 | UEN | RO | - | 細粒度使用者致能（v8.9；本核心讀 0） |
| 3 | ER | RW | - | EL0 可讀事件計數器 |
| 2 | CR | RW | - | EL0 可讀 cycle counter |
| 1 | SW | RW | - | EL0 可寫 PMSWINC |
| 0 | EN | RW | 0 | EL0 存取 PMU 總致能 |

## CPUECTLR_EL1
- Offset: 0x1A0
- Reset: -
- Verified: ARM 官方 Trusted Firmware-A（ARM-software/arm-trusted-firmware include/lib/cpus/aarch64/cortex_a55.h） — 編碼 S3_0_C15_C1_4 與 L1WSCTL 位置經 ARM 官方原始碼核對
- Description: CPU Extended Control Register — 核心擴充控制（實作定義；MRS S3_0_C15_C1_4）。L1WSCTL 位置經 ARM 官方 TF-A 原始碼證實；其餘欄位依 2026-08 交叉審查轉錄自 A55 TRM §3.2.30（Figure 3-106），尚未親驗原文

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:40 | RES0 | RO | 0 | 保留（審查轉錄） |
| 39:38 | ATOM | RW | - | 原子指令處理行為控制（審查轉錄） |
| 37 | L2FLUSH | RW | - | L2 flush 控制（審查轉錄） |
| 36:31 | RES0 | RO | 0 | 保留（審查轉錄） |
| 30:29 | L3WSCTL | RW | - | L3 write streaming 門檻（審查轉錄） |
| 28:27 | L2WSCTL | RW | - | L2 write streaming 門檻（審查轉錄） |
| 26:25 | L1WSCTL | RW | - | L1 write streaming 門檻（ARM 官方 TF-A cortex_a55.h 證實位置） |
| 24:16 | RES0 | RO | 0 | 保留（審查轉錄） |
| 15:13 | L1PCTL | RW | - | L1 資料預取控制（審查轉錄） |
| 12:10 | L3PCTL | RW | - | L3 資料預取控制（審查轉錄） |
| 9:1 | RES0 | RO | 0 | 保留（審查轉錄） |
| 0 | EXTLLC | RW | - | 外部 last-level cache 存在指示（審查轉錄） |

## CPUACTLR_EL1
- Offset: 0x1A8
- Reset: -
- Verified: ARM 官方 Trusted Firmware-A（ARM-software/arm-trusted-firmware include/lib/cpus/aarch64/cortex_a55.h） — 編碼 S3_0_C15_C1_0 與三個 errata 位的位置經 ARM 官方原始碼核對
- Description: CPU Auxiliary Control Register（MRS S3_0_C15_C1_0）。⚠ A55 TRM（§3.2.28，審查確認）將整顆標為「Reserved for Arm internal use」——除非 Arm 指示，**不得修改**；下列三個具名位僅為 ARM 官方 TF-A errata workaround 所操作位置的證據（非公開穩定介面），其餘位元一律視為內部保留。2026-08 第四輪審查修正：整顆存取屬性為 RW（TRM accessibility 審查轉錄＋TF-A 以 MSR 寫入 errata 位佐證）——Access 欄記硬體屬性，「不得修改」是使用政策（本工具僅解碼 dump，不寫硬體），舊版把內部保留位標 RO 是把政策誤植成硬體語意

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:50 | INTERNAL | RW | - | Arm 內部保留（未經 Arm 指示不得修改） |
| 49 | DIS_L1_PGWLK | RW | - | 停用 L1 pagewalk 快取（TF-A errata 1221012） |
| 48:32 | INTERNAL2 | RW | - | Arm 內部保留（未經 Arm 指示不得修改） |
| 31 | DIS_DUAL_ISSUE | RW | - | 停用雙發射（TF-A errata 778703） |
| 30:25 | INTERNAL1 | RW | - | Arm 內部保留（未經 Arm 指示不得修改） |
| 24 | DIS_WR_STREAM | RW | - | 停用 write streaming（TF-A errata 778703） |
| 23:0 | INTERNAL0 | RW | - | Arm 內部保留（未經 Arm 指示不得修改） |

## CPUPWRCTLR_EL1
- Offset: 0x1B0
- Reset: -
- Verified: ARM 官方 Trusted Firmware-A（ARM-software/arm-trusted-firmware include/lib/cpus/aarch64/cortex_a55.h） — 編碼 S3_0_C15_C2_7 與 CORE_PWRDN_EN 位置經 ARM 官方原始碼核對
- Description: CPU Power Control Register — 核心電源控制（實作定義；MRS S3_0_C15_C2_7）。CORE_PWRDN_EN 位置經 ARM 官方 TF-A 證實；retention 欄位依 2026-08 交叉審查轉錄自 A55 TRM §3.2.35（Figure 3-111），尚未親驗原文

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 63:13 | RES0 | RO | 0 | 保留（審查轉錄） |
| 12:10 | SIMD_RET_CTRL | RW | - | Advanced SIMD/FP retention 進入延遲（審查轉錄） |
| 9:7 | WFE_RET_CTRL | RW | - | WFE retention 進入延遲（審查轉錄） |
| 6:4 | WFI_RET_CTRL | RW | - | WFI retention 進入延遲（審查轉錄） |
| 3:1 | RES0 | RO | 0 | 保留（審查轉錄） |
| 0 | CORE_PWRDN_EN | RW | 0 | WFI 時允許核心斷電（ARM 官方 TF-A 證實位置） |

### Enum: CORE_PWRDN_EN
- 0: WFI 不斷電
- 1: WFI 進入斷電
