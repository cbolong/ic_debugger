"""產生 examples/sample_r5.bin — 對應 specs/arm_cortex_r5.md 的示範 dump。

情境設定成一個「有東西可看」的除錯現場：
- SCTLR 開了 MPU / I-cache / D-cache / 分支預測 / 背景區（多個欄位 ≠ reset）
- CPACR 把 FPU（cp10/cp11）設成完全存取
- DFSR 記錄了一筆「寫入時的對齊 fault」，DFAR 是未對齊位址
- 其餘維持 reset 或典型組態值

用法：python tools/make_sample_bin.py（在 repo 根目錄執行）
"""

from pathlib import Path

WORDS = [
    ("MIDR",   0x411FC152),  # r1p2，同 reset
    ("CTR",    0x8003C003),  # 同 reset
    ("MPIDR",  0xC0000000),  # 單處理器（M=1, U=1）
    ("MPUIR",  0x00000C00),  # 12 個 MPU region
    ("SCTLR",  0x00C7187D),  # M/C/I/Z/BR=1 + RES1 位元（[6:3],[16],[18],[22],[23]）
    ("CPACR",  0x00F00000),  # cp10/cp11 完全存取
    ("DFSR",   0x00000801),  # WnR=1（寫入）、FS=0b0001（對齊 fault）
    ("IFSR",   0x00000000),
    ("DFAR",   0x20000F02),  # 未對齊的 fault 位址
    ("IFAR",   0x00000000),
    ("ATCMRR", 0x00000019),  # Base=0x0、Size=32KB、EN=1
    ("BTCMRR", 0x00080019),  # Base=0x80000、Size=32KB、EN=1
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
