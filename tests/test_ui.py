"""UI 資產的靜態檢查。

沿 ic-monitor 的教訓：JS 是以 Python 字串夾帶的，Python 可能吃掉跳脫字元或
佔位符沒替換乾淨，這類錯誤瀏覽器只會默默死掉 —— 所以在測試裡把「Python 實際
輸出的 JS」抓出來給 node --check 驗語法。
"""

import re
import shutil
import subprocess

import pytest

from ui.assets import THEME_ROOT_CSS, build_main_html


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
