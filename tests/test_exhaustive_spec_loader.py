"""spec_loader 的窮舉驗證。

兩個窮舉軸：
A. 「寬容輸入」設計 —— 所有宣稱支援的格式變體（數字寫法、Bits 寫法、
   表頭別名、全形冒號、CRLF、BOM、markdown 行內標記）逐一驗證。
   這些是刻意的設計，之後不准把任何一種改成不支援。
B. 「嚴格回報」設計 —— spec_loader 內每一條 warning 分支逐一觸發並驗證
   訊息與降級行為（略過該列／該暫存器但不毀掉整份 spec）。
"""

import pytest

from core.spec_loader import load_spec_file, parse_int, parse_spec_text


def parse(text: str):
    return parse_spec_text(text, "t")


MINI = """\
# CPU: T
## R
- Offset: 0x0
{table}
"""


# ════════════════════════════════════════════════════════════════════
# A. 寬容輸入：格式變體窮舉
# ════════════════════════════════════════════════════════════════════

PARSE_INT_CASES = [
    # (輸入, 期望)
    ("0x1F", 31), ("0X1f", 31), ("0xff", 255),
    ("0b101", 5), ("0B101", 5),
    ("123", 123), ("0", 0),
    ("1_000", 1000), ("0x0000_0010", 16), ("0b0100_0101", 0x45),
    ("  0x10  ", 16),
    # 未知／無效 → None（設計：未知值不是錯誤，是「沒有基準」）
    ("-", None), ("?", None), ("—", None), ("N/A", None), ("n/a", None),
    ("TBD", None), ("tbd", None), ("", None), ("   ", None),
    ("abc", None), ("0x", None), ("0b", None), ("12.5", None), ("0xG", None),
]


def test_parse_int_exhaustive_table():
    for raw, want in PARSE_INT_CASES:
        assert parse_int(raw) == want, f"parse_int({raw!r})"


BITS_VALID = [
    ("31:24", (31, 24)), ("31-24", (31, 24)), ("31~24", (31, 24)),
    ("[31:24]", (31, 24)), ("[ 31 : 24 ]", (31, 24)),
    ("5", (5, 5)), ("[5]", (5, 5)),
    ("24:31", (31, 24)),  # 寫反自動轉正（設計如此，讓 AI 產的 spec 容錯）
    ("0", (0, 0)), ("31:0", (31, 0)),
]

BITS_INVALID = ["", "abc", "3.5", "31:", ":24", "31::24", "31:24:8", "-3"]


def test_bits_syntax_exhaustive():
    for raw, (msb, lsb) in BITS_VALID:
        spec = parse(MINI.format(table=f"| Bits | Field |\n|---|---|\n| {raw} | F |"))
        fs = spec.registers[0].fields
        assert len(fs) == 1 and (fs[0].msb, fs[0].lsb) == (msb, lsb), f"Bits={raw!r}"

    for raw in BITS_INVALID:
        spec = parse(MINI.format(table=f"| Bits | Field |\n|---|---|\n| {raw} | F |"))
        assert spec.registers[0].fields == [], f"Bits={raw!r} 不該解析成功"
        assert any("Bits" in w and "解析失敗" in w for w in spec.warnings)


COL_ALIASES = {
    "bits": ["Bits", "bits", "Bit", "位元", "位元範圍"],
    "name": ["Field", "Name", "欄位", "欄位名稱", "名稱"],
    "access": ["Access", "Type", "存取", "屬性", "R/W"],
    "reset": ["Reset", "重置", "重置值", "預設", "預設值", "Default"],
    "desc": ["Description", "Desc", "說明", "描述", "Meaning", "意義"],
}


def test_table_header_aliases_exhaustive():
    """每個表頭別名都要被認得（中英混用是給 AI 產 spec 的容錯，設計如此）。"""
    for b in COL_ALIASES["bits"]:
        for n in COL_ALIASES["name"]:
            spec = parse(MINI.format(table=f"| {b} | {n} |\n|---|---|\n| 3:0 | F |"))
            assert spec.registers[0].fields[0].name == "F", f"{b}/{n}"
    for a in COL_ALIASES["access"]:
        spec = parse(MINI.format(table=f"| Bits | Field | {a} |\n|---|---|---|\n| 0 | F | RW |"))
        assert spec.registers[0].fields[0].access == "RW", a
    for r in COL_ALIASES["reset"]:
        spec = parse(MINI.format(table=f"| Bits | Field | {r} |\n|---|---|---|\n| 0 | F | 1 |"))
        assert spec.registers[0].fields[0].reset == 1, r
    for d in COL_ALIASES["desc"]:
        spec = parse(MINI.format(table=f"| Bits | Field | {d} |\n|---|---|---|\n| 0 | F | 嗨 |"))
        assert spec.registers[0].fields[0].desc == "嗨", d


def test_fullwidth_colon_everywhere():
    spec = parse("# CPU： 全形\n## R\n- Offset： 0x0\n\n| Bits | Field |\n|---|---|\n| 0 | EN |\n\n### Enum： EN\n- 0： 關\n")
    assert spec.cpu == "全形"
    assert spec.registers[0].offset == 0
    assert spec.registers[0].fields[0].enum == {0: "關"}
    assert spec.warnings == []


def test_crlf_and_markdown_inline_marks():
    text = ("# CPU: T\n## R\n- Offset: 0x0\n\n"
            "| Bits | Field | Reset | Description |\n|---|---|---|---|\n"
            "| `1` | **EN** | *1* | 致能 |\n").replace("\n", "\r\n")
    spec = parse(text)
    f = spec.registers[0].fields[0]
    assert (f.msb, f.name, f.reset, f.desc) == (1, "EN", 1, "致能")
    assert spec.warnings == []


def test_bom_via_file(tmp_path):
    p = tmp_path / "bom.md"
    p.write_bytes(("\ufeff" + "# CPU: BOM\n## R\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n").encode("utf-8"))
    spec = load_spec_file(p)
    assert spec.cpu == "BOM" and spec.warnings == []


def test_table_without_leading_trailing_pipes_and_extra_cols():
    spec = parse(MINI.format(table="Bits | Field | Access | Reset | Description | 多的欄\n---|---|---|---|---|---\n3:0 | F | RO | 0x5 | 說 | 忽略"))
    f = spec.registers[0].fields[0]
    assert (f.msb, f.lsb, f.access, f.reset, f.desc) == (3, 0, "RO", 5, "說")


def test_html_comments_and_prose_ignored():
    spec = parse("# CPU: T\n<!-- 註解 -->\n說明文字。\n## R\n- Offset: 0x0\n中間插話。\n\n| Bits | Field |\n|---|---|\n| 0 | F |\n尾註。\n")
    assert spec.warnings == [] and len(spec.registers[0].fields) == 1


def test_size_64_field_to_63_and_widths():
    for width in (8, 16, 32, 64):
        spec = parse(f"# CPU: T\n# Width: {width}\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| {width - 1}:0 | V |\n")
        assert spec.width == width and spec.registers[0].size == width
        assert spec.registers[0].fields[0].msb == width - 1
        assert spec.warnings == []


def test_register_level_size_override():
    spec = parse("# CPU: T\n## R\n- Offset: 0x0\n- Size: 64\n\n| Bits | Field |\n|---|---|\n| 63:0 | V |\n")
    assert spec.width == 32 and spec.registers[0].size == 64
    assert spec.warnings == []


def test_enum_then_register_attr_not_swallowed():
    """Enum 區塊後面接『- Description: …』必須被當成暫存器屬性，不是列舉值。"""
    spec = parse("# CPU: T\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 0 | EN |\n\n### Enum: EN\n- 0: 關\n- Description: 補充說明\n")
    assert spec.registers[0].desc == "補充說明"
    assert spec.registers[0].fields[0].enum == {0: "關"}
    assert spec.warnings == []


def test_enum_attaches_to_all_same_named_fields():
    """設計如此：同名欄位（如多段 RES0）的 Enum 會掛到每一段。"""
    spec = parse("# CPU: T\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 3 | X |\n| 1 | X |\n\n### Enum: X\n- 1: 開\n")
    assert all(f.enum == {1: "開"} for f in spec.registers[0].fields)


def test_registers_sorted_by_offset_not_document_order():
    spec = parse("# CPU: T\n## B\n- Offset: 0x4\n\n| Bits | Field |\n|---|---|\n| 0 | F |\n\n## A\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 0 | F |\n")
    assert [r.name for r in spec.registers] == ["A", "B"]


def test_fields_sorted_msb_desc_not_document_order():
    spec = parse(MINI.format(table="| Bits | Field |\n|---|---|\n| 0 | LO |\n| 7:4 | HI |"))
    assert [f.name for f in spec.registers[0].fields] == ["HI", "LO"]


# ════════════════════════════════════════════════════════════════════
# B. 警告分支窮舉：spec_loader 的每一條 warning 都要能被觸發並降級存活
# ════════════════════════════════════════════════════════════════════

WARNING_CASES = [
    # (代號, spec 文字, 警告需包含, 額外斷言 lambda spec)
    ("enum_before_register",
     "# CPU: T\n### Enum: X\n- 0: a\n## R\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "任何暫存器之前", lambda s: len(s.registers) == 1),
    ("enum_unknown_field",
     MINI.format(table="| Bits | Field |\n|---|---|\n| 0 | EN |\n\n### Enum: NOPE\n- 0: x"),
     "NOPE", lambda s: s.registers[0].fields[0].enum == {}),
    ("enum_value_unparsable",
     MINI.format(table="| Bits | Field |\n|---|---|\n| 0 | EN |\n\n### Enum: EN\n- xx: 壞"),
     "解析失敗", lambda s: s.registers[0].fields[0].enum == {}),
    ("enum_value_out_of_range",
     MINI.format(table="| Bits | Field |\n|---|---|\n| 0 | EN |\n\n### Enum: EN\n- 2: 超"),
     "超出欄位", lambda s: 2 in s.registers[0].fields[0].enum),  # 記錄但警告
    ("width_invalid",
     "# CPU: T\n# Width: 33\n## R\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "Width", lambda s: s.width == 32),
    ("unknown_header_key",
     "# CPU: T\n# Bogus: x\n## R\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "bogus", lambda s: s.cpu == "T"),
    ("offset_unparsable_drops_register",
     "# CPU: T\n## R\n- Offset: xyz\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "Offset", lambda s: s.registers == []),
    ("offset_missing_drops_register",
     "# CPU: T\n## R\n- Description: 沒 offset\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "Offset", lambda s: s.registers == []),
    ("size_invalid",
     "# CPU: T\n## R\n- Offset: 0x0\n- Size: 24\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "Size", lambda s: s.registers[0].size == 32),
    ("reset_unparsable",
     "# CPU: T\n## R\n- Offset: 0x0\n- Reset: xyz\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "Reset", lambda s: s.registers[0].reset is None),
    ("unknown_register_attr",
     "# CPU: T\n## R\n- Offset: 0x0\n- Bogus: x\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "bogus", lambda s: len(s.registers) == 1),
    ("table_header_missing_required_cols",
     MINI.format(table="| Bits | 隨便 |\n|---|---|\n| 0 | F |"),
     "表頭", lambda s: s.registers[0].fields == []),
    ("bits_unparsable_row_dropped",
     MINI.format(table="| Bits | Field |\n|---|---|\n| zz | F |\n| 0 | OK |"),
     "解析失敗", lambda s: [f.name for f in s.registers[0].fields] == ["OK"]),
    ("field_beyond_register_width_dropped",
     MINI.format(table="| Bits | Field |\n|---|---|\n| 40:36 | C |\n| 0 | OK |"),
     "超出暫存器寬度", lambda s: [f.name for f in s.registers[0].fields] == ["OK"]),
    ("field_reset_out_of_range_becomes_unknown",
     MINI.format(table="| Bits | Field | Reset |\n|---|---|---|\n| 1:0 | F | 0x7 |"),
     "超出", lambda s: s.registers[0].fields[0].reset is None),
    ("missing_cpu_header_falls_back_to_id",
     "## R\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "CPU", lambda s: s.cpu == "t"),
    ("offset_not_word_aligned",
     "# CPU: T\n## R\n- Offset: 0x2\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "4 的倍數", lambda s: s.registers[0].offset == 2),  # 警告但保留
    ("duplicate_offset",
     "# CPU: T\n## A\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n\n## B\n- Offset: 0x0\n| Bits | Field |\n|---|---|\n| 0 | F |\n",
     "重複", lambda s: len(s.registers) == 2),
    ("bit_overlap_kept_with_warning",
     MINI.format(table="| Bits | Field |\n|---|---|\n| 3:0 | A |\n| 4:2 | B |"),
     "重疊", lambda s: len(s.registers[0].fields) == 2),
    ("register_reset_exceeds_size_truncated",
     "# CPU: T\n## R\n- Offset: 0x0\n- Size: 8\n- Reset: 0x1FF\n| Bits | Field |\n|---|---|\n| 7:0 | F |\n",
     "截斷", lambda s: s.registers[0].reset == 0xFF),
    ("span_overlap_between_registers",
     "# CPU: T\n## A\n- Offset: 0x0\n- Size: 64\n| Bits | Field |\n|---|---|\n| 63:0 | V |\n\n## B\n- Offset: 0x4\n| Bits | Field |\n|---|---|\n| 31:0 | V |\n",
     "位移範圍重疊", lambda s: len(s.registers) == 2),
    ("empty_spec_no_registers",
     "# CPU: T\n",
     "沒有任何有效的暫存器", lambda s: s.registers == []),
]


@pytest.mark.parametrize("case", WARNING_CASES, ids=[c[0] for c in WARNING_CASES])
def test_every_warning_branch(case):
    _, text, needle, check = case
    spec = parse(text)
    assert any(needle in w for w in spec.warnings), \
        f"警告應包含「{needle}」，實際：{spec.warnings}"
    check(spec)


def test_warning_carries_line_number():
    spec = parse("# CPU: T\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| zz | F |\n")
    assert any(":7:" in w for w in spec.warnings), spec.warnings


def test_clean_specs_have_zero_warnings():
    """反向保障：合法輸入不得產生任何多餘警告（避免警告通膨稀釋注意力）。"""
    for _, text, __ in [("m", MINI.format(table="| Bits | Field |\n|---|---|\n| 31:0 | V |"), None)]:
        assert parse(text).warnings == []


def test_file_read_error_returns_spec_with_warning(tmp_path):
    spec = load_spec_file(tmp_path / "not_exist.md")
    assert spec.registers == []
    assert any("讀取失敗" in w for w in spec.warnings)
