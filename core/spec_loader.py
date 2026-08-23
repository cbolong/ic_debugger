"""Spec MD 檔解析器。

把 `specs/*.md`（格式見 SPEC_FORMAT.md）解析成資料模型：

    Spec ── registers: [Register] ── fields: [Field] ── enum: {值: 意義}

設計原則（spec 之後會由 AI 依範例產生，品質不保證完美）：
- **寬容輸入**：欄位別名（中英文表頭）、0x/0b/十進位/底線分隔都收；
  cell 內的 `code`、**bold** 標記自動剝除；認不得的行直接略過。
- **嚴格回報**：所有不對勁（缺 Offset、位元重疊、超出寬度、解析失敗的列）
  都收進 Spec.warnings，帶行號，由 UI 的「Spec 管理」頁完整呈現，
  讓使用者一眼看出 AI 產的 spec 哪裡要修 —— 絕不默默吞掉。
- 解析失敗的元件盡量降級保留（例如壞掉的欄位列丟棄但暫存器保留），
  不讓一行錯誤毀掉整份 spec。
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field as dc_field
from pathlib import Path

# ── 欄位表表頭別名（一律先 lower / 去空白再比對）──────────────────────────
_COL_ALIASES = {
    "bits": {"bits", "bit", "位元", "位元範圍", "bit範圍"},
    "name": {"field", "name", "欄位", "欄位名稱", "名稱"},
    "access": {"access", "type", "存取", "屬性", "r/w", "rw"},
    "reset": {"reset", "resetvalue", "重置", "重置值", "預設", "預設值", "default"},
    "desc": {"description", "desc", "說明", "描述", "meaning", "意義"},
}

# 保留位元的慣用命名：這些欄位在 UI 中會淡化顯示
_RESERVED_RE = re.compile(r"^(RES[01]|RESERVED|RAZ(/WI)?|SBZ(P)?|SBO(P)?|UNK|保留|—|-)$", re.I)

_BITS_RE = re.compile(r"^\[?\s*(\d+)\s*(?:[:~\-]\s*(\d+))?\s*\]?$")


@dataclass
class Field:
    msb: int
    lsb: int
    name: str
    access: str = ""
    reset: int | None = None
    desc: str = ""
    enum: dict[int, str] = dc_field(default_factory=dict)

    @property
    def width(self) -> int:
        return self.msb - self.lsb + 1

    @property
    def reserved(self) -> bool:
        return bool(_RESERVED_RE.match(self.name.strip()))


@dataclass
class Register:
    name: str
    offset: int
    size: int
    reset: int | None = None
    desc: str = ""
    fields: list[Field] = dc_field(default_factory=list)
    line: int = 0  # 來源行號（警告訊息用）


@dataclass
class Spec:
    spec_id: str
    cpu: str
    version: str = ""
    width: int = 32
    source: str = ""
    status: str = ""      # 查核狀態（# Status:），UI 直接顯示，提醒哪些欄位還沒對過原廠文件
    desc: str = ""
    vendor: str = ""      # 廠商＝specs/ 下的子目錄名（arm、andes…），UI 用來分組
    registers: list[Register] = dc_field(default_factory=list)
    warnings: list[str] = dc_field(default_factory=list)
    origin: str = "builtin"  # builtin（打包進 exe）| external（執行時載入）
    path: str = ""

    @property
    def display_name(self) -> str:
        return f"{self.cpu} ({self.version})" if self.version else self.cpu

    @property
    def span_bytes(self) -> int:
        """spec 涵蓋的 bin 範圍：最後一個 register 的結尾位移。"""
        if not self.registers:
            return 0
        return max(r.offset + r.size // 8 for r in self.registers)


def parse_int(text: str) -> int | None:
    """解析 0x… / 0b… / 十進位（允許底線分隔）。'-'、'?'、空白、認不得 → None。"""
    s = (text or "").strip().replace("_", "").replace(",", "")
    if not s or s in {"-", "?", "—", "N/A", "n/a", "TBD", "tbd"}:
        return None
    try:
        if s.lower().startswith("0x"):
            return int(s, 16)
        if s.lower().startswith("0b"):
            return int(s, 2)
        return int(s, 10)
    except ValueError:
        return None


def _clean_cell(s: str) -> str:
    """剝除 markdown 行內標記（`code` / **bold** / *italic*）與首尾空白。"""
    s = s.strip()
    s = re.sub(r"`([^`]*)`", r"\1", s)
    s = re.sub(r"\*\*([^*]*)\*\*", r"\1", s)
    s = re.sub(r"(?<!\w)\*([^*]+)\*(?!\w)", r"\1", s)
    return s.strip()


def _split_row(line: str) -> list[str]:
    """把 '| a | b |' 切成 cell list（容忍缺首尾 pipe）。"""
    s = line.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [_clean_cell(c) for c in s.split("|")]


def _is_separator_row(cells: list[str]) -> bool:
    return all(re.fullmatch(r"[:\-\s]*", c) for c in cells)


def _parse_bits(cell: str) -> tuple[int, int] | None:
    m = _BITS_RE.match(cell.strip())
    if not m:
        return None
    msb = int(m.group(1))
    lsb = int(m.group(2)) if m.group(2) is not None else msb
    if msb < lsb:  # 寫反了就幫忙轉正
        msb, lsb = lsb, msb
    return msb, lsb


def parse_spec_text(text: str, spec_id: str, path: str = "", origin: str = "builtin") -> Spec:
    """解析一份 spec MD 內容。永遠回傳 Spec；問題全部進 warnings。"""
    spec = Spec(spec_id=spec_id, cpu="", origin=origin, path=path)
    warn = spec.warnings.append
    loc = Path(path).name if path else spec_id

    reg: Register | None = None
    table_cols: dict[str, int] | None = None  # 欄位名 -> cell index
    enum_field: str | None = None  # 目前 '### Enum:' 綁定的欄位名
    saw_any_register = False

    lines = text.splitlines()
    for ln, raw in enumerate(lines, 1):
        line = raw.rstrip()
        stripped = line.strip()
        if not stripped or stripped.startswith("<!--"):
            continue

        # ── '### Enum: FIELD' 列舉區塊 ──────────────────────────────
        m = re.match(r"^###\s+(?:Enum|Values|列舉|數值)\s*[:：]\s*(.+)$", stripped, re.I)
        if m:
            table_cols = None
            if reg is None:
                warn(f"{loc}:{ln}: Enum 區塊出現在任何暫存器之前，已略過")
                enum_field = None
                continue
            enum_field = _clean_cell(m.group(1))
            if not any(f.name == enum_field for f in reg.fields):
                warn(f"{loc}:{ln}: Enum 對應的欄位「{enum_field}」不存在於 {reg.name} 的欄位表（Enum 區塊必須放在欄位表之後）")
                enum_field = None
            continue

        # ── '## 暫存器名稱' ────────────────────────────────────────
        m = re.match(r"^##\s+(?!#)(.+)$", stripped)
        if m and not stripped.startswith("###"):
            saw_any_register = True
            table_cols, enum_field = None, None
            name = _clean_cell(m.group(1))
            reg = Register(name=name, offset=-1, size=spec.width, line=ln)
            spec.registers.append(reg)
            continue

        # ── '# Key: value' 檔頭（只認第一個暫存器出現之前的）────────
        m = re.match(r"^#\s+([A-Za-z]+)\s*[:：]\s*(.*)$", stripped)
        if m and not saw_any_register:
            key, val = m.group(1).strip().lower(), _clean_cell(m.group(2))
            if key == "cpu":
                spec.cpu = val
            elif key == "version":
                spec.version = val
            elif key == "width":
                w = parse_int(val)
                if w in (8, 16, 32, 64):
                    spec.width = w
                else:
                    warn(f"{loc}:{ln}: Width「{val}」無效（只接受 8/16/32/64），改用預設 32")
            elif key == "source":
                spec.source = val
            elif key == "status":
                spec.status = val
            elif key == "description":
                spec.desc = val
            else:
                warn(f"{loc}:{ln}: 不認得的檔頭欄位「{key}」，已略過")
            continue

        # ── 列舉項目 '- 值: 意義' ──────────────────────────────────
        if enum_field is not None and reg is not None:
            m = re.match(r"^[-*]\s+([^:：]+)[:：]\s*(.+)$", stripped)
            if m and m.group(1).strip().lower() in {"offset", "size", "reset", "description"}:
                m = None  # 這是暫存器屬性不是列舉值 → 結束 enum 區塊往下處理
            if m:
                v = parse_int(_clean_cell(m.group(1)))
                if v is None:
                    warn(f"{loc}:{ln}: Enum 值「{m.group(1).strip()}」解析失敗，已略過")
                else:
                    for f in reg.fields:
                        if f.name == enum_field:
                            if v >= (1 << f.width):
                                warn(f"{loc}:{ln}: Enum 值 {m.group(1).strip()} 超出欄位 {enum_field}（{f.width} bit）的範圍")
                            f.enum[v] = _clean_cell(m.group(2))
                continue
            # 非列舉項目的行 → 結束 enum 區塊，繼續往下判斷
            enum_field = None

        # ── 暫存器屬性 '- Key: value' ──────────────────────────────
        m = re.match(r"^[-*]\s+([A-Za-z]+)\s*[:：]\s*(.*)$", stripped)
        if m and reg is not None:
            key, val = m.group(1).strip().lower(), _clean_cell(m.group(2))
            if key == "offset":
                v = parse_int(val)
                if v is None or v < 0:
                    warn(f"{loc}:{reg.line}: {reg.name} 的 Offset「{val}」解析失敗")
                else:
                    reg.offset = v
            elif key == "size":
                v = parse_int(val)
                if v in (8, 16, 32, 64):
                    reg.size = v
                else:
                    warn(f"{loc}:{ln}: {reg.name} 的 Size「{val}」無效（只接受 8/16/32/64），改用 {reg.size}")
            elif key == "reset":
                v = parse_int(val)
                if v is None and val not in {"", "-", "?", "—"}:
                    warn(f"{loc}:{ln}: {reg.name} 的 Reset「{val}」解析失敗，視為未知")
                reg.reset = v
            elif key == "description":
                reg.desc = val
            else:
                warn(f"{loc}:{ln}: {reg.name} 有不認得的屬性「{key}」，已略過")
            continue

        # ── 欄位表 ─────────────────────────────────────────────────
        if stripped.startswith("|") or stripped.count("|") >= 2:
            cells = _split_row(stripped)
            if _is_separator_row(cells):
                continue
            lowered = [re.sub(r"\s+", "", c).lower() for c in cells]
            if table_cols is None or any(v in _COL_ALIASES["bits"] for v in lowered):
                # 表頭列：建立欄位對照
                cols: dict[str, int] = {}
                for idx, cell in enumerate(lowered):
                    for col, aliases in _COL_ALIASES.items():
                        if cell in aliases and col not in cols:
                            cols[col] = idx
                if "bits" in cols and "name" in cols:
                    table_cols = cols
                elif reg is not None:
                    warn(f"{loc}:{ln}: 表格表頭缺少 Bits / Field 欄，整張表已略過")
                    table_cols = None
                continue
            if reg is None:
                continue
            # 資料列
            def cell(col: str) -> str:
                i = table_cols.get(col, -1)
                return cells[i] if 0 <= i < len(cells) else ""

            bits = _parse_bits(cell("bits"))
            if bits is None:
                warn(f"{loc}:{ln}: {reg.name} 欄位表的 Bits「{cell('bits')}」解析失敗，該列已略過")
                continue
            msb, lsb = bits
            if msb >= reg.size:
                warn(f"{loc}:{ln}: {reg.name} 欄位 {cell('name') or '?'} 的位元 [{msb}:{lsb}] 超出暫存器寬度 {reg.size}，該列已略過")
                continue
            fname = cell("name") or f"[{msb}:{lsb}]"
            freset_txt = cell("reset")
            freset = parse_int(freset_txt)
            if freset is not None and freset >= (1 << (msb - lsb + 1)):
                warn(f"{loc}:{ln}: {reg.name}.{fname} 的 Reset「{freset_txt}」超出 {msb - lsb + 1} bit 範圍，視為未知")
                freset = None
            reg.fields.append(Field(
                msb=msb, lsb=lsb, name=fname,
                access=cell("access"), reset=freset, desc=cell("desc"),
            ))
            continue

        # 其他行（說明文字等）一律容許並略過

    _finalize(spec, loc)
    return spec


def _finalize(spec: Spec, loc: str) -> None:
    """收尾驗證：丟棄無效暫存器、檢查重疊/重複，一律以 warning 呈現。"""
    warn = spec.warnings.append

    if not spec.cpu:
        spec.cpu = spec.spec_id
        warn(f"{loc}: 檔頭缺少「# CPU:」，以檔名代替顯示名稱")

    valid: list[Register] = []
    seen_offsets: dict[int, str] = {}
    for reg in spec.registers:
        if reg.offset < 0:
            warn(f"{loc}:{reg.line}: {reg.name} 缺少有效的 Offset，整個暫存器已略過")
            continue
        if reg.offset % 4 != 0:
            warn(f"{loc}:{reg.line}: {reg.name} 的 Offset 0x{reg.offset:X} 不是 4 的倍數（bin 以 32-bit word 對齊讀取，請確認）")
        if reg.offset in seen_offsets:
            warn(f"{loc}:{reg.line}: {reg.name} 的 Offset 0x{reg.offset:X} 與 {seen_offsets[reg.offset]} 重複")
        else:
            seen_offsets[reg.offset] = reg.name

        # 位元重疊檢查
        occupied: dict[int, str] = {}
        for f in reg.fields:
            for b in range(f.lsb, f.msb + 1):
                if b in occupied:
                    warn(f"{loc}: {reg.name} 的欄位 {f.name} 與 {occupied[b]} 在 bit {b} 重疊")
                    break
                occupied[b] = f.name

        if reg.reset is not None and reg.size < 64 and reg.reset >= (1 << reg.size):
            warn(f"{loc}: {reg.name} 的 Reset 0x{reg.reset:X} 超出 {reg.size} bit，已截斷")
            reg.reset &= (1 << reg.size) - 1

        reg.fields.sort(key=lambda f: f.msb, reverse=True)
        valid.append(reg)

    # 檢查暫存器之間的位移範圍重疊（例如 64-bit 暫存器吃到下一個的位置）
    valid.sort(key=lambda r: r.offset)
    for a, b in zip(valid, valid[1:]):
        if a.offset + a.size // 8 > b.offset:
            warn(f"{loc}: {a.name}（0x{a.offset:X}，{a.size} bit）與 {b.name}（0x{b.offset:X}）的位移範圍重疊")

    spec.registers = valid
    if not valid:
        warn(f"{loc}: 這份 spec 沒有任何有效的暫存器")


def load_spec_file(path: str | Path, origin: str = "builtin", vendor: str = "") -> Spec:
    """從檔案載入 spec。讀檔失敗回傳只帶 warning 的空 Spec（UI 可呈現）。"""
    p = Path(path)
    spec_id = p.stem
    try:
        text = p.read_text(encoding="utf-8-sig")  # 容忍 Windows 編輯器的 BOM
    except OSError as e:
        s = Spec(spec_id=spec_id, cpu=spec_id, origin=origin, path=str(p), vendor=vendor)
        s.warnings.append(f"{p.name}: 讀取失敗：{e}")
        return s
    spec = parse_spec_text(text, spec_id=spec_id, path=str(p), origin=origin)
    spec.vendor = vendor
    return spec


def is_spec_file(path: Path) -> bool:
    """specs/ 底下哪些 .md 算 spec：排除 README 與底線開頭的檔名，
    讓維護者能在 spec 旁邊放說明/草稿而不會被當成壞掉的 spec 解析。"""
    return (path.suffix.lower() == ".md"
            and path.stem.upper() != "README"
            and not path.name.startswith("_"))


def load_builtin_specs(specs_dir: str | Path) -> list[Spec]:
    """遞迴載入內建 spec 目錄下所有 .md。

    目錄結構＝`specs/<廠商>/<型號>.md`（例：specs/arm/cortex_r5.md）；
    子目錄名就是廠商（UI 依此分組），放在 specs/ 根目錄的檔案廠商為空字串。
    依 (廠商, 檔名) 排序，確保 UI 的清單順序永遠穩定。
    """
    d = Path(specs_dir)
    if not d.is_dir():
        return []
    files = sorted((p for p in d.rglob("*.md") if is_spec_file(p)),
                   key=lambda p: (p.parent.relative_to(d).as_posix(), p.stem))
    out = []
    for p in files:
        rel_parent = p.parent.relative_to(d).as_posix()
        vendor = "" if rel_parent == "." else rel_parent.split("/")[0]
        out.append(load_spec_file(p, origin="builtin", vendor=vendor))
    return out
