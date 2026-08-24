# CPU: ARM Cortex-A55
# Version: r2p0 · ARMv8.2-A AArch64
# Width: 64
# Source: Arm Architecture Reference Manual for A-profile (ARM DDI 0487)／Cortex-A55 TRM (ARM 100442)
# Status: ⚠ 20 顆中有 14 顆的**欄位位置**已逐欄對照 Arm 機器可讀架構規格（rems-project/sail-arm arm-v9.4-a 的 bitfield 定義，由 Arm 官方 machine-readable specification 產生），125 個具名欄位全數相符（出處見各暫存器的 Verified）；另 6 顆（CurrentEL／DAIF／VBAR_EL1／FAR_EL1／ELR_EL1／CNTFRQ_EL0）該模型沒有對應 bitfield，仍未對照。**尚未對照 Cortex-A55 TRM 與 DDI 0487 原文**（本環境無法連上 developer.arm.com）：本核心是 Armv8.2-A，v8.3 之後才加入的欄位在本檔一律標 RES0；Reset 值與 IMPLEMENTATION DEFINED 的部分都還沒核對。落差見本檔開頭的註解
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

  ── 與官方文件的落差 ───────────────────────────────────────────────
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
| 29    | LSMAOE   | RW     | -     | Load/Store multiple 原子性與順序（相容性位元） |
| 28    | nTLSMD   | RW     | -     | 對 Device 記憶體的 Load/Store multiple 是否受限 |
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
| 51:48 | DIT      | RO     | -     | 資料無關時序（ARMv8.4） |
| 47:44 | AMU      | RO     | -     | 活動監控單元 |
| 43:40 | MPAM     | RO     | -     | 記憶體分區與監控 |
| 39:36 | SEL2     | RO     | -     | Secure EL2 |
| 35:32 | SVE      | RO     | -     | 可縮放向量擴充 |
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
- Description: AArch64 Memory Model Feature Register 0 — 實體位址範圍與頁面大小支援度

| Bits  | Field     | Access | Reset | Description |
|-------|-----------|--------|-------|-------------|
| 63:48 | RES0      | RO     | 0     | 保留 |
| 47:44 | ExS       | RO     | -     | 例外進出時的內容同步 |
| 43:40 | TGran4_2  | RO     | -     | 第 2 階轉換的 4 KB 頁支援 |
| 39:36 | TGran64_2 | RO     | -     | 第 2 階轉換的 64 KB 頁支援 |
| 35:32 | TGran16_2 | RO     | -     | 第 2 階轉換的 16 KB 頁支援 |
| 31:28 | TGran4    | RO     | -     | 4 KB 頁支援 |
| 27:24 | TGran64   | RO     | -     | 64 KB 頁支援 |
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
