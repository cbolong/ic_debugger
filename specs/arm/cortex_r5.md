# CPU: ARM Cortex-R5
# Version: r1p2 · ARMv7-R
# Width: 32
# Source: ARM Architecture Reference Manual ARMv7-A/R (ARM DDI 0406C)／Cortex-R5 TRM (ARM DDI 0460)
# Status: 架構定義欄位已整理完成；Reset 標「-」者依組態接腳或實作而異。實作定義暫存器（ACTLR／ADFSR 等）尚未收錄，見檔尾待補清單。正式使用前請對照貴專案的 TRM 版本核對
# Description: ARMv7-R CP15 系統控制暫存器、故障狀態暫存器與 MPU 區域暫存器（常用子集）

<!--
  ── Offset 對應約定 ────────────────────────────────────────────────
  Offset ＝ 此暫存器的值在 bin dump 中的「位元組位移」（從 0 起算），
  不是 CP15 的 (CRn, op1, CRm, op2) 編碼。請讓 dump 腳本的輸出順序與
  下面的 Offset 順序一致（examples/sample_r5.bin 即依此順序產生）。

  ── 尚未收錄（實作定義，需查 Cortex-R5 TRM 逐欄補上）──────────────
  * ACTLR      (c1,0,c0,1)  輔助控制：ECC／FPU／匯流排行為開關
  * ADFSR      (c5,0,c1,0)  輔助資料故障狀態（ECC 錯誤資訊）
  * AIFSR      (c5,0,c1,1)  輔助指令故障狀態
  * TCMTR      (c0,0,c0,2)  TCM 型態
  * SLPCTL／PWRCTL          低功耗控制（依 SoC 整合而異）
  * PMCR 等效能監控群組      (c9,0,c12,x)
  補的時候照本檔格式即可；補完把上面的 Status 一併更新。
-->

## MIDR
- Offset: 0x000
- Reset: 0x411FC152
- Description: Main ID Register — CPU 識別碼

| Bits  | Field        | Access | Reset | Description |
|-------|--------------|--------|-------|-------------|
| 31:24 | Implementer  | RO     | 0x41  | 實作者代碼 |
| 23:20 | Variant      | RO     | 0x1   | 主要版本（rXpY 的 X） |
| 19:16 | Architecture | RO     | 0xF   | 架構代碼 |
| 15:4  | PartNum      | RO     | 0xC15 | 部件編號 |
| 3:0   | Revision     | RO     | 0x2   | 次要版本（rXpY 的 Y） |

### Enum: Implementer
- 0x41: ARM Limited

### Enum: Architecture
- 0xF: 由 CPUID scheme 定義（ARMv7 之後固定值）

### Enum: PartNum
- 0xC15: Cortex-R5

## CTR
- Offset: 0x004
- Reset: 0x8003C003
- Description: Cache Type Register — 快取架構資訊

| Bits  | Field    | Access | Reset | Description |
|-------|----------|--------|-------|-------------|
| 31:29 | Format   | RO     | 0b100 | 暫存器格式 |
| 28    | RES0     | RO     | 0     | 保留 |
| 27:24 | CWG      | RO     | 0x0   | Cache writeback granule |
| 23:20 | ERG      | RO     | 0x0   | Exclusives reservation granule |
| 19:16 | DminLine | RO     | 0x3   | 最小 D-cache line（log2 words；3 = 32 bytes） |
| 15:14 | L1Ip     | RO     | 0b11  | L1 I-cache 索引／標籤策略 |
| 13:4  | RES0     | RO     | 0     | 保留 |
| 3:0   | IminLine | RO     | 0x3   | 最小 I-cache line（log2 words；3 = 32 bytes） |

### Enum: Format
- 0b100: ARMv7 格式

### Enum: L1Ip
- 0b01: AIVIVT
- 0b10: VIPT
- 0b11: PIPT

## MPUIR
- Offset: 0x008
- Reset: -
- Description: MPU Type Register — MPU 區域數量組態（唯讀，依合成參數而定）

| Bits  | Field   | Access | Reset | Description |
|-------|---------|--------|-------|-------------|
| 31:24 | RES0    | RO     | 0     | 保留 |
| 23:16 | IRegion | RO     | 0x0   | 獨立 I-side 區域數（R5 為統一 MPU，固定 0） |
| 15:8  | DRegion | RO     | -     | MPU 區域數量 |
| 7:1   | RES0    | RO     | 0     | 保留 |
| 0     | nU      | RO     | 0     | MPU 統一／分離 |

### Enum: DRegion
- 0x00: 未實作 MPU
- 0x0C: 12 個區域
- 0x10: 16 個區域

### Enum: nU
- 0: 統一（unified）MPU
- 1: 分離（I／D 各自）MPU

## MPIDR
- Offset: 0x00C
- Reset: -
- Description: Multiprocessor Affinity Register — 多處理器親和性（識別本核心在叢集中的位置）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31    | M     | RO     | 1     | 固定為 1（表示採用多處理器格式） |
| 30    | U     | RO     | -     | 單處理器旗標 |
| 29:25 | RES0  | RO     | 0     | 保留 |
| 24    | MT    | RO     | -     | 多執行緒實作旗標 |
| 23:16 | Aff2  | RO     | -     | 親和性層級 2（實作定義） |
| 15:8  | Aff1  | RO     | -     | 親和性層級 1（叢集編號） |
| 7:0   | Aff0  | RO     | -     | 親和性層級 0（核心編號；twin-CPU 時為 0 或 1） |

### Enum: U
- 0: 多處理器系統中的一員
- 1: 單處理器

### Enum: MT
- 0: 各核心獨立
- 1: 以多執行緒方式實作

## SCTLR
- Offset: 0x010
- Reset: -
- Description: System Control Register — 核心主控制（Reset 值依 VINITHI／CFGEE／TEINIT 等組態接腳而異）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31    | IE    | RO     | -     | 指令 endianness（依 CFGIE 接腳） |
| 30    | TE    | RW     | -     | 例外進入時的指令集狀態（依 TEINIT 接腳） |
| 29:28 | RES0  | RO     | 0     | 保留 |
| 27    | NMFI  | RO     | -     | Non-maskable FIQ（依 CFGNMFI 接腳） |
| 26    | RES0  | RO     | 0     | 保留 |
| 25    | EE    | RW     | -     | 例外時載入 CPSR.E 的值（依 CFGEE 接腳） |
| 24    | VE    | RW     | 0     | 中斷向量化（VIC 埠） |
| 23    | RES1  | RO     | 1     | 保留，讀為 1 |
| 22    | U     | RO     | 1     | 對齊模型（ARMv7 固定為 1） |
| 21    | FI    | RO     | -     | 低延遲中斷組態 |
| 20    | RES0  | RO     | 0     | 保留 |
| 19    | DZ    | RW     | 0     | 除以零行為 |
| 18    | RES1  | RO     | 1     | 保留，讀為 1 |
| 17    | BR    | RW     | 0     | MPU 背景區（background region） |
| 16    | RES1  | RO     | 1     | 保留，讀為 1 |
| 15    | RES0  | RO     | 0     | 保留 |
| 14    | RR    | RW     | 0     | 快取替換策略 |
| 13    | V     | RW     | -     | 例外向量基底（依 VINITHI 接腳） |
| 12    | I     | RW     | 0     | L1 指令快取致能 |
| 11    | Z     | RW     | 0     | 分支預測致能 |
| 10    | SW    | RW     | 0     | SWP／SWPB 指令致能 |
| 9:7   | RES0  | RO     | 0     | 保留 |
| 6:3   | RES1  | RO     | 0xF   | 保留，讀為 1 |
| 2     | C     | RW     | 0     | L1 資料快取致能 |
| 1     | A     | RW     | 0     | 對齊檢查致能 |
| 0     | M     | RW     | 0     | MPU 致能 |

### Enum: IE
- 0: 指令為 little-endian
- 1: 指令為 big-endian

### Enum: TE
- 0: 例外以 ARM 狀態進入
- 1: 例外以 Thumb 狀態進入

### Enum: NMFI
- 0: FIQ 可被遮罩
- 1: FIQ 不可遮罩（non-maskable）

### Enum: EE
- 0: 例外時資料為 little-endian
- 1: 例外時資料為 big-endian

### Enum: VE
- 0: 使用 0x18 的 IRQ 例外向量
- 1: 由 VIC 埠提供 handler 位址

### Enum: FI
- 0: 一般中斷延遲
- 1: 低延遲中斷組態（部分多週期指令不可中斷）

### Enum: DZ
- 0: 除以零回傳 0，不產生例外
- 1: 除以零產生 Undefined Instruction 例外

### Enum: BR
- 0: 背景區關閉（region 未命中即 fault）
- 1: 特權存取以預設記憶體映射為背景區

### Enum: RR
- 0: Random 替換
- 1: Round-robin 替換

### Enum: V
- 0: 例外向量在 0x00000000
- 1: 例外向量在 0xFFFF0000（高位向量）

### Enum: I
- 0: I-cache 關閉
- 1: I-cache 開啟

### Enum: Z
- 0: 分支預測關閉
- 1: 分支預測開啟

### Enum: SW
- 0: SWP／SWPB 為 Undefined
- 1: SWP／SWPB 可執行

### Enum: C
- 0: D-cache 關閉
- 1: D-cache 開啟

### Enum: A
- 0: 不做對齊檢查
- 1: 未對齊存取產生 Alignment fault

### Enum: M
- 0: MPU 關閉（使用預設記憶體映射）
- 1: MPU 開啟

## CPACR
- Offset: 0x014
- Reset: 0x00000000
- Description: Coprocessor Access Control Register — 協同處理器（FPU）存取權限

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:24 | RES0  | RO     | 0     | 保留（R5 未實作 ASEDIS／D32DIS，RAZ/WI） |
| 23:22 | cp11  | RW     | 0b00  | cp11（FPU 資料傳輸）存取權限 |
| 21:20 | cp10  | RW     | 0b00  | cp10（FPU）存取權限 |
| 19:0  | RES0  | RO     | 0     | cp0–cp9 存取控制（R5 未實作這些協同處理器，RAZ/WI） |

### Enum: cp11
- 0b00: 拒絕存取（存取產生 Undefined 例外）
- 0b01: 僅特權模式可存取
- 0b10: 保留
- 0b11: 完全存取

### Enum: cp10
- 0b00: 拒絕存取（存取產生 Undefined 例外）
- 0b01: 僅特權模式可存取
- 0b10: 保留
- 0b11: 完全存取

## CPSR
- Offset: 0x018
- Reset: -
- Description: Current Program Status Register — 目前處理器狀態（模式、中斷遮罩、條件旗標）

| Bits  | Field   | Access | Reset | Description |
|-------|---------|--------|-------|-------------|
| 31    | N       | RW     | -     | 負值條件旗標 |
| 30    | Z       | RW     | -     | 零值條件旗標 |
| 29    | C       | RW     | -     | 進位條件旗標 |
| 28    | V       | RW     | -     | 溢位條件旗標 |
| 27    | Q       | RW     | -     | 累積飽和旗標 |
| 26:25 | IT[1:0] | RW     | -     | If-Then 狀態低位 |
| 24    | J       | RW     | 0     | Jazelle 狀態 |
| 23:20 | RES0    | RO     | 0     | 保留 |
| 19:16 | GE      | RW     | -     | SIMD 大於等於旗標 |
| 15:10 | IT[7:2] | RW     | -     | If-Then 狀態高位 |
| 9     | E       | RW     | -     | 資料 endianness（0=little） |
| 8     | A       | RW     | 1     | 非同步中止（abort）遮罩 |
| 7     | I       | RW     | 1     | IRQ 遮罩 |
| 6     | F       | RW     | 1     | FIQ 遮罩 |
| 5     | T       | RW     | -     | Thumb 狀態 |
| 4:0   | M       | RW     | -     | 處理器模式 |

### Enum: E
- 0: 資料存取為 little-endian
- 1: 資料存取為 big-endian

### Enum: A
- 0: 非同步中止未遮罩
- 1: 非同步中止已遮罩

### Enum: I
- 0: IRQ 開啟
- 1: IRQ 已遮罩（關閉）

### Enum: F
- 0: FIQ 開啟
- 1: FIQ 已遮罩（關閉）

### Enum: T
- 0: ARM 狀態
- 1: Thumb 狀態

### Enum: M
- 0b10000: User 模式
- 0b10001: FIQ 模式
- 0b10010: IRQ 模式
- 0b10011: Supervisor 模式
- 0b10111: Abort 模式
- 0b11011: Undefined 模式
- 0b11111: System 模式

## DFSR
- Offset: 0x01C
- Reset: -
- Description: Data Fault Status Register — 最近一次資料中止（abort）的狀態

| Bits  | Field   | Access | Reset | Description |
|-------|---------|--------|-------|-------------|
| 31:13 | RES0    | RO     | 0     | 保留 |
| 12    | ExT     | RW     | -     | 外部 abort 類型（AXI 錯誤分類） |
| 11    | WnR     | RW     | -     | 發生 fault 的存取方向 |
| 10    | FS[4]   | RW     | -     | Fault status 位元 4（與 FS[3:0] 合成 5-bit 狀態碼） |
| 9:4   | RES0    | RO     | 0     | 保留 |
| 3:0   | FS[3:0] | RW     | -     | Fault status 位元 3:0（下列意義以 FS[4]=0 為準） |

### Enum: WnR
- 0: 讀取時發生
- 1: 寫入時發生

### Enum: FS[3:0]
- 0b0000: 背景 fault（MPU 無區域命中）
- 0b0001: 對齊（alignment）fault
- 0b0010: 除錯事件
- 0b1000: 同步外部 abort
- 0b1101: 權限（permission）fault

## IFSR
- Offset: 0x020
- Reset: -
- Description: Instruction Fault Status Register — 最近一次預取中止的狀態

| Bits  | Field   | Access | Reset | Description |
|-------|---------|--------|-------|-------------|
| 31:13 | RES0    | RO     | 0     | 保留 |
| 12    | ExT     | RW     | -     | 外部 abort 類型 |
| 11    | RES0    | RO     | 0     | 保留 |
| 10    | FS[4]   | RW     | -     | Fault status 位元 4 |
| 9:4   | RES0    | RO     | 0     | 保留 |
| 3:0   | FS[3:0] | RW     | -     | Fault status 位元 3:0（意義同 DFSR） |

### Enum: FS[3:0]
- 0b0000: 背景 fault（MPU 無區域命中）
- 0b0001: 對齊（alignment）fault
- 0b0010: 除錯事件
- 0b1000: 同步外部 abort
- 0b1101: 權限（permission）fault

## DFAR
- Offset: 0x024
- Reset: -
- Description: Data Fault Address Register — 造成資料 abort 的存取位址

| Bits | Field   | Access | Reset | Description |
|------|---------|--------|-------|-------------|
| 31:0 | Address | RW     | -     | fault 位址 |

## IFAR
- Offset: 0x028
- Reset: -
- Description: Instruction Fault Address Register — 造成預取 abort 的指令位址

| Bits | Field   | Access | Reset | Description |
|------|---------|--------|-------|-------------|
| 31:0 | Address | RW     | -     | fault 位址 |

## RGNR
- Offset: 0x02C
- Reset: -
- Description: MPU Region Number Register — 選擇後續 DRBAR／DRSR／DRACR 要存取的區域

| Bits | Field  | Access | Reset | Description |
|------|--------|--------|-------|-------------|
| 31:8 | RES0   | RO     | 0     | 保留 |
| 7:0  | Region | RW     | -     | 目前選取的 MPU 區域編號 |

## DRBAR
- Offset: 0x030
- Reset: -
- Description: MPU Region Base Address Register — RGNR 所選區域的基底位址

| Bits | Field       | Access | Reset | Description |
|------|-------------|--------|-------|-------------|
| 31:5 | BaseAddress | RW     | -     | 區域基底位址（32-byte 對齊；欄位值即位址的 [31:5]） |
| 4:0  | RES0        | RO     | 0     | 保留 |

## DRSR
- Offset: 0x034
- Reset: -
- Description: MPU Region Size and Enable Register — 區域大小、子區域停用與致能

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:16 | RES0  | RO     | 0     | 保留 |
| 15:8  | SRD   | RW     | -     | 子區域停用位元（每個位元對應 1/8 區域，1 = 停用） |
| 7:6   | RES0  | RO     | 0     | 保留 |
| 5:1   | RSIZE | RW     | -     | 區域大小；實際大小 = 2^(RSIZE+1) bytes |
| 0     | EN    | RW     | 0     | 區域致能 |

### Enum: RSIZE
- 0b00100: 32 bytes（最小值）
- 0b01001: 1 KB
- 0b01011: 4 KB
- 0b10011: 1 MB
- 0b11011: 256 MB
- 0b11111: 4 GB（最大值）

### Enum: EN
- 0: 區域關閉
- 1: 區域啟用

## DRACR
- Offset: 0x038
- Reset: -
- Description: MPU Region Access Control Register — 區域存取權限與記憶體屬性

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:13 | RES0  | RO     | 0     | 保留 |
| 12    | XN    | RW     | -     | 禁止執行（Execute Never） |
| 11    | RES0  | RO     | 0     | 保留 |
| 10:8  | AP    | RW     | -     | 存取權限 |
| 7:6   | RES0  | RO     | 0     | 保留 |
| 5:3   | TEX   | RW     | -     | 型態擴充（與 C／B 共同決定記憶體型態） |
| 2     | S     | RW     | -     | 可共享（Shareable） |
| 1     | C     | RW     | -     | 可快取（Cacheable） |
| 0     | B     | RW     | -     | 可緩衝（Bufferable） |

### Enum: XN
- 0: 允許執行
- 1: 禁止執行（取指會產生 permission fault）

### Enum: AP
- 0b000: 任何模式皆不可存取
- 0b001: 僅特權模式可讀寫
- 0b010: 特權可讀寫、User 唯讀
- 0b011: 特權與 User 皆可讀寫
- 0b101: 僅特權模式唯讀
- 0b110: 特權與 User 皆唯讀
- 0b111: 特權與 User 皆唯讀（已棄用編碼）

### Enum: S
- 0: 不可共享
- 1: 可共享

## ATCMRR
- Offset: 0x03C
- Reset: -
- Description: ATCM Region Register — ATCM 基底位址、大小與致能（大小為唯讀，由合成組態決定）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:12 | Base  | RW     | -     | TCM 基底位址（4KB 對齊；欄位值即位址的 [31:12]） |
| 11:7  | RES0  | RO     | 0     | 保留 |
| 6:2   | Size  | RO     | -     | TCM 大小 |
| 1     | RES0  | RO     | 0     | 保留 |
| 0     | EN    | RW     | -     | TCM 致能（Reset 值依 INITRAM 接腳） |

### Enum: Size
- 0b00000: 0 KB（未實作）
- 0b00011: 4 KB
- 0b00100: 8 KB
- 0b00101: 16 KB
- 0b00110: 32 KB
- 0b00111: 64 KB
- 0b01000: 128 KB
- 0b01001: 256 KB
- 0b01010: 512 KB
- 0b01011: 1 MB

### Enum: EN
- 0: TCM 關閉
- 1: TCM 開啟

## BTCMRR
- Offset: 0x040
- Reset: -
- Description: BTCM Region Register — BTCM 基底位址、大小與致能

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:12 | Base  | RW     | -     | TCM 基底位址（4KB 對齊） |
| 11:7  | RES0  | RO     | 0     | 保留 |
| 6:2   | Size  | RO     | -     | TCM 大小（編碼同 ATCMRR.Size） |
| 1     | RES0  | RO     | 0     | 保留 |
| 0     | EN    | RW     | -     | TCM 致能 |

### Enum: Size
- 0b00000: 0 KB（未實作）
- 0b00011: 4 KB
- 0b00100: 8 KB
- 0b00101: 16 KB
- 0b00110: 32 KB
- 0b00111: 64 KB
- 0b01000: 128 KB
- 0b01001: 256 KB
- 0b01010: 512 KB
- 0b01011: 1 MB

### Enum: EN
- 0: TCM 關閉
- 1: TCM 開啟
