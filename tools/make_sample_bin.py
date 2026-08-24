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
    ("MIDR",   0x411FC152),  # r1p2，同 reset
    ("CTR",    0x8003C003),  # 同 reset
    ("TCMTR",  0x00010001),  # ATCM x1、BTCM x1
    ("MPUIR",  0x00000C00),  # 12 個 MPU 區域
    ("MPIDR",  0x80000000),  # 多處理器格式、核心 0
    ("SCTLR",  0x00C7187D),  # M/C/I/Z/BR=1 + RES1 位元
    ("CPACR",  0x00F00000),  # cp10/cp11 完全存取
    ("CPSR",   0x40000113),  # Z=1、A 遮罩、Supervisor 模式、IRQ/FIQ 開啟
    ("DFSR",   0x00000801),  # WnR=1（寫入）、FS=0b00001（對齊 fault）
    ("IFSR",   0x00000000),
    ("DFAR",   0x20000F02),  # 未對齊的 fault 位址
    ("IFAR",   0x00000000),
    ("RGNR",   0x00000003),  # 目前選取 MPU 區域 3
    ("DRBAR",  0x20000000),  # 區域基底 0x20000000
    ("DRSR",   0x00000027),  # RSIZE=0b10011（1MB）、EN=1
    ("DRACR",  0x0000030B),  # AP=0b011 完全存取、TEX=0b001、C=1、B=1
    ("ATCMRR", 0x00000019),  # Base=0x0、Size=32KB、EN=1
    ("BTCMRR", 0x00080019),  # Base=0x00080000、Size=32KB、EN=1
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
