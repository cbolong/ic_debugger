"""解碼引擎：Spec × BinFile → UI 渲染用 payload。

重要約定：payload 內所有「值」一律是**格式化好的字串**（hex/bin/dec），
不放原始整數 —— 64-bit 值超過 JavaScript Number 的安全範圍（2^53），
整數一過橋就會掉精度。所有位元運算都留在 Python 這一側，
前端 JS 只負責渲染，這也讓解碼邏輯能被 pytest 完整覆蓋。

沒載入 bin 時同樣能產生 payload（值全為 None）：此時 UI 就是一份
可搜尋的 spec 閱讀器 —— 「暫存器頁就是 spec 頁，載入 dump 後值疊上去」。
"""

from __future__ import annotations

from .bin_parser import BinFile, word_at
from .spec_loader import Field, Register, Spec, parse_int


# ── 數值格式化 ────────────────────────────────────────────────────────────

def fmt_hex(value: int, bits: int) -> str:
    """固定寬度大寫 hex；64-bit 以底線分成兩半方便讀（0x00000000_30D00980）。"""
    digits = max(1, (bits + 3) // 4)
    s = f"{value:0{digits}X}"
    if digits > 8:
        # 從右往左每 8 位插底線
        parts = []
        while s:
            parts.append(s[-8:])
            s = s[:-8]
        s = "_".join(reversed(parts))
    return "0x" + s


def fmt_bin(value: int, bits: int) -> str:
    """0b 前綴、由 LSB 起每 4 位以底線分組：0b0100_0101。"""
    s = f"{value:0{bits}b}"
    parts = []
    while s:
        parts.append(s[-4:])
        s = s[:-4]
    return "0b" + "_".join(reversed(parts))


def _fmt_enum_key(value: int, bits: int) -> str:
    """列舉表顯示用：窄欄位用二進位（0b10）、寬欄位用 hex。"""
    return fmt_bin(value, bits) if bits <= 4 else fmt_hex(value, bits)


def extract(value: int, msb: int, lsb: int) -> int:
    return (value >> lsb) & ((1 << (msb - lsb + 1)) - 1)


# ── 欄位列 ────────────────────────────────────────────────────────────────

def _uncovered_ranges(reg: Register) -> list[tuple[int, int]]:
    """spec 沒定義到的位元區段（(msb, lsb)，由高至低）。"""
    covered = [False] * reg.size
    for f in reg.fields:
        for b in range(f.lsb, min(f.msb, reg.size - 1) + 1):
            covered[b] = True
    ranges: list[tuple[int, int]] = []
    b = reg.size - 1
    while b >= 0:
        if not covered[b]:
            lo = b
            while lo - 1 >= 0 and not covered[lo - 1]:
                lo -= 1
            ranges.append((b, lo))
            b = lo - 1
        else:
            b -= 1
    return ranges


def _bits_label(msb: int, lsb: int) -> str:
    return str(msb) if msb == lsb else f"{msb}:{lsb}"


def _field_row(field: Field, reg_value: int | None, reg_reset: int | None) -> dict:
    w = field.width
    fval = extract(reg_value, field.msb, field.lsb) if reg_value is not None else None
    # 欄位 Reset：表格有寫就用表格的，否則從暫存器 Reset 推導
    freset = field.reset
    if freset is None and reg_reset is not None:
        freset = extract(reg_reset, field.msb, field.lsb)
    differs = (fval != freset) if (fval is not None and freset is not None) else None

    enum_label = field.enum.get(fval) if fval is not None else None
    enum_rows = [
        {"v": _fmt_enum_key(v, w), "label": label, "current": (fval is not None and v == fval)}
        for v, label in sorted(field.enum.items())
    ]
    return {
        "kind": "field",
        "bits": _bits_label(field.msb, field.lsb),
        "msb": field.msb, "lsb": field.lsb,
        "name": field.name,
        "access": field.access,
        "desc": field.desc,
        "reserved": field.reserved,
        "value_hex": fmt_hex(fval, w) if fval is not None else None,
        "value_bin": fmt_bin(fval, w) if fval is not None else None,
        "value_dec": str(fval) if fval is not None else None,
        "reset_hex": fmt_hex(freset, w) if freset is not None else None,
        "differs": differs,
        "enum_label": enum_label,
        "enum": enum_rows,
    }


def _undef_row(msb: int, lsb: int, reg_value: int | None) -> dict:
    w = msb - lsb + 1
    fval = extract(reg_value, msb, lsb) if reg_value is not None else None
    return {
        "kind": "undef",
        "bits": _bits_label(msb, lsb),
        "msb": msb, "lsb": lsb,
        "name": "（未定義）",
        "access": "",
        "desc": "spec 未定義此位元範圍",
        "reserved": True,
        "value_hex": fmt_hex(fval, w) if fval is not None else None,
        "value_bin": fmt_bin(fval, w) if fval is not None else None,
        "value_dec": str(fval) if fval is not None else None,
        "reset_hex": None,
        "differs": None,
        "enum_label": None,
        "enum": [],
        "nonzero": bool(fval),
    }


# ── 暫存器 ────────────────────────────────────────────────────────────────

def _register_dict(reg: Register, data: bytes | None) -> dict:
    value = word_at(data, reg.offset, reg.size) if data is not None else None
    covered = value is not None
    # bin 存在但長度不足以涵蓋整個暫存器 → 標成「截斷」讓使用者知道對不齊
    partial = (
        data is not None and value is None
        and reg.offset < len(data) < reg.offset + reg.size // 8
    )

    rows = [_field_row(f, value, reg.reset) for f in reg.fields]
    undef_rows = [_undef_row(msb, lsb, value) for msb, lsb in _uncovered_ranges(reg)]
    rows.extend(undef_rows)
    rows.sort(key=lambda r: r["msb"], reverse=True)

    reg_differs: bool | None = None
    if value is not None:
        if reg.reset is not None:
            reg_differs = value != reg.reset
        else:
            field_diffs = [r["differs"] for r in rows if r["differs"] is not None]
            reg_differs = any(field_diffs) if field_diffs else None

    return {
        "name": reg.name,
        "offset": reg.offset,
        "offset_hex": f"0x{reg.offset:03X}",
        "size": reg.size,
        "desc": reg.desc,
        "verified": reg.verified,
        "covered": covered,
        "partial": partial,
        "value_hex": fmt_hex(value, reg.size) if value is not None else None,
        "value_bits": f"{value:0{reg.size}b}" if value is not None else None,
        "reset_hex": fmt_hex(reg.reset, reg.size) if reg.reset is not None else None,
        "differs": reg_differs,
        "nonzero_undef": any(r.get("nonzero") for r in undef_rows),
        "rows": rows,
    }


# ── Hex dump ─────────────────────────────────────────────────────────────

def _hexdump(spec: Spec, binf: BinFile) -> dict:
    """以 32-bit word 為單位呈現整個 bin，並標註每個 word 屬於哪個暫存器，
    讓使用者一眼檢查「dump 跟 spec 有沒有對齊」。"""
    word_owner: dict[int, str] = {}
    for reg in spec.registers:
        if reg.size == 64:
            word_owner[reg.offset] = f"{reg.name} [31:0]"
            word_owner[reg.offset + 4] = f"{reg.name} [63:32]"
        else:
            word_owner[reg.offset] = reg.name

    data = binf.data
    rows = []
    for base in range(0, len(data), 16):
        words = []
        for off in range(base, min(base + 16, len(data)), 4):
            chunk = data[off:off + 4]
            if len(chunk) == 4:
                words.append({
                    "offset_hex": f"0x{off:03X}",
                    "hex": fmt_hex(int.from_bytes(chunk, "little"), 32),
                    "reg": word_owner.get(off),
                })
            else:  # 檔尾不足一個 word：以原始 bytes 呈現
                words.append({
                    "offset_hex": f"0x{off:03X}",
                    "hex": " ".join(f"{b:02X}" for b in chunk),
                    "reg": None,
                    "partial": True,
                })
        rows.append({"offset_hex": f"0x{base:04X}", "words": words})

    note = None
    span = spec.span_bytes
    if len(data) > span:
        note = f"bin 檔比 spec 涵蓋範圍多出 {len(data) - span} bytes（spec 只定義到 0x{span:X}），多出的部分未對應任何暫存器"
    elif len(data) < span:
        note = f"bin 檔比 spec 涵蓋範圍短 {span - len(data)} bytes（spec 定義到 0x{span:X}），檔尾之後的暫存器顯示為「未涵蓋」"
    return {"rows": rows, "note": note}


# ── Payload ──────────────────────────────────────────────────────────────

def spec_summary(spec: Spec) -> dict:
    """下拉選單 / Spec 管理頁用的精簡資訊。"""
    return {
        "id": spec.spec_id,
        "cpu": spec.cpu,
        "version": spec.version,
        "display_name": spec.display_name,
        "width": spec.width,
        "source": spec.source,
        "status": spec.status,
        "vendor": spec.vendor,
        "desc": spec.desc,
        "origin": spec.origin,
        "path": spec.path,
        "register_count": len(spec.registers),
        "verified_count": sum(1 for r in spec.registers if r.verified),
        "warnings": list(spec.warnings),
    }


def lookup_register(spec: Spec, query: str, value_text: str) -> dict:
    """快速反查：使用者只有「一組 offset（或暫存器名稱）＋一個值」時的單筆解碼。

    解碼結果與 bin 模式**完全同源**（設計如此）：把值放進一個假想 buffer 的
    對應位移，走同一個 _register_dict() —— 兩條路徑永遠不會各解各的。

    回傳 {"ok": True, "register": <同 build_payload 的暫存器 dict>, "note": …}
    或 {"ok": False, "error": 中文錯誤訊息（含建議）}。
    """
    q = (query or "").strip()
    if not q:
        return {"ok": False, "error": "請輸入暫存器名稱或 Offset"}
    regs = sorted(spec.registers, key=lambda r: r.offset)
    if not regs:
        return {"ok": False, "error": "目前的 spec 沒有任何暫存器"}

    # 名稱優先（大小寫不拘）——工程師手上常只有名字，offset 是 dump 腳本的產物
    reg = next((r for r in regs if r.name.lower() == q.lower()), None)
    note = None
    if reg is None:
        off = parse_int(q)
        if off is None or off < 0:
            cands = [r.name for r in regs if q.lower() in r.name.lower()][:8]
            hint = f"；名稱相近：{'、'.join(cands)}" if cands else ""
            return {"ok": False, "error": f"找不到暫存器「{q}」{hint}"}
        reg = next((r for r in regs if r.offset == off), None)
        if reg is None:
            # 落在某暫存器範圍中間（例如 64-bit 的高半段）→ 以整個暫存器解碼並註記
            inside = next((r for r in regs if r.offset < off < r.offset + r.size // 8), None)
            if inside is None:
                return {"ok": False, "error":
                        f"spec 沒有定義 Offset 0x{off:X}（此 spec 涵蓋 0x000–0x{spec.span_bytes - 1:03X}）"}
            reg = inside
            note = (f"Offset 0x{off:X} 位於 {reg.name}（Offset 0x{reg.offset:X}、"
                    f"{reg.size}-bit）的範圍內，以整個暫存器解碼")

    value = parse_int(value_text)
    if value is None:
        return {"ok": False, "error": f"值「{(value_text or '').strip()}」解析失敗（可用 0x…、0b…、十進位）"}
    if value < 0:
        return {"ok": False, "error": "值不可為負數"}
    if value >= (1 << reg.size):
        return {"ok": False, "error":
                f"值 0x{value:X} 超過 {reg.name} 的寬度（{reg.size}-bit，最大 {fmt_hex((1 << reg.size) - 1, reg.size)}）"}

    data = bytes(reg.offset) + value.to_bytes(reg.size // 8, "little")
    return {"ok": True, "register": _register_dict(reg, data), "note": note}


def spec_detail(spec: Spec, binf: BinFile | None = None) -> dict:
    """「Spec 全文」檢視用：完整解析結果＋原始 Markdown 原文。

    目的：讓使用者稽核「軟體實際依據的 spec」對不對 —— 解析後內容是引擎
    真正使用的資料，原文則供與 TRM 逐字比對。原文從 spec.path 重新讀
    （內建＝exe 解壓目錄、外部＝使用者的檔案）；讀不到時 raw=None 並附原因，
    解析內容照樣可看。

    傳入 binf 時，解析後內容同頁疊上目前值（成為連續版的完整對照）；
    呼叫端只該對「目前使用中的 spec」傳 binf —— bin 的 offset 對應是跟著
    spec 定義走的，套到別份 spec 上值沒有意義（AppState.detail_binf 把關）。
    """
    payload = build_payload(spec, binf)
    raw: str | None = None
    raw_error: str | None = None
    if spec.path:
        try:
            from pathlib import Path
            raw = Path(spec.path).read_text(encoding="utf-8-sig")
        except OSError as e:
            raw_error = f"無法讀取原始檔：{e}"
    else:
        raw_error = "此 spec 不是從檔案載入，沒有原始檔可顯示"
    return {
        "summary": payload["spec"],
        "registers": payload["registers"],
        "raw": raw,
        "raw_error": raw_error,
    }


def build_payload(spec: Spec, binf: BinFile | None) -> dict:
    regs = sorted(spec.registers, key=lambda r: r.offset)
    data = binf.data if binf is not None else None
    reg_dicts = [_register_dict(r, data) for r in regs]

    covered = sum(1 for r in reg_dicts if r["covered"])
    differs = sum(1 for r in reg_dicts if r["differs"] is True)
    stats = {
        "total": len(reg_dicts),
        "covered": covered,
        "not_covered": len(reg_dicts) - covered,
        "differs": differs,
        "spec_span_bytes": spec.span_bytes,
        "bin_size": binf.size if binf is not None else None,
    }
    return {
        "spec": spec_summary(spec),
        "bin": {"name": binf.name, "path": binf.path, "size": binf.size} if binf else None,
        "registers": reg_dicts,
        "hexdump": _hexdump(spec, binf) if binf is not None else None,
        "stats": stats,
    }
