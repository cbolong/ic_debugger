"""快速反查（lookup_register）的窮舉驗證。

兩條鎖死的設計：
1. 解碼結果必須與 bin 模式**完全同源**（同一個 _register_dict 路徑）——
   用 deep equality 對照 build_payload 的輸出，一個 key 都不准差。
2. 解析失敗一律回中文錯誤（帶建議），絕不丟例外、絕不默默截斷。
"""

import pytest

from core.analyzer import build_payload, fmt_hex, lookup_register
from core.bin_parser import BinFile
from core.spec_loader import load_spec_file, parse_spec_text

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

SPEC = """\
# CPU: T
## CTRL
- Offset: 0x0
- Reset: 0x10

| Bits | Field | Reset | Description |
|---|---|---|---|
| 31:8 | RES0 | 0 | 保留 |
| 7:4 | MODE | 0b0001 | 模式 |
| 3:0 | RES0 | 0 | 保留 |

### Enum: MODE
- 0b0001: 正常
- 0b0010: 省電

## STAT
- Offset: 0x4

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


def spec():
    s = parse_spec_text(SPEC, "t")
    assert s.warnings == []
    return s


# ── 解析軸窮舉：名稱／offset 的每一種解析路徑 ────────────────────────────

RESOLVE_OK = [
    # (query, 期望暫存器, 是否應有 note)
    ("CTRL", "CTRL", False),
    ("ctrl", "CTRL", False),        # 大小寫不拘（設計如此）
    (" CTRL ", "CTRL", False),      # 前後空白
    ("0x0", "CTRL", False),
    ("0", "CTRL", False),           # 十進位 offset
    ("0x4", "STAT", False),
    ("4", "STAT", False),
    ("0b100", "STAT", False),       # 二進位 offset
    ("0x8", "WIDE", False),
    ("0x2", "CTRL", True),          # 落在 32-bit 暫存器中間 → 整顆解碼＋note
    ("0xC", "WIDE", True),          # 64-bit 的高半段 → 整顆解碼＋note
    ("0xF", "WIDE", True),
]


def test_resolution_paths_exhaustive():
    s = spec()
    for q, want, has_note in RESOLVE_OK:
        r = lookup_register(s, q, "0x0")
        assert r["ok"], (q, r)
        assert r["register"]["name"] == want, q
        assert (r["note"] is not None) == has_note, (q, r["note"])


RESOLVE_FAIL = [
    # (query, 錯誤需包含)
    ("NOPE", "找不到暫存器"),
    ("ST", "名稱相近：STAT"),        # 部分名稱 → 給建議（設計如此）
    ("0x10", "涵蓋 0x000–0x00F"),   # 超出 spec 範圍 → 講清楚涵蓋範圍
    ("0x100", "沒有定義"),
    ("", "請輸入"),
    ("   ", "請輸入"),
]


def test_resolution_failures_exhaustive():
    s = spec()
    for q, needle in RESOLVE_FAIL:
        r = lookup_register(s, q, "0x0")
        assert not r["ok"], q
        assert needle in r["error"], (q, r["error"])


def test_name_priority_over_offset_parse():
    """名稱優先於 offset 解讀（設計如此）：暫存器名剛好長得像數字時以名稱為準。"""
    s = parse_spec_text("# CPU: T\n## 15\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 31:0 | V |\n", "t")
    r = lookup_register(s, "15", "0x1")
    assert r["ok"] and r["register"]["name"] == "15" and r["note"] is None


def test_empty_spec():
    s = parse_spec_text("# CPU: T\n", "t")
    r = lookup_register(s, "0x0", "0x0")
    assert not r["ok"] and "沒有任何暫存器" in r["error"]


# ── 值驗證軸窮舉：每種寬度 × 邊界值 × 格式 ──────────────────────────────

def test_value_bounds_every_width():
    for width in (8, 16, 32, 64):
        s = parse_spec_text(
            f"# CPU: T\n## R\n- Offset: 0x0\n- Size: {width}\n\n| Bits | Field |\n|---|---|\n| {width - 1}:0 | V |\n",
            "t")
        maxv = (1 << width) - 1
        for v in (0, 1, maxv):
            r = lookup_register(s, "R", hex(v))
            assert r["ok"], (width, v)
            assert r["register"]["value_hex"] == fmt_hex(v, width)
        over = lookup_register(s, "R", hex(maxv + 1))
        assert not over["ok"] and f"{width}-bit" in over["error"]


VALUE_FORMS_SAME = ["0x45", "0X45", "69", "0b0100_0101", "0x0000_0045", "  0x45  "]
VALUE_INVALID = [
    ("xyz", "解析失敗"),
    ("", "解析失敗"),
    ("-", "解析失敗"),      # parse_int 視 '-' 為未知
    ("-5", "負數"),
    ("0x", "解析失敗"),
    ("12.5", "解析失敗"),
]


def test_value_formats_equivalent_and_invalid():
    s = spec()
    results = [lookup_register(s, "STAT", form) for form in VALUE_FORMS_SAME]
    assert all(r["ok"] for r in results)
    assert len({r["register"]["value_hex"] for r in results}) == 1  # 全部同一個值
    for raw, needle in VALUE_INVALID:
        r = lookup_register(s, "STAT", raw)
        assert not r["ok"] and needle in r["error"], (raw, r)


# ── 單一解碼來源：與 bin 模式 deep equality ──────────────────────────────

def test_lookup_identical_to_bin_path():
    """反查結果必須與「把同一個值放進 bin 再 build_payload」一個 key 都不差。"""
    s = spec()
    cases = [("CTRL", 0x22), ("STAT", 0x5A5A5A5A), ("WIDE", 0xDEADBEEF_CAFEBABE)]
    data = (0x22).to_bytes(4, "little") + (0x5A5A5A5A).to_bytes(4, "little") \
        + (0xDEADBEEF_CAFEBABE).to_bytes(8, "little")
    payload = build_payload(s, BinFile(path="x", name="x.bin", data=data))
    by_name = {r["name"]: r for r in payload["registers"]}
    for name, value in cases:
        looked = lookup_register(s, name, hex(value))
        assert looked["ok"]
        assert looked["register"] == by_name[name]  # deep equality


def test_lookup_r5_sample_case():
    """端到端：R5 spec 反查 SCTLR=0x00C7187D，須解出與範例 bin 相同的重點欄位。"""
    s = load_spec_file(ROOT / "specs" / "arm_cortex_r5.md")
    r = lookup_register(s, "SCTLR", "0x00C7187D")
    assert r["ok"]
    reg = r["register"]
    assert reg["value_hex"] == "0x00C7187D"
    m = next(row for row in reg["rows"] if row["name"] == "M")
    assert m["enum_label"] == "MPU 開啟" and m["differs"] is True
    # offset 反查同顆
    r2 = lookup_register(s, "0x010", "0x00C7187D")
    assert r2["ok"] and r2["register"] == reg


def test_duplicate_register_names_pick_first_by_offset():
    s = parse_spec_text(
        "# CPU: T\n## R\n- Offset: 0x4\n\n| Bits | Field |\n|---|---|\n| 31:0 | V |\n\n"
        "## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 31:0 | V |\n", "t")
    r = lookup_register(s, "R", "0x1")
    assert r["ok"] and r["register"]["offset_hex"] == "0x000"  # offset 排序後的第一個
