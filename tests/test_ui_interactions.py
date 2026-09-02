"""真實瀏覽器的互動驗證（Chromium；找不到瀏覽器就 skip——CI 一定跑）。

靜態檢查（test_ui.py）驗得了語法與交叉引用，驗不了「產生出來的 onclick
參數有沒有加引號」這種點下去才爆的錯：快速反查頁的 bit ruler 就曾因
registerBlock 共用時傳入字串 ri='lk'，產生 focusField(lk,0)（少引號＝
未定義識別字），整組點擊沉默失效（2026-09-02 全面 review 抓到並修正）。
"""

import os
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHROMIUM = "/opt/pw-browsers/chromium"


def _launch(p):
    """先吃固定路徑（工作容器），沒有再退回 playwright 自管的瀏覽器
    （CI 以 `python -m playwright install chromium` 安裝）。"""
    exe = CHROMIUM if os.path.exists(CHROMIUM) else p.chromium.executable_path
    if not exe or not os.path.exists(exe):
        pytest.skip("找不到 chromium（固定路徑與 playwright 自管瀏覽器皆缺）")
    return p.chromium.launch(executable_path=exe)


@pytest.fixture(scope="module")
def preview_uri(tmp_path_factory):
    sys.path.insert(0, str(ROOT))
    from tools.preview import build_preview_html
    f = tmp_path_factory.mktemp("ui") / "preview.html"
    f.write_text(build_preview_html(), encoding="utf-8")
    return f.as_uri()


def _open(playwright_mod, uri):
    p = playwright_mod.sync_playwright().start()
    browser = _launch(p)
    page = browser.new_page()
    errors: list[str] = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(uri)
    page.wait_for_selector(".cards")
    return p, browser, page, errors


def test_bit_ruler_click_focuses_field_on_both_pages(preview_uri):
    """bit ruler 點擊在「暫存器」（ri=數字）與「快速反查」（ri='lk' 字串）
    都必須捲動＋閃爍對應欄位列，且全程零 JS 錯誤。"""
    playwright = pytest.importorskip("playwright.sync_api")
    p, browser, page, errors = _open(playwright, preview_uri)
    try:
        # 暫存器頁：展開 SCTLR、點 bit ruler 第一個欄位
        page.click('[data-view="regs"]')
        page.click("#reg-SCTLR")
        page.wait_for_selector(".bitruler .bitgroup")
        page.click(".bitruler .bitgroup")
        page.wait_for_selector(".field-table .frow.flash", timeout=3000)

        # 快速反查頁：示範結果的 bit ruler（字串 ri——曾整組沉默失效的路徑）
        page.click('[data-view="lookup"]')
        page.wait_for_selector(".lk-detail .bitgroup")
        page.click(".lk-detail .bitgroup")
        page.wait_for_selector(".lk-detail .frow.flash", timeout=3000)
    finally:
        browser.close()
        p.stop()
    assert not errors, f"JS 錯誤：{errors}"


def test_search_filters_after_debounce(preview_uri):
    """搜尋輸入走 120ms 合併重繪：打完字（含等待）後過濾結果必須生效，
    且目標暫存器可見 —— 端到端鎖住 debounce 沒把過濾弄壞。"""
    playwright = pytest.importorskip("playwright.sync_api")
    p, browser, page, errors = _open(playwright, preview_uri)
    try:
        page.click('[data-view="regs"]')
        total = page.eval_on_selector_all("tr.reg-row", "els => els.length")
        page.fill("#searchInput", "TCMTR")
        page.wait_for_timeout(400)  # > 120ms debounce
        filtered = page.eval_on_selector_all("tr.reg-row", "els => els.length")
        assert filtered < total, f"搜尋沒有過濾（{filtered}/{total}）"
        assert page.query_selector("#reg-TCMTR") is not None, "目標暫存器不在結果中"
    finally:
        browser.close()
        p.stop()
    assert not errors, f"JS 錯誤：{errors}"


def test_clamped_prose_expands_on_click(preview_uri):
    """長文夾行（clamp3）點擊必須展開、再點收合——資訊不刪除、預設收斂。"""
    playwright = pytest.importorskip("playwright.sync_api")
    p, browser, page, errors = _open(playwright, preview_uri)
    try:
        page.click('[data-view="specs"]')
        # Spec 卡的查核狀態：.clamp3 在帶 padding 的 .spec-status 內層
        page.wait_for_selector(".spec-status .clamp3")
        inner = page.query_selector(".spec-status .clamp3")
        clamped_h = inner.bounding_box()["height"]
        inner.click()  # 事件冒泡到外盒的 toggleClamp(this)
        page.wait_for_timeout(100)
        expanded_h = inner.bounding_box()["height"]
        assert expanded_h > clamped_h, "點擊後沒有展開"
        inner.click()
        page.wait_for_timeout(100)
        assert abs(inner.bounding_box()["height"] - clamped_h) < 2, "再點沒有收合"
    finally:
        browser.close()
        p.stop()
    assert not errors, f"JS 錯誤：{errors}"
