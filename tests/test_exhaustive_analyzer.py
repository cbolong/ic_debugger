"""analyzer 的窮舉驗證：解碼引擎的每個行為軸全面掃過。

核心手法：
- 「截斷全掃」：bin 長度從 0 掃到 spec 範圍 +2，每個長度都驗 covered／
  partial／hexdump note —— 邊界 off-by-one 無所遁形。
- 「真值表」：differs 的每一種已知/未知組合逐格驗證。
- 「暴力對照」：未定義位元用 set 補集重新算一次，跟實作比對。
"""

import random

from core.analyzer import _uncovered_ranges, build_payload, spec_detail
from core.bin_parser import BinFile, word_at
from core.spec_loader import Register, Field, load_spec_file, parse_spec_text

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def bf(data: bytes) -> BinFile:
    return BinFile(path="t", name="t.bin", data=data)


# ════════════════════════════════════════════════════════════════════
# word_at：小 buffer 內全 offset × 全 size 窮舉，與 int.from_bytes 對照
# ════════════════════════════════════════════════════════════════════

def test_word_at_exhaustive_small_buffer():
    data = bytes(range(1, 13))  # 12 bytes：01 02 … 0C
    for size in (8, 16, 32, 64):
        n = size // 8
        for off in range(-2, 16):
            got = word_at(data, off, size)
            if 0 <= off and off + n <= len(data):
                assert got == int.from_bytes(data[off:off + n], "little"), (off, size)
            else:
                assert got is None, (off, size)  # 不足／越界 → None，絕不丟例外


# ════════════════════════════════════════════════════════════════════
# 截斷全掃：spec 佔 16 bytes（32/64-bit 混合），bin 長度 0..18 全驗
# ════════════════════════════════════════════════════════════════════

SPEC_MIX = """\
# CPU: T
## A
- Offset: 0x0
- Reset: 0x0

| Bits | Field |
|---|---|
| 31:0 | V |

## B
- Offset: 0x4

| Bits | Field |
|---|---|
| 31:0 | V |

## W
- Offset: 0x8
- Size: 64
- Reset: 0x0

| Bits | Field |
|---|---|
| 63:0 | V |
"""


def test_truncation_sweep_every_length():
    spec = parse_spec_text(SPEC_MIX, "t")
    assert spec.warnings == [] and spec.span_bytes == 16
    full = bytes(range(0x10, 0x10 + 18))
    for n in range(0, 19):
        payload = build_payload(spec, bf(full[:n])) if n else None
        if payload is None:
            # 長度 0 的檔在 load_bin 就擋掉了；analyzer 這層不會遇到
            continue
        a, b, w = payload["registers"]
        assert a["covered"] == (n >= 4)
        assert a["partial"] == (0 < n < 4)
        assert b["covered"] == (n >= 8)
        assert b["partial"] == (4 < n < 8)
        assert w["covered"] == (n >= 16)
        assert w["partial"] == (8 < n < 16)
        st = payload["stats"]
        assert st["covered"] == sum(r["covered"] for r in payload["registers"])
        assert st["covered"] + st["not_covered"] == st["total"] == 3
        note = payload["hexdump"]["note"]
        if n < 16:
            assert note and "短" in note, n
        elif n == 16:
            assert note is None
        else:
            assert note and "多出" in note and f"{n - 16} bytes" in note, n
        # covered 的暫存器一定有值字串；沒 covered 的一定沒有
        for r in payload["registers"]:
            assert (r["value_hex"] is not None) == r["covered"]


# ════════════════════════════════════════════════════════════════════
# differs 真值表：暫存器層 × 欄位層的已知/未知組合
# ════════════════════════════════════════════════════════════════════

def _one_reg_payload(reg_reset: str, field_reset: str, value: int):
    text = (f"# CPU: T\n## R\n- Offset: 0x0\n- Reset: {reg_reset}\n\n"
            f"| Bits | Field | Reset |\n|---|---|---|\n| 3:0 | F | {field_reset} |\n")
    spec = parse_spec_text(text, "t")
    payload = build_payload(spec, bf(value.to_bytes(4, "little")))
    return payload["registers"][0]


def test_differs_truth_table():
    # (暫存器 Reset, 欄位 Reset, 匯入值, 期望 reg.differs, 期望 field.differs)
    cases = [
        # 兩層 reset 都有：欄位用表格值；暫存器用暫存器值
        ("0x5", "0x5", 0x5, False, False),
        ("0x5", "0x5", 0x6, True,  True),
        # 欄位 reset 省略 → 從暫存器 Reset 推導（設計：表格可以少抄）
        ("0x5", "-",   0x5, False, False),
        ("0x5", "-",   0x6, True,  True),
        # 暫存器 reset 未知、欄位有 → 暫存器層用「任一欄位 differs」判定
        ("-",   "0x5", 0x5, False, False),
        ("-",   "0x5", 0x6, True,  True),
        # 全都未知 → 無基準（None），不是 False！UI 顯示「無基準」
        ("-",   "-",   0x6, None,  None),
        # 欄位 reset 明寫且與暫存器 Reset 推導值不同 → 以明寫的為準（設計）
        ("0x0", "0x6", 0x6, True,  False),
    ]
    for reg_reset, field_reset, value, want_reg, want_field in cases:
        r = _one_reg_payload(reg_reset, field_reset, value)
        f = next(row for row in r["rows"] if row["name"] == "F")
        assert r["differs"] is want_reg, (reg_reset, field_reset, value, r["differs"])
        assert f["differs"] is want_field, (reg_reset, field_reset, value, f["differs"])


def test_differs_none_when_bin_absent_or_uncovered():
    spec = parse_spec_text(SPEC_MIX, "t")
    for r in build_payload(spec, None)["registers"]:
        assert r["differs"] is None and r["value_hex"] is None
    short = build_payload(spec, bf(bytes(4)))
    assert short["registers"][1]["differs"] is None  # 未涵蓋 → 無從比較


# ════════════════════════════════════════════════════════════════════
# 未定義位元：隨機欄位佈局 × 暴力對照 ＋ 「rows 必須完整分割」不變條件
# ════════════════════════════════════════════════════════════════════

def _random_layout(rng, size):
    fields, b = [], size - 1
    while b >= 0:
        w = rng.randint(1, min(9, b + 1))
        if rng.random() < 0.55:  # 55% 機率放欄位，其餘留成未定義洞
            fields.append(Field(msb=b, lsb=b - w + 1, name=f"F{b}"))
        b -= w
    return fields


def test_uncovered_ranges_vs_bruteforce_random_layouts():
    rng = random.Random(20260823)
    for size in (32, 64):
        for _ in range(150):
            reg = Register(name="R", offset=0, size=size, fields=_random_layout(rng, size))
            got = _uncovered_ranges(reg)
            covered = set()
            for f in reg.fields:
                covered.update(range(f.lsb, f.msb + 1))
            want_bits = set(range(size)) - covered
            got_bits = set()
            for msb, lsb in got:
                assert msb >= lsb
                got_bits.update(range(lsb, msb + 1))
            assert got_bits == want_bits
            # 各區段之間不得相鄰（相鄰就該合併成一段）
            edges = sorted(l for _, l in got) + sorted(m for m, _ in got)
            spans = sorted(got, key=lambda t: t[1])
            for (m1, l1), (m2, l2) in zip(spans, spans[1:]):
                assert l2 > m1 + 1


def test_rows_always_partition_register_exactly():
    """不變條件：payload 的 rows（欄位＋未定義）必須不重疊地覆蓋每一個 bit，
    並依 msb 由高到低排序 —— bit ruler 與欄位表都建立在這個保證上。"""
    rng = random.Random(7)
    for size in (32, 64):
        for _ in range(60):
            reg = Register(name="R", offset=0, size=size, fields=_random_layout(rng, size))
            spec_obj = parse_spec_text("# CPU: T\n", "t")
            spec_obj.registers = [reg]
            payload = build_payload(spec_obj, bf(bytes(size // 8)))
            rows = payload["registers"][0]["rows"]
            assert sum(r["msb"] - r["lsb"] + 1 for r in rows) == size
            assert [r["msb"] for r in rows] == sorted((r["msb"] for r in rows), reverse=True)
            seen = set()
            for r in rows:
                bits = set(range(r["lsb"], r["msb"] + 1))
                assert not (bits & seen)
                seen |= bits
            assert seen == set(range(size))


def test_nonzero_undef_flag():
    text = "# CPU: T\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 3:0 | F |\n"
    spec = parse_spec_text(text, "t")
    zero = build_payload(spec, bf((0x0000000F).to_bytes(4, "little")))
    assert zero["registers"][0]["nonzero_undef"] is False
    hot = build_payload(spec, bf((0x8000000F).to_bytes(4, "little")))
    assert hot["registers"][0]["nonzero_undef"] is True


# ════════════════════════════════════════════════════════════════════
# enum 呈現：全值域窮舉 current 標記與 label
# ════════════════════════════════════════════════════════════════════

def test_enum_current_marking_full_domain():
    text = ("# CPU: T\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 1:0 | M |\n\n"
            "### Enum: M\n- 0b00: 甲\n- 0b01: 乙\n- 0b10: 丙\n")  # 0b11 刻意缺
    spec = parse_spec_text(text, "t")
    labels = {0: "甲", 1: "乙", 2: "丙", 3: None}
    for v in range(4):
        payload = build_payload(spec, bf(v.to_bytes(4, "little")))
        row = payload["registers"][0]["rows"][-1]
        assert row["enum_label"] == labels[v]
        currents = [e["v"] for e in row["enum"] if e["current"]]
        if labels[v] is None:
            assert currents == []  # 值不在列舉表 → label None、無 current（設計）
        else:
            assert len(currents) == 1


# ════════════════════════════════════════════════════════════════════
# hexdump：32/64/位移空洞 混合佈局的逐 word 標註窮舉
# ════════════════════════════════════════════════════════════════════

def test_hexdump_annotation_with_gap_and_64bit():
    text = ("# CPU: T\n## A\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 31:0 | V |\n\n"
            "## W\n- Offset: 0x8\n- Size: 64\n\n| Bits | Field |\n|---|---|\n| 63:0 | V |\n")
    spec = parse_spec_text(text, "t")  # 0x4 是空洞
    payload = build_payload(spec, bf(bytes(16)))
    words = [w for row in payload["hexdump"]["rows"] for w in row["words"]]
    assert [w["reg"] for w in words] == ["A", None, "W [31:0]", "W [63:32]"]
    assert [w["offset_hex"] for w in words] == ["0x000", "0x004", "0x008", "0x00C"]


def test_hexdump_value_matches_le_word():
    data = (0x11223344).to_bytes(4, "little") + (0xAABBCCDD).to_bytes(4, "little")
    text = "# CPU: T\n## A\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 31:0 | V |\n"
    payload = build_payload(parse_spec_text(text, "t"), bf(data))
    words = payload["hexdump"]["rows"][0]["words"]
    assert words[0]["hex"] == "0x11223344"
    assert words[1]["hex"] == "0xAABBCCDD"


# ════════════════════════════════════════════════════════════════════
# spec_detail（Spec 全文檢視）
# ════════════════════════════════════════════════════════════════════

def test_spec_detail_builtin_raw_matches_file():
    path = ROOT / "specs" / "arm_cortex_r5.md"
    detail = spec_detail(load_spec_file(path))
    assert detail["summary"]["id"] == "arm_cortex_r5"
    assert detail["raw"] == path.read_text(encoding="utf-8-sig")  # 原文一字不差
    assert detail["raw_error"] is None
    assert len(detail["registers"]) == detail["summary"]["register_count"] == 12
    # 全文模式沒有 bin：不得出現任何值
    assert all(r["value_hex"] is None for r in detail["registers"])


def test_spec_detail_missing_file_degrades(tmp_path):
    p = tmp_path / "gone.md"
    p.write_text("# CPU: G\n## R\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n", encoding="utf-8")
    spec = load_spec_file(p, origin="external")
    p.unlink()  # 載入後檔案被刪走
    detail = spec_detail(spec)
    assert detail["raw"] is None and "無法讀取" in detail["raw_error"]
    assert detail["registers"]  # 解析內容仍在，功能降級不失效


def test_spec_detail_no_path():
    spec = parse_spec_text("# CPU: T\n## R\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n", "t")
    detail = spec_detail(spec)
    assert detail["raw"] is None and detail["raw_error"]
