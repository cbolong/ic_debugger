"""位元運算層的窮舉驗證。

這一層是全 app 的地基：extract／fmt_hex／fmt_bin 錯一個 bit，畫面上每個
數字都是錯的。所以不抽樣 —— 能窮舉的全部窮舉，並且用「與實作不同的演算法」
（bit 字串切片）當參考答案，避免實作與驗證犯同一個錯。
"""

import random

from core.analyzer import extract, fmt_bin, fmt_hex


def ref_extract(value: int, msb: int, lsb: int, size: int) -> int:
    """參考實作：走二進位字串切片（與 extract 的位移遮罩演算法獨立）。"""
    bits = f"{value:0{size}b}"
    return int(bits[size - 1 - msb: size - lsb], 2)


# ── extract：32-bit 全部 (msb, lsb) 組合 × 代表性測值 ────────────────────

def test_extract_all_ranges_32bit():
    patterns = [0x00000000, 0xFFFFFFFF, 0xA5A5A5A5, 0x5A5A5A5A, 0x80000001, 0x7FFFFFFE]
    checked = 0
    for msb in range(32):
        for lsb in range(msb + 1):
            for v in patterns:
                assert extract(v, msb, lsb) == ref_extract(v, msb, lsb, 32), \
                    f"extract(0x{v:08X}, {msb}, {lsb}) 不符"
            # 邊界值：只有 lsb／只有 msb 為 1
            assert extract(1 << lsb, msb, lsb) == 1
            assert extract(1 << msb, msb, lsb) == 1 << (msb - lsb)
            checked += 1
    assert checked == 528  # C(32,2)+32 = 32*33/2，確認真的全跑到


def test_extract_all_ranges_64bit_boundaries():
    # 64-bit 全 2080 組太多值就抽 pattern，但 (msb,lsb) 仍全窮舉
    patterns = [0, 2**64 - 1, 0xA5A5A5A5_5A5A5A5A, 1 << 63, (1 << 63) | 1]
    for msb in range(64):
        for lsb in range(msb + 1):
            for v in patterns:
                assert extract(v, msb, lsb) == ref_extract(v, msb, lsb, 64)


def test_extract_field_partition_reconstructs_value():
    """性質驗證：欄位若把暫存器切成不重疊的完整分割，抽出再組回必須等於原值。
    這保證 extract 沒有位移／遮罩的系統性偏差。"""
    rng = random.Random(20260822)
    for size in (32, 64):
        for _ in range(100):
            # 隨機切割 [0, size) 成若干欄位
            cuts = sorted(rng.sample(range(1, size), rng.randint(1, min(12, size - 1))))
            bounds = [0] + cuts + [size]
            fields = [(bounds[i + 1] - 1, bounds[i]) for i in range(len(bounds) - 1)]
            for _ in range(5):
                v = rng.getrandbits(size)
                recon = 0
                for msb, lsb in fields:
                    recon |= extract(v, msb, lsb) << lsb
                assert recon == v


# ── fmt_hex：寬度 1..64 全窮舉 × 邊界值，並驗可逆 ────────────────────────

def test_fmt_hex_all_widths_roundtrip():
    for bits in range(1, 65):
        maxv = (1 << bits) - 1
        for v in {0, 1, maxv, maxv - 1 if maxv > 0 else 0, maxv // 3}:
            s = fmt_hex(v, bits)
            assert s.startswith("0x")
            body = s[2:]
            digits = body.replace("_", "")
            # 固定寬度：ceil(bits/4) 位、全大寫、可逆
            assert len(digits) == (bits + 3) // 4, f"bits={bits} v={v} → {s}"
            assert digits == digits.upper()
            assert int(digits, 16) == v
            # 底線規則：只有超過 8 位（>32-bit）才有，且從右往左每 8 位一組
            if len(digits) <= 8:
                assert "_" not in body
            else:
                parts = body.split("_")
                assert all(len(p) == 8 for p in parts[1:])
                assert 1 <= len(parts[0]) <= 8


def test_fmt_hex_documented_examples():
    # 設計基準（VERIFICATION.md 引用的例子）：改壞會直接被抓
    assert fmt_hex(0x00450078, 32) == "0x00450078"
    assert fmt_hex(0x30D00980, 64) == "0x00000000_30D00980"
    assert fmt_hex(0xF, 4) == "0xF"
    assert fmt_hex(0, 1) == "0x0"
    assert fmt_hex(2**64 - 1, 64) == "0xFFFFFFFF_FFFFFFFF"


# ── fmt_bin：寬度 1..64 全窮舉 × 邊界值，並驗可逆 ────────────────────────

def test_fmt_bin_all_widths_roundtrip():
    for bits in range(1, 65):
        maxv = (1 << bits) - 1
        for v in {0, 1, maxv, maxv >> 1}:
            s = fmt_bin(v, bits)
            assert s.startswith("0b")
            digits = s[2:].replace("_", "")
            assert len(digits) == bits
            assert int(digits, 2) == v
            # 分組規則：由 LSB 往左每 4 位一組
            parts = s[2:].split("_")
            assert all(len(p) == 4 for p in parts[1:])
            assert 1 <= len(parts[0]) <= 4


def test_fmt_bin_documented_examples():
    assert fmt_bin(0b01, 2) == "0b01"
    assert fmt_bin(0x45, 8) == "0b0100_0101"
    assert fmt_bin(0b101, 5) == "0b0_0101"
    assert fmt_bin(0, 32) == "0b0000_0000_0000_0000_0000_0000_0000_0000"
