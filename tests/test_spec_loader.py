"""spec_loader 的行為測試：正常解析、寬容輸入、警告回報。"""

from pathlib import Path

from core.spec_loader import (is_spec_file, load_builtin_specs, load_spec_file,
                              parse_int, parse_spec_text)

SPECS_DIR = Path(__file__).resolve().parent.parent / "specs"


# ── 內建 spec 品質關卡：打包進 exe 的 spec 必須解析乾淨 ──────────────────

def test_builtin_specs_parse_clean():
    files = [p for p in sorted(SPECS_DIR.rglob("*.md")) if is_spec_file(p)]
    assert files, "specs/ 目錄不能是空的"
    for f in files:
        spec = load_spec_file(f)
        assert spec.warnings == [], f"{f.name} 有解析警告：\n" + "\n".join(spec.warnings)
        assert spec.registers, f"{f.name} 沒解析出任何暫存器"


def test_builtin_r5_shape():
    spec = load_spec_file(SPECS_DIR / "arm" / "cortex_r5.md")
    assert spec.cpu == "ARM Cortex-R5"
    assert spec.width == 32
    names = [r.name for r in spec.registers]
    assert names[0] == "MIDR" and "SCTLR" in names and "DRACR" in names
    midr = spec.registers[0]
    assert midr.offset == 0 and midr.reset == 0x411FC152
    impl = midr.fields[0]
    assert (impl.msb, impl.lsb, impl.name) == (31, 24, "Implementer")
    assert impl.enum[0x41] == "ARM Limited"
    # SCTLR 每個 bit 都被欄位涵蓋
    sctlr = next(r for r in spec.registers if r.name == "SCTLR")
    covered = set()
    for f in sctlr.fields:
        covered.update(range(f.lsb, f.msb + 1))
    assert covered == set(range(32))


# ── parse_int ───────────────────────────────────────────────────────────

def test_parse_int_formats():
    assert parse_int("0x1F") == 31
    assert parse_int("0b0100_0101") == 0x45
    assert parse_int("12") == 12
    assert parse_int("0x0008_0019") == 0x80019
    assert parse_int("-") is None
    assert parse_int("?") is None
    assert parse_int("abc") is None
    assert parse_int("") is None


# ── 寬容輸入 ────────────────────────────────────────────────────────────

def test_tolerant_markdown_noise():
    text = """\
# CPU: Demo
# Width: 32

說明文字，應被忽略。

## REG_A
- Offset: 0x0
- Reset: 0x3
- Description: 測試

| 位元 | 欄位 | 存取 | 重置 | 說明 |
|---|---|---|---|---|
| `1` | **EN** | RW | 1 | 致能 |
| 0 | MODE | RW | 1 | 模式 |
| 31:2 | RES0 | RO | 0 | 保留 |

### Enum: MODE
- 0: 模式甲
- 1: 模式乙
"""
    spec = parse_spec_text(text, "demo")
    assert spec.warnings == []
    reg = spec.registers[0]
    en = next(f for f in reg.fields if f.name == "EN")
    assert (en.msb, en.lsb, en.reset) == (1, 1, 1)
    mode = next(f for f in reg.fields if f.name == "MODE")
    assert mode.enum == {0: "模式甲", 1: "模式乙"}


def test_bits_reversed_and_brackets():
    text = """\
# CPU: Demo
## R
- Offset: 0x0

| Bits | Field |
|---|---|
| [3:0] | A |
| 4:7 | B |
"""
    spec = parse_spec_text(text, "demo")
    fields = {f.name: (f.msb, f.lsb) for f in spec.registers[0].fields}
    assert fields == {"A": (3, 0), "B": (7, 4)}


# ── 警告回報 ────────────────────────────────────────────────────────────

def test_warning_missing_offset_drops_register():
    text = """\
# CPU: Demo
## NO_OFFSET
- Description: 沒 offset

| Bits | Field |
|---|---|
| 0 | X |
"""
    spec = parse_spec_text(text, "demo")
    assert spec.registers == []
    assert any("Offset" in w for w in spec.warnings)


def test_warning_overlap_and_out_of_range():
    text = """\
# CPU: Demo
## R
- Offset: 0x0

| Bits | Field |
|---|---|
| 3:0 | A |
| 4:2 | B |
| 40:36 | C |
"""
    spec = parse_spec_text(text, "demo")
    assert any("重疊" in w for w in spec.warnings)
    assert any("超出" in w for w in spec.warnings)
    names = [f.name for f in spec.registers[0].fields]
    assert "C" not in names  # 超出寬度的整列丟棄
    assert {"A", "B"} <= set(names)  # 重疊只警告不丟棄


def test_warning_enum_unknown_field():
    text = """\
# CPU: Demo
## R
- Offset: 0x0

| Bits | Field |
|---|---|
| 0 | EN |

### Enum: NOPE
- 0: x
"""
    spec = parse_spec_text(text, "demo")
    assert any("NOPE" in w for w in spec.warnings)


def test_warning_duplicate_offset_and_span_overlap():
    text = """\
# CPU: Demo
## A
- Offset: 0x0
- Size: 64

| Bits | Field |
|---|---|
| 63:0 | V |

## B
- Offset: 0x4

| Bits | Field |
|---|---|
| 31:0 | V |
"""
    spec = parse_spec_text(text, "demo")
    assert any("重疊" in w for w in spec.warnings)


def test_missing_cpu_header_warns_and_falls_back():
    spec = parse_spec_text("## R\n- Offset: 0x0\n", "my_file")
    assert spec.cpu == "my_file"
    assert any("CPU" in w for w in spec.warnings)


# ── 目錄結構：廠商子資料夾、非 spec 檔略過（specs/README.md 的存在依據）──

def test_builtin_specs_have_vendor_from_subfolder():
    specs = {s.spec_id: s for s in load_builtin_specs(SPECS_DIR)}
    assert specs["cortex_r5"].vendor == "arm"
    assert specs["cortex_a55"].vendor == "arm"
    assert specs["n25"].vendor == "andes"
    assert specs["n45"].vendor == "andes"


def test_all_four_builtin_cpus_present_and_clean():
    """使用者指定的四顆 CPU 必須都在，且每顆都要有 Status 與可觀的暫存器數。"""
    specs = {s.spec_id: s for s in load_builtin_specs(SPECS_DIR)}
    assert set(specs) == {"cortex_r5", "cortex_a55", "n25", "n45"}
    for sid, spec in specs.items():
        assert spec.warnings == [], f"{sid}: {spec.warnings}"
        assert spec.status, f"{sid} 缺少 # Status:（查核狀態是給下一個維護者看的）"
        assert spec.source, f"{sid} 缺少 # Source:"
        assert len(spec.registers) >= 15, f"{sid} 暫存器太少：{len(spec.registers)}"
    assert specs["cortex_a55"].width == 64  # AArch64 一律 64-bit
    assert specs["cortex_r5"].width == 32


def test_is_spec_file_skips_readme_and_underscore(tmp_path):
    from pathlib import Path as _P
    assert is_spec_file(_P("specs/arm/cortex_r5.md"))
    assert not is_spec_file(_P("specs/README.md"))
    assert not is_spec_file(_P("specs/readme.md"))
    assert not is_spec_file(_P("specs/_draft.md"))
    assert not is_spec_file(_P("specs/notes.txt"))


def test_readme_in_specs_dir_is_not_loaded(tmp_path):
    (tmp_path / "arm").mkdir()
    (tmp_path / "arm" / "chip.md").write_text(
        "# CPU: X\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 0 | F |\n", encoding="utf-8")
    (tmp_path / "README.md").write_text("這不是 spec，只是說明文件", encoding="utf-8")
    (tmp_path / "arm" / "_draft.md").write_text("草稿", encoding="utf-8")
    specs = load_builtin_specs(tmp_path)
    assert [s.spec_id for s in specs] == ["chip"]
    assert specs[0].vendor == "arm"


def test_status_header_parsed_without_warning():
    spec = parse_spec_text(
        "# CPU: T\n# Status: 已核對 TRM r1p2\n## R\n- Offset: 0x0\n\n| Bits | Field |\n|---|---|\n| 0 | F |\n", "t")
    assert spec.status == "已核對 TRM r1p2"
    assert spec.warnings == []
