"""UI 預覽工具：不開 pywebview，直接把 MAIN_HTML 灌入範例資料在 Chromium 渲染。

用途：
1. 開發時快速看畫面（產出 preview.html 可直接用瀏覽器開）。
2. 有裝 playwright 時自動截圖各視圖（淺／深色），並把 console 錯誤當失敗回報
   —— 等於一個輕量的 UI 整合測試。

用法：
    PYTHONPATH=. python tools/preview.py [--out 目錄] [--html-only]
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from core.analyzer import build_payload, lookup_register, spec_detail, spec_summary  # noqa: E402
from core.bin_parser import load_bin  # noqa: E402
from core.spec_loader import load_builtin_specs  # noqa: E402
from core.version import APP_VERSION  # noqa: E402
from ui.assets import build_main_html  # noqa: E402


def build_preview_html(theme_attr: str = "") -> str:
    specs = load_builtin_specs(ROOT / "specs")
    r5 = next(s for s in specs if s.spec_id == "arm_cortex_r5")
    binf = load_bin(ROOT / "examples" / "sample_r5.bin")
    init = {
        "specs": [spec_summary(s) for s in specs],
        "payload": build_payload(r5, binf),
        "spec_detail": spec_detail(r5, binf),
        "lookup_demo": lookup_register(r5, "SCTLR", "0x00C7187D"),
        "version": APP_VERSION,
    }
    blob = json.dumps(init, ensure_ascii=False).replace("</", "<\\/")
    html = build_main_html(theme_attr=theme_attr)
    return html.replace("</head>", f"<script>window.__PREVIEW__ = {blob};</script></head>")


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "preview_out"))
    ap.add_argument("--html-only", action="store_true", help="只產 HTML 不截圖")
    args = ap.parse_args()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    html_path = out / "preview.html"
    html_path.write_text(build_preview_html(), encoding="utf-8")
    print(f"寫出 {html_path}")
    if args.html_only:
        return 0

    import os

    from playwright.sync_api import sync_playwright

    # playwright 版本與快取的瀏覽器版本可能不合；有預裝的 chromium 就直接指定
    exe = os.environ.get("PREVIEW_CHROMIUM")
    if not exe and Path("/opt/pw-browsers/chromium").exists():
        exe = "/opt/pw-browsers/chromium"

    errors: list[str] = []
    with sync_playwright() as p:
        browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
        page = browser.new_page(viewport={"width": 1440, "height": 900})
        page.on("pageerror", lambda e: errors.append(f"pageerror: {e}"))
        # 資源載入失敗（例如離線時 Google Fonts 載不到）是預期的降級路徑，不算失敗
        page.on("console", lambda m: errors.append(f"console.{m.type}: {m.text}")
                if m.type == "error" and "Failed to load resource" not in m.text else None)
        page.goto(html_path.as_uri())
        page.wait_for_selector(".cards", timeout=8000)

        def shot(name: str):
            page.screenshot(path=str(out / name))
            print(f"  截圖 {name}")

        shot("1_overview_light.png")

        # 暫存器頁：展開 SCTLR 看 bit ruler + 欄位表
        page.click('[data-view="regs"]')
        page.click("#reg-SCTLR")
        page.wait_for_selector(".bitruler")
        shot("2_registers_light.png")

        page.click('[data-view="hex"]')
        page.wait_for_selector(".hex-table")
        shot("3_hexdump_light.png")

        page.click('[data-view="specs"]')
        page.wait_for_selector(".spec-card")
        shot("4_specs_light.png")

        # 快速反查（預覽模式塞入 SCTLR 示範結果）
        page.click('[data-view="lookup"]')
        page.wait_for_selector(".lk-form")
        shot("10_lookup_light.png")

        # Spec 全文：解析後與原始 Markdown 兩個分頁
        page.click('[data-view="specdoc"]')
        page.wait_for_selector(".doc-reg-head")
        shot("8_specdoc_parsed_light.png")
        page.click("text=原始 Markdown")
        page.wait_for_selector(".rawspec")
        shot("9_specdoc_raw_light.png")

        # 深色：按 🌓
        page.click(".theme-toggle")
        page.wait_for_timeout(150)
        shot("5_specs_dark.png")
        page.click('[data-view="overview"]')
        page.wait_for_timeout(100)
        shot("6_overview_dark.png")
        page.click('[data-view="regs"]')
        page.wait_for_timeout(100)
        shot("7_registers_dark.png")

        browser.close()

    if errors:
        print("JS 錯誤：", file=sys.stderr)
        for e in errors:
            print("  " + e, file=sys.stderr)
        return 1
    print("完成，無 JS 錯誤")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
