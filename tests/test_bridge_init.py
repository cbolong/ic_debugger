"""pywebview bridge 初始化的競態驗證。

2026-08-24 現場事故：畫面永遠停在「找不到任何 CPU spec」，沒有錯誤、
沒有診斷。原因是 pywebview 先注入 `window.pywebview = {api: {}}`，
之後才用 _createApi() 把方法掛上去；前端只檢查 `pywebview.api` 存在就
初始化，剛好落在空窗期取到 undefined 的 get_init，promise 被拒之後
S.inited 已 latch，後來的 pywebviewready 也不會重試。

以下兩層驗證：
- 靜態：就緒判斷必須確認「方法真的是 function」（CI 一定會跑）。
- 動態：用 Chromium 真的重演兩段式注入，確認 UI 最後有拿到資料
  （需要 playwright，缺席就跳過）。
"""

import json
import re

import pytest

from ui.assets import build_main_html

CHROMIUM = "/opt/pw-browsers/chromium"


# ── 靜態：就緒判斷不准退回「只檢查 api 物件存在」──────────────────────

def test_bridge_ready_checks_actual_method():
    html = build_main_html("")
    assert "function bridgeReady()" in html, "缺少 bridgeReady()"
    m = re.search(r"function bridgeReady\(\)\{(.*?)\n\}", html, re.S)
    body = m.group(1)
    assert "typeof" in body and "get_init" in body and "'function'" in body, (
        "bridgeReady() 必須確認 pywebview.api.get_init 真的是 function —— "
        "只檢查 api 物件存在會落在 pywebview 的注入空窗期（現場事故成因）"
    )


def test_init_does_not_latch_before_bridge_ready():
    """init() 必須在 bridgeReady() 不成立時直接 return，且不可先設 S.inited。"""
    html = build_main_html("")
    m = re.search(r"\nfunction init\(\)\{(.*?)\n\}\n", html, re.S)
    body = m.group(1)
    guard = body.index("if (!bridgeReady()) return;")
    latch = body.index("S.inited = true;", guard)
    assert guard < latch, "bridgeReady() 檢查必須在 latch S.inited 之前"


def test_poll_has_timeout_and_reports_failure():
    """輪詢不能無限空等：逾時要把原因寫進 lastError 讓畫面說出來。"""
    html = build_main_html("")
    assert "_initTries" in html and "S.lastError" in html


def test_handle_keeps_diag_on_failure():
    """失敗回應也要留住 diag —— 否則出事時連診斷都看不到（現場事故的第二層）。"""
    html = build_main_html("")
    m = re.search(r"function handle\(resp, after\)\{(.*?)\n\}", html, re.S)
    body = m.group(1)
    diag_at = body.index("S.diag = resp.diag")
    fail_at = body.index("if (!resp.ok)")
    assert diag_at < fail_at, "diag 的指派必須在 !resp.ok 的提早 return 之前"


# ── 動態：真的重演 pywebview 的兩段式注入 ──────────────────────────────

def _fake_bridge_js(delay_ms: int) -> str:
    """模擬 pywebview：先給空的 api 物件，delay 之後才掛上方法並發事件。"""
    resp = {
        "ok": True,
        "specs": [{"id": "cortex_r5", "cpu": "ARM Cortex-R5", "version": "r1p2",
                   "display_name": "ARM Cortex-R5 (r1p2)", "width": 32, "source": "",
                   "status": "", "vendor": "arm", "desc": "", "origin": "builtin",
                   "path": "", "register_count": 1, "warnings": []}],
        "payload": {
            "spec": {"id": "cortex_r5", "display_name": "ARM Cortex-R5 (r1p2)",
                     "vendor": "arm", "source": "", "status": "", "desc": "",
                     "origin": "builtin", "path": "", "register_count": 1,
                     "warnings": [], "cpu": "ARM Cortex-R5", "version": "r1p2", "width": 32},
            "bin": None, "hexdump": None,
            "registers": [{"name": "MIDR", "offset": 0, "offset_hex": "0x000", "size": 32,
                           "desc": "", "covered": False, "partial": False,
                           "value_hex": None, "value_bits": None, "reset_hex": "0x411FC152",
                           "differs": None, "nonzero_undef": False,
                           "rows": [{"kind": "field", "bits": "31:0", "msb": 31, "lsb": 0,
                                     "name": "V", "access": "RO", "desc": "", "reserved": False,
                                     "value_hex": None, "value_bin": None, "value_dec": None,
                                     "reset_hex": None, "differs": None,
                                     "enum_label": None, "enum": []}]}],
            "stats": {"total": 1, "covered": 0, "not_covered": 1, "differs": 0,
                      "spec_span_bytes": 4, "bin_size": None},
        },
        "diag": {"version": "1.0.0", "frozen": True, "spec_count": 1,
                 "scan": [{"dir": "X:\\\\specs", "exists": True, "loaded": 1, "names": ["cortex_r5"]}],
                 "log_path": "X:\\\\log"},
    }
    return f"""
window.pywebview = {{ api: {{}} }};          // pywebview 第一段：只有空的 api
setTimeout(function(){{
  window.pywebview.api.get_init = function(){{
    return Promise.resolve({json.dumps(resp, ensure_ascii=False)});
  }};
  window.dispatchEvent(new Event('pywebviewready'));   // 第二段：方法掛好才發事件
}}, {delay_ms});
"""


@pytest.mark.parametrize("delay_ms", [0, 400, 1200])
def test_ui_loads_despite_two_phase_bridge_injection(tmp_path, delay_ms):
    """空窗期不論多長，UI 最後都必須拿到資料（這正是現場壞掉的情境）。"""
    playwright = pytest.importorskip("playwright.sync_api")
    import os

    html = build_main_html("").replace(
        "</head>", f"<script>{_fake_bridge_js(delay_ms)}</script></head>")
    page_file = tmp_path / f"bridge_{delay_ms}.html"
    page_file.write_text(html, encoding="utf-8")

    with playwright.sync_playwright() as p:
        # 先吃固定路徑（Claude 工作容器），沒有再退回 playwright 自管的
        # 瀏覽器（CI 的 `python -m playwright install chromium` 裝在這）。
        # 寫死單一路徑曾讓這 3 條在 Windows CI 靜默 skip（R4 審查抓到
        # CI 179/3 與本機 182/0 不一致的成因）。
        exe = CHROMIUM if os.path.exists(CHROMIUM) else p.chromium.executable_path
        if not exe or not os.path.exists(exe):
            pytest.skip("找不到 chromium（固定路徑與 playwright 自管瀏覽器皆缺）")
        browser = p.chromium.launch(executable_path=exe)
        page = browser.new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.goto(page_file.as_uri())
        # 下拉選單出現 spec ＝ get_init 的資料真的送達並套用
        # （state="attached"：收合的 select 裡的 option 不算「可見」）
        page.wait_for_selector("#specSelect option", state="attached", timeout=8000)
        text = page.inner_text("#specSelect")
        count = page.eval_on_selector_all("#specSelect option", "els => els.length")
        browser.close()

    assert not errors, f"JS 錯誤：{errors}"
    assert count == 1 and "Cortex-R5" in text, f"UI 沒拿到 spec（delay={delay_ms}ms）"
