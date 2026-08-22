# CPU: ARM Cortex-R5
# Version: r1p2
# Width: 32
# Source: ARM DDI 0460D（Cortex-R5 TRM）／ARM DDI 0406C（ARMv7-AR ARM）
# Description: 範例 spec：Cortex-R5 系統控制暫存器（CP15）節錄。本檔同時是 SPEC_FORMAT.md 的實際範例；內容為常用暫存器子集，正式使用前請對照 TRM 原文逐欄確認。

<!--
  Offset 是「此暫存器的值在 bin dump 中的位元組位移」（從 0 開始），
  不是 CP15 的暫存器編號。dump 的實際順序依你的 dump 腳本而定，
  請讓這裡的 Offset 與 dump 腳本的輸出順序一致。
-->

## MIDR
- Offset: 0x000
- Reset: 0x411FC152
- Description: Main ID Register — CPU 識別碼

| Bits  | Field       | Access | Reset | Description |
|-------|-------------|--------|-------|-------------|
| 31:24 | Implementer | RO     | 0x41  | 實作者代碼 |
| 23:20 | Variant     | RO     | 0x1   | 主要版本（rXpY 的 X） |
| 19:16 | Architecture| RO     | 0xF   | 架構代碼 |
| 15:4  | PartNum     | RO     | 0xC15 | 部件編號 |
| 3:0   | Revision    | RO     | 0x2   | 次要版本（rXpY 的 Y） |

### Enum: Implementer
- 0x41: ARM Limited

### Enum: Architecture
- 0xF: 由 CPUID scheme 定義（v7 之後固定值）

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
| 19:16 | DminLine | RO     | 0x3   | 最小 D-cache line 大小（log2 words；3 = 32 bytes） |
| 15:14 | L1Ip     | RO     | 0b11  | L1 I-cache 索引/標籤策略 |
| 13:4  | RES0     | RO     | 0     | 保留 |
| 3:0   | IminLine | RO     | 0x3   | 最小 I-cache line 大小（log2 words；3 = 32 bytes） |

### Enum: Format
- 0b100: ARMv7 格式

### Enum: L1Ip
- 0b01: AIVIVT
- 0b10: VIPT
- 0b11: PIPT

## MPIDR
- Offset: 0x008
- Reset: -
- Description: Multiprocessor Affinity Register — 多處理器親和性（依單核／twin-CPU 組態而異）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31    | M     | RO     | 1     | 1 = 有實作多處理器擴充 |
| 30    | U     | RO     | -     | 單處理器旗標 |
| 29:8  | RES0  | RO     | 0     | 保留／實作定義欄位（詳見 TRM） |
| 7:0   | CPUID | RO     | -     | CPU 編號（twin-CPU 組態時為 0 或 1） |

### Enum: U
- 0: 多處理器系統中的一員
- 1: 單處理器

## MPUIR
- Offset: 0x00C
- Reset: -
- Description: MPU Type Register — MPU region 組態

| Bits  | Field   | Access | Reset | Description |
|-------|---------|--------|-------|-------------|
| 31:24 | RES0    | RO     | 0     | 保留 |
| 23:16 | IRegion | RO     | 0x0   | 獨立 I-side region 數（R5 為統一 MPU，固定 0） |
| 15:8  | DRegion | RO     | -     | MPU region 數量 |
| 7:1   | RES0    | RO     | 0     | 保留 |
| 0     | nU      | RO     | 0     | MPU 統一／分離 |

### Enum: DRegion
- 0x00: 未實作 MPU
- 0x0C: 12 個 region
- 0x10: 16 個 region

### Enum: nU
- 0: 統一（unified）MPU
- 1: 分離（I/D 各自）MPU

## SCTLR
- Offset: 0x010
- Reset: -
- Description: System Control Register — 核心主控制（reset 值依組態接腳 VINITHI／CFGEE／TEINIT 等而異）

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
- 0: Little-endian
- 1: Big-endian

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
| 31:24 | RES0  | RO     | 0     | 保留（R5 無 ASEDIS／D32DIS 等功能，RAZ/WI） |
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

## DFSR
- Offset: 0x018
- Reset: -
- Description: Data Fault Status Register — 最近一次資料中止（abort）的狀態

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:13 | RES0  | RO     | 0     | 保留 |
| 12    | ExT   | RW     | -     | 外部 abort 類型（AXI 錯誤分類） |
| 11    | WnR   | RW     | -     | 發生 fault 的存取方向 |
| 10    | FS4   | RW     | -     | Fault status bit[4]（與 FS[3:0] 組成 5-bit 狀態碼） |
| 9:4   | RES0  | RO     | 0     | 保留 |
| 3:0   | FS    | RW     | -     | Fault status bits[3:0]（下列意義以 FS4=0 為準） |

### Enum: WnR
- 0: 讀取時發生
- 1: 寫入時發生

### Enum: FS
- 0b0000: 背景 fault（MPU 無 region 命中）
- 0b0001: 對齊（alignment）fault
- 0b0010: 除錯事件
- 0b1000: 同步外部 abort
- 0b1101: 權限（permission）fault

## IFSR
- Offset: 0x01C
- Reset: -
- Description: Instruction Fault Status Register — 最近一次預取中止的狀態

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:13 | RES0  | RO     | 0     | 保留 |
| 12    | ExT   | RW     | -     | 外部 abort 類型 |
| 11    | RES0  | RO     | 0     | 保留 |
| 10    | FS4   | RW     | -     | Fault status bit[4] |
| 9:4   | RES0  | RO     | 0     | 保留 |
| 3:0   | FS    | RW     | -     | Fault status bits[3:0]（意義同 DFSR.FS） |

## DFAR
- Offset: 0x020
- Reset: -
- Description: Data Fault Address Register — 造成資料 abort 的存取位址

| Bits | Field   | Access | Reset | Description |
|------|---------|--------|-------|-------------|
| 31:0 | Address | RW     | -     | fault 位址 |

## IFAR
- Offset: 0x024
- Reset: -
- Description: Instruction Fault Address Register — 造成預取 abort 的指令位址

| Bits | Field   | Access | Reset | Description |
|------|---------|--------|-------|-------------|
| 31:0 | Address | RW     | -     | fault 位址 |

## ATCMRR
- Offset: 0x028
- Reset: -
- Description: ATCM Region Register — ATCM 基底位址與大小（大小由組態決定，唯讀）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:12 | Base  | RW     | -     | TCM 基底位址（4KB 對齊，值為位址 [31:12]） |
| 11:7  | RES0  | RO     | 0     | 保留 |
| 6:2   | Size  | RO     | -     | TCM 大小 |
| 1     | RES0  | RO     | 0     | 保留 |
| 0     | EN    | RW     | -     | TCM 致能（reset 值依 INITRAM 接腳） |

### Enum: Size
- 0b00000: 0KB（未實作）
- 0b00011: 4KB
- 0b00100: 8KB
- 0b00101: 16KB
- 0b00110: 32KB
- 0b00111: 64KB
- 0b01000: 128KB
- 0b01001: 256KB
- 0b01010: 512KB
- 0b01011: 1MB

### Enum: EN
- 0: TCM 關閉
- 1: TCM 開啟

## BTCMRR
- Offset: 0x02C
- Reset: -
- Description: BTCM Region Register — BTCM 基底位址與大小

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:12 | Base  | RW     | -     | TCM 基底位址（4KB 對齊） |
| 11:7  | RES0  | RO     | 0     | 保留 |
| 6:2   | Size  | RO     | -     | TCM 大小（編碼同 ATCMRR.Size） |
| 1     | RES0  | RO     | 0     | 保留 |
| 0     | EN    | RW     | -     | TCM 致能 |

### Enum: Size
- 0b00000: 0KB（未實作）
- 0b00011: 4KB
- 0b00100: 8KB
- 0b00101: 16KB
- 0b00110: 32KB
- 0b00111: 64KB
- 0b01000: 128KB
- 0b01001: 256KB
- 0b01010: 512KB
- 0b01011: 1MB

### Enum: EN
- 0: TCM 關閉
- 1: TCM 開啟
