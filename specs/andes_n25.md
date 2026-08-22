# CPU: Andes N25
# Version: RV32（標準 CSR 節錄）
# Width: 32
# Source: RISC-V Privileged Architecture v1.11／Andes AndeStar V5
# Description: 範例 spec：RISC-V 標準 Machine-mode CSR 節錄。Andes 專屬 CSR（micm_cfg、mdcm_cfg、mmisc_ctl 等）請依 N25 datasheet 依同樣格式補上。

## mvendorid
- Offset: 0x000
- Reset: -
- Description: 供應商識別碼（JEDEC 編碼；值依實作而定）

| Bits | Field  | Access | Reset | Description |
|------|--------|--------|-------|-------------|
| 31:7 | Bank   | RO     | -     | JEDEC bank 數 |
| 6:0  | Offset | RO     | -     | JEDEC ID（bank 內編號） |

## marchid
- Offset: 0x004
- Reset: -
- Description: 微架構識別碼

| Bits | Field  | Access | Reset | Description |
|------|--------|--------|-------|-------------|
| 31:0 | ArchID | RO     | -     | 架構 ID（Andes 系列各核心不同） |

## mimpid
- Offset: 0x008
- Reset: -
- Description: 實作版本識別碼

| Bits | Field  | Access | Reset | Description |
|------|--------|--------|-------|-------------|
| 31:0 | ImpID  | RO     | -     | 實作版本 |

## mhartid
- Offset: 0x00C
- Reset: -
- Description: Hart（硬體執行緒）編號

| Bits | Field  | Access | Reset | Description |
|------|--------|--------|-------|-------------|
| 31:0 | HartID | RO     | -     | 本核心的 hart 編號（單核為 0） |

## misa
- Offset: 0x010
- Reset: -
- Description: ISA 與擴充指令集組態

| Bits  | Field      | Access | Reset | Description |
|-------|------------|--------|-------|-------------|
| 31:30 | MXL        | RO     | 0b01  | Machine XLEN |
| 29:26 | RES0       | RO     | 0     | 保留 |
| 25:0  | Extensions | RO     | -     | 各 bit 對應一個擴充：bit0=A、bit2=C、bit3=D、bit5=F、bit8=I、bit12=M、bit18=S、bit20=U、bit23=X（自訂擴充） |

### Enum: MXL
- 0b01: XLEN = 32
- 0b10: XLEN = 64
- 0b11: XLEN = 128

## mstatus
- Offset: 0x014
- Reset: -
- Description: Machine 狀態暫存器 — 全域中斷致能與特權狀態

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31    | SD    | RO     | 0     | FS/XS 有 dirty 狀態的摘要位 |
| 30:23 | RES0  | RO     | 0     | 保留 |
| 22    | TSR   | RW     | 0     | 攔截 S-mode 的 SRET（無 S-mode 時為 0） |
| 21    | TW    | RW     | 0     | 攔截 WFI（timeout wait） |
| 20    | TVM   | RW     | 0     | 攔截虛擬記憶體管理操作 |
| 19    | MXR   | RW     | 0     | 可讀取標記為 execute-only 的頁 |
| 18    | SUM   | RW     | 0     | S-mode 可存取 U-mode 頁 |
| 17    | MPRV  | RW     | 0     | Load/Store 以 MPP 特權等級進行位址轉換 |
| 16:15 | XS    | RO     | 0b00  | 自訂擴充單元狀態 |
| 14:13 | FS    | RW     | 0b00  | 浮點單元狀態 |
| 12:11 | MPP   | RW     | 0b00  | 進入 trap 前的特權模式（M-mode previous privilege） |
| 10:9  | RES0  | RO     | 0     | 保留 |
| 8     | SPP   | RW     | 0     | S-mode previous privilege |
| 7     | MPIE  | RW     | 0     | 進入 trap 前的 MIE 備份 |
| 6     | RES0  | RO     | 0     | 保留 |
| 5     | SPIE  | RW     | 0     | 進入 trap 前的 SIE 備份 |
| 4     | RES0  | RO     | 0     | 保留 |
| 3     | MIE   | RW     | 0     | Machine 全域中斷致能 |
| 2     | RES0  | RO     | 0     | 保留 |
| 1     | SIE   | RW     | 0     | Supervisor 全域中斷致能 |
| 0     | RES0  | RO     | 0     | 保留 |

### Enum: FS
- 0b00: Off（FPU 關閉，存取 FPU 產生非法指令例外）
- 0b01: Initial
- 0b10: Clean
- 0b11: Dirty

### Enum: MPP
- 0b00: User mode
- 0b01: Supervisor mode
- 0b11: Machine mode

### Enum: MIE
- 0: Machine 中斷全域關閉
- 1: Machine 中斷全域開啟

## mtvec
- Offset: 0x018
- Reset: -
- Description: Trap 向量基底位址與模式

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| 31:2 | BASE  | RW     | -     | 向量表基底位址（4-byte 對齊；欄位值 = 位址 >> 2） |
| 1:0  | MODE  | RW     | -     | 向量模式 |

### Enum: MODE
- 0b00: Direct — 所有 trap 跳到 BASE
- 0b01: Vectored — 中斷跳到 BASE + 4 × cause

## mie
- Offset: 0x01C
- Reset: 0x00000000
- Description: Machine 中斷致能（各中斷源開關）

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:12 | RES0  | RO     | 0     | 保留（含平台自訂中斷，依實作） |
| 11    | MEIE  | RW     | 0     | Machine 外部中斷致能 |
| 10    | RES0  | RO     | 0     | 保留 |
| 9     | SEIE  | RW     | 0     | Supervisor 外部中斷致能 |
| 8     | RES0  | RO     | 0     | 保留 |
| 7     | MTIE  | RW     | 0     | Machine 計時器中斷致能 |
| 6     | RES0  | RO     | 0     | 保留 |
| 5     | STIE  | RW     | 0     | Supervisor 計時器中斷致能 |
| 4     | RES0  | RO     | 0     | 保留 |
| 3     | MSIE  | RW     | 0     | Machine 軟體中斷致能 |
| 2     | RES0  | RO     | 0     | 保留 |
| 1     | SSIE  | RW     | 0     | Supervisor 軟體中斷致能 |
| 0     | RES0  | RO     | 0     | 保留 |

## mip
- Offset: 0x020
- Reset: -
- Description: Machine 中斷待處理（pending）狀態

| Bits  | Field | Access | Reset | Description |
|-------|-------|--------|-------|-------------|
| 31:12 | RES0  | RO     | 0     | 保留 |
| 11    | MEIP  | RO     | -     | Machine 外部中斷 pending |
| 10    | RES0  | RO     | 0     | 保留 |
| 9     | SEIP  | RW     | -     | Supervisor 外部中斷 pending |
| 8     | RES0  | RO     | 0     | 保留 |
| 7     | MTIP  | RO     | -     | Machine 計時器中斷 pending |
| 6     | RES0  | RO     | 0     | 保留 |
| 5     | STIP  | RW     | -     | Supervisor 計時器中斷 pending |
| 4     | RES0  | RO     | 0     | 保留 |
| 3     | MSIP  | RO     | -     | Machine 軟體中斷 pending |
| 2     | RES0  | RO     | 0     | 保留 |
| 1     | SSIP  | RW     | -     | Supervisor 軟體中斷 pending |
| 0     | RES0  | RO     | 0     | 保留 |

## mscratch
- Offset: 0x024
- Reset: -
- Description: Machine 暫存用暫存器（trap handler 交換空間）

| Bits | Field   | Access | Reset | Description |
|------|---------|--------|-------|-------------|
| 31:0 | Scratch | RW     | -     | 軟體自由使用 |

## mepc
- Offset: 0x028
- Reset: -
- Description: 發生例外／中斷時的 PC（回返位址）

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| 31:0 | EPC   | RW     | -     | 例外發生點的指令位址 |

## mcause
- Offset: 0x02C
- Reset: -
- Description: Trap 原因（最重要的除錯線索：先看 Interrupt 再看 Code）

| Bits | Field     | Access | Reset | Description |
|------|-----------|--------|-------|-------------|
| 31   | Interrupt | RW     | -     | trap 類型 |
| 30:0 | Code      | RW     | -     | 原因編號（下列意義以 Interrupt=0 例外為準；Interrupt=1 時：3=軟體中斷、7=計時器中斷、11=外部中斷） |

### Enum: Interrupt
- 0: 例外（exception）
- 1: 中斷（interrupt）

### Enum: Code
- 0: 指令位址未對齊
- 1: 指令存取 fault
- 2: 非法指令
- 3: Breakpoint（EBREAK）
- 4: 載入位址未對齊
- 5: 載入存取 fault
- 6: 儲存位址未對齊
- 7: 儲存存取 fault
- 8: U-mode 的 ECALL
- 9: S-mode 的 ECALL
- 11: M-mode 的 ECALL
- 12: 指令 page fault
- 13: 載入 page fault
- 15: 儲存 page fault

## mtval
- Offset: 0x030
- Reset: -
- Description: Trap 附帶資訊（fault 位址或造成例外的指令編碼）

| Bits | Field | Access | Reset | Description |
|------|-------|--------|-------|-------------|
| 31:0 | Value | RW     | -     | 依 mcause 而異：位址類例外為 fault 位址；非法指令為指令編碼 |
