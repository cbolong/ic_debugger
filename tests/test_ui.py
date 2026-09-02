"""UI 資產的靜態檢查。

沿 ic-monitor 的教訓：JS 是以 Python 字串夾帶的，Python 可能吃掉跳脫字元或
佔位符沒替換乾淨，這類錯誤瀏覽器只會默默死掉 —— 所以在測試裡把「Python 實際
輸出的 JS」抓出來給 node --check 驗語法。
"""

import re
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

from ui.assets import THEME_ROOT_CSS, build_main_html

ROOT = Path(__file__).resolve().parent.parent


def test_no_leftover_placeholders():
    html = build_main_html('data-theme="dark"')
    assert "__THEME_ROOT_CSS__" not in html
    assert "__html_theme_attr__" not in html
    assert "__APP_VERSION__" not in html
    assert "__DARK_TOKENS__" not in html
    assert 'data-theme="dark"' in html


def test_light_theme_attr_empty():
    html = build_main_html("")
    assert "__html_theme_attr__" not in html
    assert html.count("<html") == 1


def test_theme_tokens_complete():
    # 深色區塊必須「只重定義淺色已有的 tokens」——多出來的 token 表示淺色缺定義
    light = set(re.findall(r"--c-[a-z-]+(?=\s*:)", THEME_ROOT_CSS.split("@media")[0]))
    dark_blocks = THEME_ROOT_CSS.split("@media", 1)[1]
    dark = set(re.findall(r"--c-[a-z-]+(?=\s*:)", dark_blocks))
    assert dark <= light, f"深色定義了淺色沒有的 token：{dark - light}"


def _scripts(html: str) -> list[str]:
    return re.findall(r"<script>(.*?)</script>", html, re.S)


def test_scripts_extracted():
    html = build_main_html("")
    scripts = _scripts(html)
    assert len(scripts) == 2  # head（主題/錯誤緩衝）＋ body（app 本體）
    assert "renderAll" in scripts[1]


@pytest.mark.skipif(shutil.which("node") is None, reason="需要 node 驗 JS 語法")
def test_js_syntax_with_node(tmp_path):
    html = build_main_html("")
    for i, script in enumerate(_scripts(html)):
        f = tmp_path / f"script_{i}.js"
        f.write_text(script, encoding="utf-8")
        r = subprocess.run(
            ["node", "--check", str(f)], capture_output=True, text=True,
            encoding="utf-8", errors="replace",
        )
        assert r.returncode == 0, f"script #{i} JS 語法錯誤：\n{r.stderr}"


# ════════════════════════════════════════════════════════════════════
# 交叉引用窮舉：改名／刪函式把按鈕改壞，在這裡就會被抓，不用等點下去才死
# ════════════════════════════════════════════════════════════════════

def _declared_functions(html: str) -> set:
    out = set()
    for script in _scripts(html):
        out.update(re.findall(r"\bfunction\s+([A-Za-z_]\w*)\s*\(", script))
        out.update(re.findall(r"window\.(_\w+)\s*=\s*function", script))
    return out


def test_every_inline_handler_has_declared_function():
    """HTML／模板字串裡每個 onclick／oninput／onchange 呼叫的函式都必須存在。"""
    html = build_main_html("")
    handlers = set(re.findall(r"on(?:click|input|change)=\\?\"([A-Za-z_]\w*)\s*\(", html))
    declared = _declared_functions(html)
    missing = handlers - declared
    assert handlers, "應該要找得到 inline handler（找不到代表這個測試的 regex 壞了）"
    assert not missing, f"這些 handler 沒有對應的函式定義：{missing}"


def test_every_getelementbyid_target_exists():
    """JS 引用的靜態元素 id 必須存在於 HTML（動態產生的 id 逐一列管）。"""
    html = build_main_html("")
    used = set(re.findall(r"getElementById\('([\w-]+)'\)", html))
    static_ids = set(re.findall(r'id="([\w-]+)"', html))
    # 這些 id 是 JS 動態 render 出來的，驗它們的產生程式碼存在
    dynamic = {"searchInput"}
    for d in dynamic & used:
        assert f'id="{d}"' in html or f"id='{d}'" in html or (d + '"') in html, d
    missing = used - static_ids - dynamic - {p for p in used if p.startswith(("reg-", "ft-"))}
    assert not missing, f"JS 引用了不存在的靜態 id：{missing}"


def test_all_views_have_render_branch_and_nav_entry():
    html = build_main_html("")
    views_in_nav = set(re.findall(r'data-view="(\w+)"', html))
    assert views_in_nav == {"overview", "regs", "lookup", "hex", "specdoc", "specs"}
    body = _scripts(html)[1]
    for v in views_in_nav:
        assert f"'{v}'" in body, f"renderView 缺少 {v} 的分支或入口"


def test_every_used_css_token_is_defined_in_light_root():
    """CSS/JS 用到的每個 var(--c-*) 都必須在淺色 :root 有定義：
    打錯 token 名不會有任何錯誤訊息，顏色只會靜默消失 —— 用這條測試抓。"""
    html = build_main_html("")
    used = set(re.findall(r"var\(\s*(--c-[a-z-]+)", html))
    light_root = THEME_ROOT_CSS.split("@media")[0]
    defined = set(re.findall(r"(--c-[a-z-]+)\s*:", light_root))
    missing = used - defined
    assert used, "抓不到任何 var(--c-*)，測試 regex 壞了"
    assert not missing, f"這些 token 有使用但淺色沒定義：{missing}"


def test_api_methods_called_from_js_exist_in_python():
    """JS 透過 api('name', …) 呼叫的每個方法都必須存在於 ui/apis.py 的 Api。
    （反向不強制：Python 多提供方法無妨。）"""
    import ast
    from pathlib import Path

    html = build_main_html("")
    called = set(re.findall(r"api\('(\w+)'", html))
    called |= set(re.findall(r"pywebview\.api\.(\w+)\s*\(", html))
    src = (Path(__file__).resolve().parent.parent / "ui" / "apis.py").read_text(encoding="utf-8")
    tree = ast.parse(src)
    api_cls = next(n for n in ast.walk(tree) if isinstance(n, ast.ClassDef) and n.name == "Api")
    methods = {n.name for n in api_cls.body if isinstance(n, ast.FunctionDef)}
    missing = called - methods
    assert called, "抓不到任何 api() 呼叫，測試 regex 壞了"
    assert not missing, f"JS 呼叫了 Api 沒有的方法：{missing}"


def test_no_external_resources():
    """UI 不得載入任何外部資源。

    設計如此：IC 設計環境常是封閉網路，對 CDN／字型伺服器的 DNS 與連線
    逾時會讓啟動多等好幾秒（現場回報「開啟速度有點慢」的主因之一）。
    """
    html = build_main_html("")
    external = re.findall(r'(?:href|src)="(https?://[^"]+)"', html)
    assert not external, f"UI 引用了外部資源：{external}"


def test_verify_state_rendered_from_single_source():
    """「有沒有對照過官方文件」只准有一支渲染程式。

    設計如此：spec 卡片、Spec 全文標頭、暫存器展開、Spec 全文逐顆——四個
    地方顯示同一種資訊，若各寫各的，改一處就會與其他處說法不一致
    （CLAUDE.md 不變條件 12）。
    """
    body = _scripts(build_main_html(""))[1]
    assert body.count("function verifyChipHtml(") == 1
    assert body.count("function verifyRegChipHtml(") == 1
    # spec 層級（Spec 管理卡片＋Spec 全文標頭）
    assert body.count("+= verifyChipHtml(s)") == 2
    # 暫存器層級（registerBlock＋Spec 全文逐顆）
    assert body.count("+= verifyRegChipHtml(r,") == 2


def test_unverified_register_says_so_on_audit_page():
    """稽核頁面（Spec 全文）對「沒對照過原廠文件」必須明講，不准沉默。

    現場事故（2026-08-24）：R5 官方 TRM 有 TCMTR，本工具的 spec 沒有，
    而畫面上沒有任何線索顯示這份 spec 未經原廠文件核對。
    """
    body = _scripts(build_main_html(""))[1]
    assert "位元定義對照自：" in body
    assert "未對照官方文件" in body
    assert "位元定義尚未對照官方 0/" in body


def test_long_prose_is_clamped_with_expand_toggle():
    """長文降噪（設計如此：資訊不刪除、預設收斂）——收合列說明夾 2 行、
    審查歷程累積的 Source／查核狀態夾 3 行且點擊可展開。四個 clamp 位置：
    總覽 Source、Spec 卡查核狀態、Spec 全文查核狀態＋來源。"""
    html = build_main_html("")
    assert "tr.reg-row:not(.open) .reg-desc" in html
    assert ".clamp3" in html and "-webkit-line-clamp: 3" in html
    assert ".clamp3.expanded" in html
    body = _scripts(html)[1]
    assert "function toggleClamp(" in body
    assert body.count('onclick="toggleClamp(this)"') == 4


def test_preview_tool_accepts_relative_out_dir(tmp_path):
    """tools/preview.py 的 --out 給相對路徑曾在截圖階段炸 as_uri()
    （relative path can't be expressed as a file URI）——鎖住 resolve() 行為：
    輸出檔要落在 cwd 底下、印出的路徑必須是絕對路徑。"""
    r = subprocess.run(
        [sys.executable, str(ROOT / "tools" / "preview.py"),
         "--out", "rel_out", "--html-only"],
        cwd=tmp_path, capture_output=True, text=True, encoding="utf-8",
    )
    assert r.returncode == 0, r.stderr
    assert (tmp_path / "rel_out" / "preview.html").exists()
    line = next(l for l in r.stdout.splitlines() if "preview.html" in l)
    assert Path(line.split("寫出 ", 1)[1]).is_absolute()


def test_reset_chip_says_when_verdict_is_partial():
    """「Reset —」旁邊不可以出現沒有但書的「= Reset」。

    設計如此：暫存器層級沒有 Reset 時，比對只用得到有寫 Reset 的欄位，
    chip 必須加註「（部分欄位）」，且三個掛 chip 的地方共用同一支。
    """
    body = _scripts(build_main_html(""))[1]
    assert body.count("function resetQualifier(") == 1
    assert body.count("resetQualifier(r)") == 5  # 宣告 1 ＋ 使用 4
    assert "（部分欄位）" in body
