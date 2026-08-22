"""分析報告匯出（Markdown）。

輸入直接吃 analyzer.build_payload() 的 payload —— 值都已格式化成字串，
這裡只做排版，確保報告與畫面永遠一致（單一解碼來源）。
"""

from __future__ import annotations

from datetime import datetime

from .version import APP_NAME, APP_VERSION


def _esc_cell(s: str) -> str:
    """Markdown 表格 cell 內不能有裸的 |。"""
    return (s or "").replace("|", "\\|").replace("\n", " ")


def render_markdown(payload: dict, only_differs: bool = False) -> str:
    spec = payload["spec"]
    binf = payload.get("bin")
    stats = payload["stats"]

    lines: list[str] = []
    lines.append("# Register 分析報告")
    lines.append("")
    lines.append(f"- 產生工具：{APP_NAME} v{APP_VERSION}")
    lines.append(f"- 產生時間：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"- Spec：{spec['display_name']}" + (f"（{spec['source']}）" if spec.get("source") else ""))
    if binf:
        lines.append(f"- Bin 檔：{binf['name']}（{binf['size']:,} bytes）")
        lines.append(
            f"- 統計：共 {stats['total']} 個暫存器，"
            f"{stats['covered']} 個有值，{stats['differs']} 個與 Reset 不同"
        )
    else:
        lines.append("- Bin 檔：未載入（本報告為 spec 參考內容）")
    if only_differs:
        lines.append("- 篩選：只列出與 Reset 不同的暫存器")
    lines.append("")

    for reg in payload["registers"]:
        if only_differs and reg["differs"] is not True:
            continue
        title = f"## {reg['name']} — Offset {reg['offset_hex']}"
        if reg["value_hex"]:
            title += f" — 值 {reg['value_hex']}"
        lines.append(title)
        lines.append("")
        meta = []
        if reg.get("desc"):
            meta.append(reg["desc"])
        if reg.get("reset_hex"):
            meta.append(f"Reset：{reg['reset_hex']}")
        if reg["differs"] is True:
            meta.append("⚠ 與 Reset 不同")
        if not reg["covered"] and binf:
            meta.append("（bin 檔未涵蓋此暫存器）")
        if meta:
            lines.append("；".join(meta))
            lines.append("")

        lines.append("| Bits | 欄位 | 值 | 意義 | Reset |")
        lines.append("|---|---|---|---|---|")
        for row in reg["rows"]:
            val = row["value_hex"] or "—"
            if row["value_bin"] and row["msb"] - row["lsb"] + 1 <= 8:
                val = f"{row['value_bin']}（{row['value_hex']}）" if row["value_hex"] else "—"
            meaning = row["enum_label"] or row["desc"] or ""
            mark = " ⚠" if row["differs"] is True else ""
            lines.append(
                f"| {row['bits']} | {_esc_cell(row['name'])} | {_esc_cell(val)}{mark} "
                f"| {_esc_cell(meaning)} | {row['reset_hex'] or '—'} |"
            )
        lines.append("")

    return "\n".join(lines)
