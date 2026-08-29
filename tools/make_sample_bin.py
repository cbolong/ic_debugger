"""產生 examples/sample_r5.bin — 對應 specs/arm/cortex_r5.md 的示範 dump。

情境設定成一個「有東西可看」的除錯現場：
- SCTLR 開了 MPU / I-cache / D-cache / 分支預測 / 背景區（多個欄位 ≠ reset）
- CPACR 把 FPU（cp10/cp11）設成完全存取
- CPSR 停在 Supervisor 模式、IRQ/FIQ 開啟
- DFSR 記錄了一筆「寫入時的對齊 fault」，DFAR 是未對齊位址
- MPU 選到區域 3：基底 0x20000000、大小 1MB、完全存取、可快取

值的順序必須與 spec 的 Offset 順序一致（改 spec 就要同步改這裡）。
用法：python tools/make_sample_bin.py（在 repo 根目錄執行）
"""

from pathlib import Path

WORDS = [
    # ── c0 識別群（值＝一顆典型 R5F 的樣貌，僅供示範）──────────────
    ("MIDR",        0x411FC152),  # r1p2
    ("CTR",         0x8003C003),  # ARMv7 格式、32-byte line
    ("TCMTR",       0x00010001),  # ATCM x1、BTCM x1
    ("MPUIR",       0x00000C00),  # 12 個 MPU 區域、unified
    ("MPIDR",       0x80000000),  # 多處理器格式、核心 0
    ("REVIDR",      0x411FC152),  # 讀值＝MIDR ⇒ 此顆未實作 REVIDR
    ("ID_PFR0",     0x00000131),  # ARM+Thumb2、Jazelle trivial
    ("ID_PFR1",     0x00000001),  # 標準程式設計模型
    ("ID_DFR0",     0x00010400),  # v7 Debug（CP14＋記憶體映射）
    ("ID_AFR0",     0x00000000),
    ("ID_MMFR0",    0x00210030),  # AuxReg=2、TCM=impl-defined、PMSAv7
    ("ID_MMFR1",    0x00000000),
    ("ID_MMFR2",    0x01200000),  # WFI 停頓、CP15 barrier
    ("ID_MMFR3",    0x00000211),  # set/way＋MVA 維護
    ("ID_ISAR0",    0x02101111),  # r1p2 推導值（Table 4-15：r1p0 起 ARM+Thumb SDIV/UDIV；Table 4-2 印 0x01101111，TRM 內部衝突見 SPEC_REVIEW_LOG）
    ("ID_ISAR1",    0x13112111),
    ("ID_ISAR2",    0x21232141),  # r1p2 推導值（Table 4-17：r1p0 起加 PLDW ⇒ MemHint=0x4；Table 4-2 印 0x21232131，TRM 內部衝突見 SPEC_REVIEW_LOG）
    ("ID_ISAR3",    0x01112131),
    ("ID_ISAR4",    0x00010142),
    ("ID_ISAR5",    0x00000000),
    ("CCSIDR",      0xF00FE019),  # WB/WT/RA/WA、4-way 16KB
    ("CLIDR",       0x09200003),  # L1 分離 I/D、LoC=1
    ("AIDR",        0x00000000),
    ("CSSELR",      0x00000000),  # 選 L1 D-cache
    # ── c1 控制群 ───────────────────────────────────────────────────
    ("SCTLR",       0x00C7187D),  # M/C/I/Z/BR=1 + RES1 位元
    ("ACTLR",       0x00000000),
    ("CPACR",       0x00F00000),  # cp10/cp11 完全存取
    # ── c5/c6 故障群 ────────────────────────────────────────────────
    ("DFSR",        0x00000801),  # WnR=1（寫入）、FS=0b00001（對齊 fault）
    ("IFSR",        0x00000000),
    ("ADFSR",       0x00000000),
    ("AIFSR",       0x00000000),
    ("DFAR",        0x20000F02),  # 未對齊的 fault 位址
    ("IFAR",        0x00000000),
    # ── MPU 區域群 ──────────────────────────────────────────────────
    ("RGNR",        0x00000003),  # 目前選取 MPU 區域 3
    ("DRBAR",       0x20000000),  # 區域基底 0x20000000
    ("DRSR",        0x00000027),  # RSize=0b10011（1MB）、En=1
    ("DRACR",       0x0000030B),  # AP=0b011 完全存取、TEX=0b001、C=1、B=1
    # ── PMU 群 ──────────────────────────────────────────────────────
    ("PMCR",        0x41151800),  # IMP=0x41、IDCODE=0x15、N=3
    ("PMCNTENSET",  0x80000001),  # PMCCNTR＋counter0 啟用
    ("PMCNTENCLR",  0x80000001),
    ("PMOVSR",      0x00000000),
    ("PMSELR",      0x00000000),
    ("PMCEID0",     0x0F7FFFFF),
    ("PMCEID1",     0x00000000),
    ("PMCCNTR",     0x12345678),
    ("PMXEVTYPER",  0x00000008),  # 事件 0x08：指令執行
    ("PMXEVCNTR",   0x00000A5A),
    ("PMUSERENR",   0x00000000),
    ("PMINTENSET",  0x00000000),
    ("PMINTENCLR",  0x00000000),
    # ── TCM 區域（R5 實作層）────────────────────────────────────────
    ("ATCMRR",      0x00000019),  # Base=0x0、En=1
    ("BTCMRR",      0x00080019),  # Base=0x00080000、En=1
    # ── c13 context / thread ────────────────────────────────────────
    ("CONTEXTIDR",  0x00000042),
    ("TPIDRURW",    0x00000000),
    ("TPIDRURO",    0x00000000),
    ("TPIDRPRW",    0x8001C000),  # OS per-CPU 結構指標
    # ── 核心狀態＋FPU ───────────────────────────────────────────────
    ("CPSR",        0x40000113),  # Z=1、A 遮罩、Supervisor、IRQ/FIQ 開啟
    ("FPSID",       0x41023153),  # DDI 0460D Table 11-7 審查轉錄值（r1p2 R5F）——非親驗矽讀值
    ("FPSCR",       0x00000010),  # IXC=1（曾發生 inexact）
    ("FPEXC",       0x40000000),  # EN=1
    ("MVFR0",       0x10110221),  # 單/倍精度、VDIV/VSQRT（審查轉錄的 R5F 典型值，僅示範）
    ("MVFR1",       0x00000011),  # 支援 NaN 傳遞與完整 denorm（示範值）
]


def main() -> None:
    out = Path(__file__).resolve().parent.parent / "examples" / "sample_r5.bin"
    out.parent.mkdir(parents=True, exist_ok=True)
    data = b"".join(v.to_bytes(4, "little") for _, v in WORDS)
    out.write_bytes(data)
    print(f"寫出 {out}（{len(data)} bytes）")
    for i, (name, v) in enumerate(WORDS):
        print(f"  0x{i * 4:03X}  {name:8s} 0x{v:08X}")


if __name__ == "__main__":
    main()
