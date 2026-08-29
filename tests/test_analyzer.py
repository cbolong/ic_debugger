"""analyzer / bin_parser 的解碼正確性測試。"""

from pathlib import Path

import pytest

from core.analyzer import build_payload, extract, fmt_bin, fmt_hex
from core.bin_parser import BinError, BinFile, load_bin, word_at
from core.report import render_markdown
from core.spec_loader import load_spec_file, parse_spec_text

ROOT = Path(__file__).resolve().parent.parent


# ── 格式化 ──────────────────────────────────────────────────────────────

def test_fmt_hex():
    assert fmt_hex(0x45, 8) == "0x45"
    assert fmt_hex(0x1, 4) == "0x1"
    assert fmt_hex(0x00450078, 32) == "0x00450078"
    assert fmt_hex(0x30D00980, 64) == "0x00000000_30D00980"
    assert fmt_hex(0xDEADBEEFCAFEBABE, 64) == "0xDEADBEEF_CAFEBABE"


def test_fmt_bin():
    assert fmt_bin(0b01, 2) == "0b01"
    assert fmt_bin(0x45, 8) == "0b0100_0101"
    assert fmt_bin(0b101, 5) == "0b0_0101"


def test_extract():
    assert extract(0x411FC152, 31, 24) == 0x41
    assert extract(0x411FC152, 15, 4) == 0xC15
    assert extract(0x411FC152, 3, 0) == 2
    assert extract(0b1000, 3, 3) == 1


# ── bin_parser ──────────────────────────────────────────────────────────

def test_word_at_little_endian():
    data = bytes([0x52, 0xC1, 0x1F, 0x41, 0xAA, 0xBB])
    assert word_at(data, 0, 32) == 0x411FC152
    assert word_at(data, 4, 32) is None  # 只剩 2 bytes，不足一個 word
    assert word_at(data, 0, 16) == 0xC152
    assert word_at(data, 8, 32) is None


def test_word_at_64bit():
    data = (0xDEADBEEFCAFEBABE).to_bytes(8, "little")
    assert word_at(data, 0, 64) == 0xDEADBEEFCAFEBABE


def test_load_bin_errors(tmp_path):
    empty = tmp_path / "empty.bin"
    empty.write_bytes(b"")
    with pytest.raises(BinError):
        load_bin(empty)
    with pytest.raises(BinError):
        load_bin(tmp_path / "not_exist.bin")


# ── 解碼 payload ────────────────────────────────────────────────────────

SPEC_TEXT = """\
# CPU: Demo
# Width: 32

## CTRL
- Offset: 0x0
- Reset: 0x0000_0010
- Description: 控制

| Bits | Field | Access | Reset | Description |
|---|---|---|---|---|
| 31:8 | RES0 | RO | 0 | 保留 |
| 7:4 | MODE | RW | 0b0001 | 模式 |
| 1 | EN | RW | 0 | 致能 |

### Enum: MODE
- 0b0001: 正常
- 0b0010: 省電

### Enum: EN
- 0: 關
- 1: 開

## STAT
- Offset: 0x4
- Description: 狀態（無 reset）

| Bits | Field |
|---|---|
| 31:0 | V |

## WIDE
- Offset: 0x8
- Size: 64
- Reset: 0x0

| Bits | Field |
|---|---|
| 63:0 | V |
"""


def _demo_spec():
    spec = parse_spec_text(SPEC_TEXT, "demo")
    assert spec.warnings == []
    return spec


def test_payload_decode_and_differs():
    spec = _demo_spec()
    #        CTRL=0x22（MODE=0b0010、EN=1）  STAT=0x5A5A5A5A  WIDE=0x1_00000000
    data = (0x22).to_bytes(4, "little") + (0x5A5A5A5A).to_bytes(4, "little") \
        + (0x1_00000000).to_bytes(8, "little")
    payload = build_payload(spec, BinFile(path="x", name="x.bin", data=data))

    ctrl, stat, wide = payload["registers"]
    assert ctrl["value_hex"] == "0x00000022"
    assert ctrl["differs"] is True
    mode = next(r for r in ctrl["rows"] if r["name"] == "MODE")
    assert mode["value_bin"] == "0b0010"
    assert mode["enum_label"] == "省電"
    assert mode["differs"] is True
    en = next(r for r in ctrl["rows"] if r["name"] == "EN")
    assert en["enum_label"] == "開" and en["differs"] is True
    res = next(r for r in ctrl["rows"] if r["name"] == "RES0")
    assert res["differs"] is False  # 從暫存器 reset 推導出欄位 reset=0

    # bit 0、bit 3:2 沒被欄位表涵蓋 → 未定義列
    undef_bits = [r["bits"] for r in ctrl["rows"] if r["kind"] == "undef"]
    assert undef_bits == ["3:2", "0"]

    assert stat["differs"] is None  # 無 reset 可比
    assert wide["value_hex"] == "0x00000001_00000000"
    assert wide["differs"] is True

    st = payload["stats"]
    assert st == {
        "total": 3, "covered": 3, "not_covered": 0, "differs": 2,
        "spec_span_bytes": 16, "bin_size": 16,
    }


def test_payload_short_bin_marks_uncovered():
    spec = _demo_spec()
    data = (0x10).to_bytes(4, "little") + b"\x5A\x5A"  # STAT 只剩 2 bytes
    payload = build_payload(spec, BinFile(path="x", name="x.bin", data=data))
    ctrl, stat, wide = payload["registers"]
    assert ctrl["covered"] and ctrl["differs"] is False
    assert not stat["covered"] and stat["partial"]  # 截斷
    assert not wide["covered"] and not wide["partial"]
    assert payload["hexdump"]["note"] is not None
    assert payload["stats"]["covered"] == 1


def test_payload_without_bin_is_spec_browser():
    spec = _demo_spec()
    payload = build_payload(spec, None)
    assert payload["bin"] is None and payload["hexdump"] is None
    ctrl = payload["registers"][0]
    assert ctrl["value_hex"] is None
    mode = next(r for r in ctrl["rows"] if r["name"] == "MODE")
    assert mode["reset_hex"] == "0x1" and mode["enum_label"] is None
    assert len(mode["enum"]) == 2


def test_hexdump_annotation():
    spec = _demo_spec()
    data = bytes(16) + b"\xAB\xCD"  # 多 2 bytes 尾巴
    payload = build_payload(spec, BinFile(path="x", name="x.bin", data=data))
    rows = payload["hexdump"]["rows"]
    words = rows[0]["words"]
    assert words[0]["reg"] == "CTRL" and words[1]["reg"] == "STAT"
    assert words[2]["reg"] == "WIDE [31:0]" and words[3]["reg"] == "WIDE [63:32]"
    tail = rows[1]["words"][0]
    assert tail.get("partial") and tail["hex"] == "AB CD"
    assert "多出" in payload["hexdump"]["note"]


# ── 範例 bin × 範例 spec 整合 ────────────────────────────────────────────

def test_sample_bin_against_r5_spec():
    spec = load_spec_file(ROOT / "specs" / "arm" / "cortex_r5.md")
    binf = load_bin(ROOT / "examples" / "sample_r5.bin")
    payload = build_payload(spec, binf)
    st = payload["stats"]
    assert st["total"] == 62 and st["covered"] == 62
    assert st["bin_size"] == st["spec_span_bytes"] == 248

    regs = {r["name"]: r for r in payload["registers"]}
    assert regs["MIDR"]["differs"] is False
    sctlr = regs["SCTLR"]
    assert sctlr["value_hex"] == "0x00C7187D"
    m = next(r for r in sctlr["rows"] if r["name"] == "M")
    assert m["enum_label"] == "MPU 開啟" and m["differs"] is True
    dfsr = regs["DFSR"]
    fs = next(r for r in dfsr["rows"] if r["name"] == "FS[3:0]")
    assert "對齊故障" in fs["enum_label"]  # FS[4]=0 讀法（官方 Table B5-8）
    wnr = next(r for r in dfsr["rows"] if r["name"] == "WnR")
    assert wnr["enum_label"] == "由寫入指令造成"  # 官方 WnR 用語
    # SCTLR 全 bit 涵蓋 → 不該有未定義列
    assert all(r["kind"] == "field" for r in sctlr["rows"])


# ── 報告輸出 ────────────────────────────────────────────────────────────

def test_report_markdown():
    spec = _demo_spec()
    data = (0x22).to_bytes(4, "little") + bytes(12)
    payload = build_payload(spec, BinFile(path="x", name="demo.bin", data=data))
    md = render_markdown(payload)
    assert "# Register 分析報告" in md
    assert "## CTRL" in md and "0x00000022" in md
    assert "省電" in md
    only = render_markdown(payload, only_differs=True)
    assert "## CTRL" in only and "## STAT" not in only


def test_report_escapes_pipe_in_enum_label():
    """enum 意義文字可以含「|」；進 Markdown 表格必須跳脫，否則表格整個歪掉。"""
    text = ("# CPU: T\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 1:0 | M |\n\n"
            "### Enum: M\n- 0: 甲|乙 模式\n")
    spec = parse_spec_text(text, "t")
    payload = build_payload(spec, BinFile(path="x", name="x.bin", data=bytes(4)))
    md = render_markdown(payload)
    assert "甲\\|乙 模式" in md
    assert "甲|乙" not in md.replace("甲\\|乙", "")


def test_report_no_bin_and_no_diff_wording():
    spec = _demo_spec()
    browse = render_markdown(build_payload(spec, None))
    assert "未載入" in browse and "## CTRL" in browse
    # 全部等於 reset：only_differs 報告只剩表頭，不出現任何暫存器章節
    data = (0x10).to_bytes(4, "little") + bytes(12)
    only = render_markdown(build_payload(spec, BinFile(path="x", name="x.bin", data=data)),
                           only_differs=True)
    assert "## CTRL" not in only and "只列出與 Reset 不同" in only
